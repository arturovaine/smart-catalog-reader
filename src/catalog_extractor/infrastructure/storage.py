"""Storage repository implementation for JSON persistence."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import structlog

from catalog_extractor.domain.interfaces import StorageRepository
from catalog_extractor.domain.models import Catalog, Product, PromotionalRule, ValidationAlert

logger = structlog.get_logger()


class JSONStorageRepository(StorageRepository):
    """Storage repository using JSON files."""

    def __init__(self, output_dir: Path | None = None) -> None:
        """Initialize storage repository.

        Args:
            output_dir: Default output directory for saved files
        """
        self._output_dir = output_dir or Path("data/output")
        self._output_dir.mkdir(parents=True, exist_ok=True)
        self._checkpoints_dir = self._output_dir / ".checkpoints"
        self._checkpoints_dir.mkdir(exist_ok=True)
        self._logger = logger.bind(component="JSONStorageRepository")

    def _serialize_catalog(self, catalog: Catalog) -> dict[str, Any]:
        """Serialize catalog to JSON-compatible dict."""
        return {
            "metadata": {
                "nome": catalog.nome,
                "marca": catalog.marca,
                "ciclo": catalog.ciclo,
                "vigencia_inicio": (
                    catalog.vigencia_inicio.isoformat() if catalog.vigencia_inicio else None
                ),
                "vigencia_fim": (
                    catalog.vigencia_fim.isoformat() if catalog.vigencia_fim else None
                ),
                "total_paginas": catalog.total_paginas,
                "source_file": str(catalog.source_file),
                "paginas_processadas": catalog.paginas_processadas,
                "paginas_com_erro": catalog.paginas_com_erro,
                "exported_at": datetime.now().isoformat(),
            },
            "regras_promocionais_globais": [
                self._serialize_promo_rule(r) for r in catalog.regras_promocionais_globais
            ],
            "produtos": [self._serialize_product(p) for p in catalog.produtos],
            "estatisticas": {
                "total_produtos": len(catalog.produtos),
                "produtos_com_promocao": sum(1 for p in catalog.produtos if p.promocao_ativa),
                "categorias": list(set(p.categoria_normalizada or "Outros" for p in catalog.produtos)),
                "linhas": list(set(p.linha for p in catalog.produtos if p.linha)),
            },
        }

    def _serialize_product(self, product: Product) -> dict[str, Any]:
        """Serialize a product to dict."""
        return {
            "codigo": product.codigo,
            "nome": product.nome,
            "linha": product.linha,
            "categoria": product.categoria,
            "categoria_normalizada": product.categoria_normalizada,
            "volume_peso": product.volume_peso,
            "quantidade": product.quantidade,
            "preco_regular": product.preco_regular,
            "preco_promocional": product.preco_promocional,
            "economia": product.economia,
            "desconto_percentual": product.desconto_percentual,
            "promocao_ativa": product.promocao_ativa,
            "regra_promocional": (
                self._serialize_promo_rule(product.regra_promocional)
                if product.regra_promocional
                else None
            ),
            "caracteristicas": product.caracteristicas,
            "pagina": product.pagina,
            "quadrante": product.quadrante,
            "alertas": [self._serialize_alert(a) for a in product.alertas],
        }

    def _serialize_promo_rule(self, rule: PromotionalRule) -> dict[str, Any]:
        """Serialize promotional rule to dict."""
        return {
            "tipo": rule.type.value,
            "descricao": rule.description,
            "conditions": rule.conditions,
            "discount_tiers": rule.discount_tiers,
            "combo_codes": rule.combo_codes,
            "paginas_relacionadas": rule.related_pages,
        }

    def _serialize_alert(self, alert: ValidationAlert) -> dict[str, Any]:
        """Serialize validation alert to dict."""
        return {
            "level": alert.level.value,
            "field": alert.field,
            "message": alert.message,
            "original_value": alert.original_value,
            "corrected_value": alert.corrected_value,
        }

    def save_catalog(self, catalog: Catalog, output_path: Path | None = None) -> Path:
        """Save extracted catalog data to JSON.

        Args:
            catalog: Catalog object to save
            output_path: Optional custom output path

        Returns:
            Path where data was saved
        """
        if output_path is None:
            # Generate filename from catalog info
            safe_name = catalog.nome.replace(" ", "_").replace("/", "-").lower()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self._output_dir / f"{safe_name}_{timestamp}.json"

        data = self._serialize_catalog(catalog)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        self._logger.info(
            "Catalog saved",
            path=str(output_path),
            products=len(catalog.produtos),
        )

        return output_path

    def load_catalog(self, path: Path) -> Catalog:
        """Load a previously saved catalog."""
        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        metadata = data.get("metadata", {})

        # Reconstruct products
        products = []
        for p_data in data.get("produtos", []):
            product = Product(
                codigo=p_data["codigo"],
                nome=p_data["nome"],
                linha=p_data.get("linha"),
                categoria=p_data.get("categoria"),
                categoria_normalizada=p_data.get("categoria_normalizada"),
                volume_peso=p_data.get("volume_peso"),
                quantidade=p_data.get("quantidade"),
                preco_regular=p_data["preco_regular"],
                preco_promocional=p_data.get("preco_promocional"),
                economia=p_data.get("economia"),
                promocao_ativa=p_data.get("promocao_ativa", False),
                caracteristicas=p_data.get("caracteristicas", []),
                pagina=p_data["pagina"],
                quadrante=p_data.get("quadrante"),
            )
            products.append(product)

        return Catalog(
            nome=metadata.get("nome", "Unknown"),
            marca=metadata.get("marca", "Unknown"),
            ciclo=metadata.get("ciclo"),
            total_paginas=metadata.get("total_paginas", 0),
            source_file=Path(metadata.get("source_file", "")),
            produtos=products,
            paginas_processadas=metadata.get("paginas_processadas", 0),
            paginas_com_erro=metadata.get("paginas_com_erro", []),
        )

    def save_checkpoint(self, catalog: Catalog, last_processed_page: int) -> Path:
        """Save extraction checkpoint for resuming.

        Args:
            catalog: Partial catalog data
            last_processed_page: Last successfully processed page

        Returns:
            Path to checkpoint file
        """
        safe_name = catalog.nome.replace(" ", "_").replace("/", "-").lower()
        checkpoint_path = self._checkpoints_dir / f"{safe_name}.checkpoint.json"

        data = {
            "catalog": self._serialize_catalog(catalog),
            "last_processed_page": last_processed_page,
            "checkpoint_time": datetime.now().isoformat(),
        }

        with open(checkpoint_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        self._logger.info(
            "Checkpoint saved",
            catalog=catalog.nome,
            last_page=last_processed_page,
        )

        return checkpoint_path

    def load_checkpoint(self, catalog_name: str) -> tuple[Catalog, int] | None:
        """Load checkpoint if exists.

        Args:
            catalog_name: Name of the catalog

        Returns:
            Tuple of (partial catalog, last processed page) or None
        """
        safe_name = catalog_name.replace(" ", "_").replace("/", "-").lower()
        checkpoint_path = self._checkpoints_dir / f"{safe_name}.checkpoint.json"

        if not checkpoint_path.exists():
            return None

        try:
            with open(checkpoint_path, encoding="utf-8") as f:
                data = json.load(f)

            # Reconstruct catalog from checkpoint
            catalog_data = data.get("catalog", {})
            metadata = catalog_data.get("metadata", {})

            products = []
            for p_data in catalog_data.get("produtos", []):
                product = Product(
                    codigo=p_data["codigo"],
                    nome=p_data["nome"],
                    linha=p_data.get("linha"),
                    categoria=p_data.get("categoria"),
                    categoria_normalizada=p_data.get("categoria_normalizada"),
                    volume_peso=p_data.get("volume_peso"),
                    quantidade=p_data.get("quantidade"),
                    preco_regular=p_data["preco_regular"],
                    preco_promocional=p_data.get("preco_promocional"),
                    economia=p_data.get("economia"),
                    promocao_ativa=p_data.get("promocao_ativa", False),
                    caracteristicas=p_data.get("caracteristicas", []),
                    pagina=p_data["pagina"],
                    quadrante=p_data.get("quadrante"),
                )
                products.append(product)

            catalog = Catalog(
                nome=metadata.get("nome", catalog_name),
                marca=metadata.get("marca", "Unknown"),
                ciclo=metadata.get("ciclo"),
                total_paginas=metadata.get("total_paginas", 0),
                source_file=Path(metadata.get("source_file", "")),
                produtos=products,
                paginas_processadas=metadata.get("paginas_processadas", 0),
                paginas_com_erro=metadata.get("paginas_com_erro", []),
            )

            self._logger.info(
                "Checkpoint loaded",
                catalog=catalog_name,
                last_page=data["last_processed_page"],
            )

            return catalog, data["last_processed_page"]

        except Exception as e:
            self._logger.error(
                "Failed to load checkpoint",
                catalog=catalog_name,
                error=str(e),
            )
            return None

    def delete_checkpoint(self, catalog_name: str) -> bool:
        """Delete a checkpoint file.

        Args:
            catalog_name: Name of the catalog

        Returns:
            True if deleted, False if not found
        """
        safe_name = catalog_name.replace(" ", "_").replace("/", "-").lower()
        checkpoint_path = self._checkpoints_dir / f"{safe_name}.checkpoint.json"

        if checkpoint_path.exists():
            checkpoint_path.unlink()
            self._logger.info("Checkpoint deleted", catalog=catalog_name)
            return True
        return False

    def list_catalogs(self, directory: Path) -> list[Path]:
        """List available PDF catalogs in directory."""
        if not directory.exists():
            return []
        return sorted(directory.glob("*.pdf"))

    def list_extractions(self) -> list[Path]:
        """List all saved extraction files."""
        return sorted(self._output_dir.glob("*.json"))
