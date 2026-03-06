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
                "name": catalog.nome,
                "brand": catalog.marca,
                "cycle": catalog.ciclo,
                "validity_start": (
                    catalog.vigencia_inicio.isoformat() if catalog.vigencia_inicio else None
                ),
                "validity_end": (
                    catalog.vigencia_fim.isoformat() if catalog.vigencia_fim else None
                ),
                "total_pages": catalog.total_paginas,
                "source_file": str(catalog.source_file),
                "pages_processed": catalog.paginas_processadas,
                "pages_with_errors": catalog.paginas_com_erro,
                "exported_at": datetime.now().isoformat(),
            },
            "global_promotional_rules": [
                self._serialize_promo_rule(r) for r in catalog.regras_promocionais_globais
            ],
            "products": [self._serialize_product(p) for p in catalog.produtos],
            "statistics": {
                "total_products": len(catalog.produtos),
                "products_with_promotion": sum(1 for p in catalog.produtos if p.promocao_ativa),
                "categories": list(set(p.categoria_normalizada or "Other" for p in catalog.produtos)),
                "product_lines": list(set(p.linha for p in catalog.produtos if p.linha)),
            },
        }

    def _serialize_product(self, product: Product) -> dict[str, Any]:
        """Serialize a product to dict."""
        return {
            "code": product.codigo,
            "name": product.nome,
            "product_line": product.linha,
            "category": product.categoria,
            "normalized_category": product.categoria_normalizada,
            "volume_weight": product.volume_peso,
            "quantity": product.quantidade,
            "regular_price": product.preco_regular,
            "promotional_price": product.preco_promocional,
            "savings": product.economia,
            "discount_percentage": product.desconto_percentual,
            "promotion_active": product.promocao_ativa,
            "promotional_rule": (
                self._serialize_promo_rule(product.regra_promocional)
                if product.regra_promocional
                else None
            ),
            "features": product.caracteristicas,
            "page": product.pagina,
            "quadrant": product.quadrante,
            "alerts": [self._serialize_alert(a) for a in product.alertas],
        }

    def _serialize_promo_rule(self, rule: PromotionalRule) -> dict[str, Any]:
        """Serialize promotional rule to dict."""
        return {
            "type": rule.type.value,
            "description": rule.description,
            "conditions": rule.conditions,
            "discount_tiers": rule.discount_tiers,
            "combo_codes": rule.combo_codes,
            "related_pages": rule.related_pages,
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

    def _deserialize_promo_rule(self, data: dict[str, Any]) -> PromotionalRule:
        """Deserialize promotional rule from dict."""
        from catalog_extractor.domain.models import PromotionType

        return PromotionalRule(
            type=PromotionType(data.get("type", "none")),
            description=data.get("description"),
            conditions=data.get("conditions"),
            discount_tiers=data.get("discount_tiers"),
            combo_codes=data.get("combo_codes"),
            related_pages=data.get("related_pages"),
        )

    def _deserialize_alert(self, data: dict[str, Any]) -> ValidationAlert:
        """Deserialize validation alert from dict."""
        from catalog_extractor.domain.models import ValidationAlertLevel

        return ValidationAlert(
            level=ValidationAlertLevel(data.get("level", "info")),
            field=data.get("field", ""),
            message=data.get("message", ""),
            original_value=data.get("original_value"),
            corrected_value=data.get("corrected_value"),
        )

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

        # Reconstruct products (using English keys from serialization)
        products = []
        for p_data in data.get("products", []):
            # Parse promotional rule if present
            promo_rule = None
            if p_data.get("promotional_rule"):
                promo_rule = self._deserialize_promo_rule(p_data["promotional_rule"])

            # Parse alerts if present
            alerts = []
            for a_data in p_data.get("alerts", []):
                alerts.append(self._deserialize_alert(a_data))

            product = Product(
                codigo=p_data["code"],
                nome=p_data["name"],
                linha=p_data.get("product_line"),
                categoria=p_data.get("category"),
                categoria_normalizada=p_data.get("normalized_category"),
                volume_peso=p_data.get("volume_weight"),
                quantidade=p_data.get("quantity"),
                preco_regular=p_data["regular_price"],
                preco_promocional=p_data.get("promotional_price"),
                economia=p_data.get("savings"),
                desconto_percentual=p_data.get("discount_percentage"),
                promocao_ativa=p_data.get("promotion_active", False),
                regra_promocional=promo_rule,
                caracteristicas=p_data.get("features", []),
                pagina=p_data["page"],
                quadrante=p_data.get("quadrant"),
                alertas=alerts,
            )
            products.append(product)

        # Parse global promotional rules
        global_rules = []
        for rule_data in data.get("global_promotional_rules", []):
            global_rules.append(self._deserialize_promo_rule(rule_data))

        return Catalog(
            nome=metadata.get("name", "Unknown"),
            marca=metadata.get("brand", "Unknown"),
            ciclo=metadata.get("cycle"),
            total_paginas=metadata.get("total_pages", 0),
            source_file=Path(metadata.get("source_file", "")),
            produtos=products,
            regras_promocionais_globais=global_rules,
            paginas_processadas=metadata.get("pages_processed", 0),
            paginas_com_erro=metadata.get("pages_with_errors", []),
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

            # Reconstruct products (using English keys from serialization)
            products = []
            for p_data in catalog_data.get("products", []):
                # Parse promotional rule if present
                promo_rule = None
                if p_data.get("promotional_rule"):
                    promo_rule = self._deserialize_promo_rule(p_data["promotional_rule"])

                # Parse alerts if present
                alerts = []
                for a_data in p_data.get("alerts", []):
                    alerts.append(self._deserialize_alert(a_data))

                product = Product(
                    codigo=p_data["code"],
                    nome=p_data["name"],
                    linha=p_data.get("product_line"),
                    categoria=p_data.get("category"),
                    categoria_normalizada=p_data.get("normalized_category"),
                    volume_peso=p_data.get("volume_weight"),
                    quantidade=p_data.get("quantity"),
                    preco_regular=p_data["regular_price"],
                    preco_promocional=p_data.get("promotional_price"),
                    economia=p_data.get("savings"),
                    desconto_percentual=p_data.get("discount_percentage"),
                    promocao_ativa=p_data.get("promotion_active", False),
                    regra_promocional=promo_rule,
                    caracteristicas=p_data.get("features", []),
                    pagina=p_data["page"],
                    quadrante=p_data.get("quadrant"),
                    alertas=alerts,
                )
                products.append(product)

            # Parse global promotional rules
            global_rules = []
            for rule_data in catalog_data.get("global_promotional_rules", []):
                global_rules.append(self._deserialize_promo_rule(rule_data))

            catalog = Catalog(
                nome=metadata.get("name", catalog_name),
                marca=metadata.get("brand", "Unknown"),
                ciclo=metadata.get("cycle"),
                total_paginas=metadata.get("total_pages", 0),
                source_file=Path(metadata.get("source_file", "")),
                produtos=products,
                regras_promocionais_globais=global_rules,
                paginas_processadas=metadata.get("pages_processed", 0),
                paginas_com_erro=metadata.get("pages_with_errors", []),
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
