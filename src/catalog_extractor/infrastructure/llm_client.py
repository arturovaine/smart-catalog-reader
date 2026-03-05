"""LLM client implementation for Gemini API."""

import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

import google.generativeai as genai
import structlog
from google.api_core import exceptions
from PIL import Image
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from catalog_extractor.domain.interfaces import LLMClient
from catalog_extractor.domain.models import (
    ExtractionResult,
    PageImage,
    Product,
    PromotionalRule,
    PromotionType,
)

logger = structlog.get_logger()

# Default extraction prompt optimized for cosmetics catalogs
DEFAULT_EXTRACTION_PROMPT = """
Analise esta página de catálogo de cosméticos e extraia TODOS os produtos em formato JSON.

REGRAS DE EXTRAÇÃO:
1. Retorne um objeto JSON válido com a estrutura exata abaixo (sem markdown, sem ```json)
2. Campos numéricos (preços) devem ser float (ex: 55.90, não "R$ 55,90")
3. O código do produto geralmente tem 5 dígitos
4. Identifique a "linha" (ex: Cuide-se Bem, Botik, Nativa SPA) pelo contexto visual
5. Identifique a "categoria" (ex: Hidratação, Perfumaria, Maquiagem, Cabelos, Corpo e Banho)

PROMOÇÕES COMPLEXAS:
- Desconto Progressivo: Detalhe os níveis (ex: "1 un = 20% off, 2+ = 30% off")
- Combo/Kit: Liste os códigos incluídos
- Leve X Pague Y: Especifique a regra
- Pack: Indique quantidade e preço unitário implícito

ESTRUTURA JSON ESPERADA:
{
    "tipo_pagina": "produtos" | "publicidade" | "indice",
    "itens": [
        {
            "codigo": "85675",
            "nome": "Nome Completo do Produto",
            "linha": "Cuide-se Bem",
            "categoria": "Hidratação",
            "volume_peso": "200ml",
            "preco_regular": 69.90,
            "preco_promocional": 55.90,
            "promocao_ativa": true,
            "regra_promocional": {
                "tipo": "simple_discount" | "progressive_discount" | "combo" | "buy_x_pay_y" | "pack" | "none",
                "descricao": "Descrição da regra",
                "discount_tiers": {"1_unit": 0.20, "2_plus": 0.30},
                "combo_codes": ["85675", "85676"]
            },
            "caracteristicas": ["Vegano", "48h de hidratação"],
            "quadrante": "top-left" | "top-right" | "bottom-left" | "bottom-right" | "center"
        }
    ],
    "regras_globais": [
        {
            "tipo": "progressive_discount",
            "descricao": "Desconto progressivo Botik",
            "paginas_relacionadas": [8, 9, 10]
        }
    ]
}

Se a página for apenas publicidade/marketing sem produtos com código, retorne:
{"tipo_pagina": "publicidade", "itens": [], "regras_globais": []}
"""


class GeminiClient(LLMClient):
    """Gemini API client for product extraction."""

    def __init__(
        self,
        api_key: str,
        model_name: str = "gemini-2.5-flash",
        max_workers: int = 2,
        max_retries: int = 10,
    ) -> None:
        """Initialize Gemini client.

        Args:
            api_key: Gemini API key
            model_name: Model to use for extraction
            max_workers: Maximum parallel workers for batch processing
            max_retries: Maximum retry attempts for API calls
        """
        genai.configure(api_key=api_key)
        self._model = genai.GenerativeModel(model_name)
        self._max_workers = max_workers
        self._max_retries = max_retries
        self._logger = logger.bind(component="GeminiClient", model=model_name)

    @retry(
        retry=retry_if_exception_type(
            (exceptions.ResourceExhausted, exceptions.ServiceUnavailable)
        ),
        wait=wait_exponential(multiplier=1, min=2, max=60),
        stop=stop_after_attempt(10),
        reraise=True,
    )
    def _call_api(self, image: Image.Image, prompt: str) -> str:
        """Make API call with automatic retry on rate limiting.

        Args:
            image: PIL Image to analyze
            prompt: Extraction prompt

        Returns:
            Raw response text from API
        """
        response = self._model.generate_content([prompt, image])
        return response.text

    def _parse_response(self, raw_response: str, page_number: int) -> ExtractionResult:
        """Parse raw JSON response into structured data.

        Args:
            raw_response: Raw JSON string from API
            page_number: Page number for context

        Returns:
            ExtractionResult with parsed products
        """
        # Clean markdown formatting if present
        cleaned = raw_response.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as e:
            self._logger.error(
                "Failed to parse JSON response",
                page=page_number,
                error=str(e),
                raw_response=raw_response[:500],
            )
            return ExtractionResult(
                page_number=page_number,
                success=False,
                error_message=f"JSON parse error: {e}",
                raw_response=raw_response,
            )

        # Check if page is just advertising
        page_type = data.get("tipo_pagina", "produtos")
        if page_type in ("publicidade", "indice"):
            return ExtractionResult(
                page_number=page_number,
                success=True,
                products=[],
                raw_response=raw_response,
            )

        # Parse products
        products: list[Product] = []
        for item in data.get("itens", []):
            try:
                product = self._parse_product(item, page_number)
                products.append(product)
            except Exception as e:
                self._logger.warning(
                    "Failed to parse product",
                    page=page_number,
                    item=item,
                    error=str(e),
                )

        # Parse global promotional rules
        promo_rules: list[PromotionalRule] = []
        for rule in data.get("regras_globais", []):
            try:
                promo_rule = self._parse_promotional_rule(rule)
                promo_rules.append(promo_rule)
            except Exception as e:
                self._logger.warning(
                    "Failed to parse promotional rule",
                    page=page_number,
                    rule=rule,
                    error=str(e),
                )

        return ExtractionResult(
            page_number=page_number,
            success=True,
            products=products,
            promotional_rules=promo_rules,
            raw_response=raw_response,
        )

    def _parse_product(self, item: dict[str, Any], page_number: int) -> Product:
        """Parse a single product from extracted data."""
        # Parse promotional rule if present
        regra_promo = None
        if rule_data := item.get("regra_promocional"):
            regra_promo = self._parse_promotional_rule(rule_data)

        return Product(
            codigo=str(item.get("codigo", "")),
            nome=item.get("nome", ""),
            linha=item.get("linha"),
            categoria=item.get("categoria"),
            volume_peso=item.get("volume_peso"),
            quantidade=item.get("quantidade"),
            preco_regular=item.get("preco_regular", 0.0),
            preco_promocional=item.get("preco_promocional"),
            promocao_ativa=item.get("promocao_ativa", False),
            regra_promocional=regra_promo,
            caracteristicas=item.get("caracteristicas", []),
            pagina=page_number,
            quadrante=item.get("quadrante"),
        )

    def _parse_promotional_rule(self, rule: dict[str, Any]) -> PromotionalRule:
        """Parse promotional rule data."""
        tipo_str = rule.get("tipo", "none").lower().replace(" ", "_")

        # Map string to enum
        tipo_map = {
            "none": PromotionType.NONE,
            "simple_discount": PromotionType.SIMPLE_DISCOUNT,
            "progressive_discount": PromotionType.PROGRESSIVE_DISCOUNT,
            "combo": PromotionType.COMBO,
            "buy_x_pay_y": PromotionType.BUY_X_PAY_Y,
            "pack": PromotionType.PACK,
        }
        tipo = tipo_map.get(tipo_str, PromotionType.NONE)

        return PromotionalRule(
            type=tipo,
            description=rule.get("descricao"),
            discount_tiers=rule.get("discount_tiers") or {},
            combo_codes=rule.get("combo_codes") or [],
            related_pages=rule.get("paginas_relacionadas") or [],
        )

    def extract_products(
        self,
        image: Image.Image,
        page_number: int,
        prompt: str | None = None,
    ) -> ExtractionResult:
        """Extract products from a single page.

        Args:
            image: PIL Image of the catalog page
            page_number: Page number for context
            prompt: Optional custom prompt (uses default if not provided)

        Returns:
            ExtractionResult with extracted products
        """
        start_time = time.time()
        prompt = prompt or DEFAULT_EXTRACTION_PROMPT

        self._logger.info("Extracting products", page=page_number)

        try:
            raw_response = self._call_api(image, prompt)
            result = self._parse_response(raw_response, page_number)
            result.processing_time_ms = (time.time() - start_time) * 1000

            self._logger.info(
                "Extraction complete",
                page=page_number,
                products_found=len(result.products),
                success=result.success,
                time_ms=result.processing_time_ms,
            )

            return result

        except Exception as e:
            self._logger.error(
                "Extraction failed",
                page=page_number,
                error=str(e),
            )
            return ExtractionResult(
                page_number=page_number,
                success=False,
                error_message=str(e),
                processing_time_ms=(time.time() - start_time) * 1000,
            )

    def extract_batch(
        self,
        pages: list[PageImage],
        prompt: str | None = None,
    ) -> list[ExtractionResult]:
        """Extract products from multiple pages in parallel.

        Args:
            pages: List of PageImage objects
            prompt: Optional custom prompt

        Returns:
            List of ExtractionResult objects (in page order)
        """
        prompt = prompt or DEFAULT_EXTRACTION_PROMPT
        results: dict[int, ExtractionResult] = {}

        self._logger.info(
            "Starting batch extraction",
            total_pages=len(pages),
            max_workers=self._max_workers,
        )

        with ThreadPoolExecutor(max_workers=self._max_workers) as executor:
            # Submit all tasks
            future_to_page = {
                executor.submit(
                    self.extract_products,
                    page.image,
                    page.page_number,
                    prompt,
                ): page.page_number
                for page in pages
            }

            # Collect results as they complete
            for future in as_completed(future_to_page):
                page_num = future_to_page[future]
                try:
                    result = future.result()
                    results[page_num] = result
                except Exception as e:
                    self._logger.error(
                        "Batch extraction failed for page",
                        page=page_num,
                        error=str(e),
                    )
                    results[page_num] = ExtractionResult(
                        page_number=page_num,
                        success=False,
                        error_message=str(e),
                    )

        # Return results sorted by page number
        return [results[p.page_number] for p in sorted(pages, key=lambda x: x.page_number)]
