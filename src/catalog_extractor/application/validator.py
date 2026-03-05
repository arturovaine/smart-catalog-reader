"""Product validation service."""

import re
from typing import Any

import structlog

from catalog_extractor.domain.interfaces import CategoryNormalizer, ProductValidator
from catalog_extractor.domain.models import Product, ValidationAlert, ValidationAlertLevel

logger = structlog.get_logger()


class ProductValidatorService(ProductValidator):
    """Service for validating extracted product data."""

    def __init__(
        self,
        normalizer: CategoryNormalizer,
        strict_mode: bool = False,
    ) -> None:
        """Initialize validator.

        Args:
            normalizer: Category normalizer for category validation
            strict_mode: If True, treat warnings as errors
        """
        self._normalizer = normalizer
        self._strict_mode = strict_mode
        self._logger = logger.bind(component="ProductValidatorService")

        # Validation rules configuration
        self._min_code_length = 4
        self._max_code_length = 6
        self._min_price = 0.01
        self._max_price = 10000.0

    def validate(self, product: Product) -> list[ValidationAlert]:
        """Validate a single product and return alerts.

        Args:
            product: Product to validate

        Returns:
            List of validation alerts
        """
        alerts: list[ValidationAlert] = []

        # Run all validation checks
        alerts.extend(self._validate_code(product))
        alerts.extend(self._validate_name(product))
        alerts.extend(self._validate_prices(product))
        alerts.extend(self._validate_category(product))
        alerts.extend(self._validate_volume_weight(product))
        alerts.extend(self._validate_promotion_consistency(product))

        return alerts

    def _validate_code(self, product: Product) -> list[ValidationAlert]:
        """Validate product code."""
        alerts = []
        code = product.codigo

        if not code:
            alerts.append(
                ValidationAlert(
                    level=ValidationAlertLevel.ERROR,
                    field="codigo",
                    message="Product code is missing",
                )
            )
            return alerts

        # Check if code is numeric
        if not code.isdigit():
            alerts.append(
                ValidationAlert(
                    level=ValidationAlertLevel.WARNING,
                    field="codigo",
                    message=f"Product code contains non-numeric characters: {code}",
                    original_value=code,
                )
            )

        # Check code length
        if len(code) < self._min_code_length:
            alerts.append(
                ValidationAlert(
                    level=ValidationAlertLevel.WARNING,
                    field="codigo",
                    message=f"Product code seems too short: {code}",
                    original_value=code,
                )
            )
        elif len(code) > self._max_code_length:
            alerts.append(
                ValidationAlert(
                    level=ValidationAlertLevel.WARNING,
                    field="codigo",
                    message=f"Product code seems too long: {code}",
                    original_value=code,
                )
            )

        return alerts

    def _validate_name(self, product: Product) -> list[ValidationAlert]:
        """Validate product name."""
        alerts = []
        name = product.nome

        if not name or len(name.strip()) < 3:
            alerts.append(
                ValidationAlert(
                    level=ValidationAlertLevel.ERROR,
                    field="nome",
                    message="Product name is missing or too short",
                    original_value=name,
                )
            )
            return alerts

        # Check for suspicious patterns (likely OCR errors)
        if re.search(r"[^\w\sáéíóúâêîôûãõàèìòùçÁÉÍÓÚÂÊÎÔÛÃÕÀÈÌÒÙÇ°º%/\-\+\(\)]", name):
            alerts.append(
                ValidationAlert(
                    level=ValidationAlertLevel.INFO,
                    field="nome",
                    message="Product name contains unusual characters",
                    original_value=name,
                )
            )

        return alerts

    def _validate_prices(self, product: Product) -> list[ValidationAlert]:
        """Validate pricing information."""
        alerts = []
        regular = product.preco_regular
        promo = product.preco_promocional

        # Regular price validation
        if regular <= 0:
            alerts.append(
                ValidationAlert(
                    level=ValidationAlertLevel.ERROR,
                    field="preco_regular",
                    message="Regular price is zero or negative",
                    original_value=regular,
                )
            )
        elif regular > self._max_price:
            alerts.append(
                ValidationAlert(
                    level=ValidationAlertLevel.WARNING,
                    field="preco_regular",
                    message=f"Regular price seems unusually high: R$ {regular}",
                    original_value=regular,
                )
            )

        # Promotional price validation
        if promo is not None:
            if promo <= 0:
                alerts.append(
                    ValidationAlert(
                        level=ValidationAlertLevel.WARNING,
                        field="preco_promocional",
                        message="Promotional price is zero or negative",
                        original_value=promo,
                    )
                )
            elif promo > regular:
                alerts.append(
                    ValidationAlert(
                        level=ValidationAlertLevel.ERROR,
                        field="preco_promocional",
                        message=f"Promotional price (R$ {promo}) is higher than regular price (R$ {regular})",
                        original_value=promo,
                        corrected_value=None,
                    )
                )
            elif promo == regular:
                alerts.append(
                    ValidationAlert(
                        level=ValidationAlertLevel.INFO,
                        field="preco_promocional",
                        message="Promotional price equals regular price (no discount)",
                        original_value=promo,
                    )
                )

            # Check discount percentage is reasonable
            if regular > 0 and promo > 0:
                discount_pct = (1 - promo / regular) * 100
                if discount_pct > 80:
                    alerts.append(
                        ValidationAlert(
                            level=ValidationAlertLevel.WARNING,
                            field="preco_promocional",
                            message=f"Discount seems unusually high: {discount_pct:.1f}%",
                            original_value=promo,
                        )
                    )

        # Validate economia field if present
        if product.economia and promo and regular:
            expected_savings = round(regular - promo, 2)
            if abs(product.economia - expected_savings) > 0.10:
                alerts.append(
                    ValidationAlert(
                        level=ValidationAlertLevel.WARNING,
                        field="economia",
                        message=f"Savings value doesn't match price difference. Expected: R$ {expected_savings}, Got: R$ {product.economia}",
                        original_value=product.economia,
                        corrected_value=expected_savings,
                    )
                )

        return alerts

    def _validate_category(self, product: Product) -> list[ValidationAlert]:
        """Validate category normalization."""
        alerts = []

        # Normalize category if not already done
        if product.categoria and not product.categoria_normalizada:
            normalized = self._normalizer.normalize(product.categoria)
            if normalized == "Outros":
                alerts.append(
                    ValidationAlert(
                        level=ValidationAlertLevel.INFO,
                        field="categoria",
                        message=f"Category could not be normalized: {product.categoria}",
                        original_value=product.categoria,
                        corrected_value="Outros",
                    )
                )

        return alerts

    def _validate_volume_weight(self, product: Product) -> list[ValidationAlert]:
        """Validate volume/weight information."""
        alerts = []
        vol_peso = product.volume_peso

        if not vol_peso:
            return alerts

        # Check for common patterns
        valid_patterns = [
            r"\d+\s*ml",
            r"\d+\s*g",
            r"\d+\s*kg",
            r"\d+\s*l",
            r"\d+\s*unidades?",
            r"\d+\s*un",
            r"\d+\s*x\s*\d+",
        ]

        has_valid_pattern = any(
            re.search(pattern, vol_peso.lower()) for pattern in valid_patterns
        )

        if not has_valid_pattern:
            alerts.append(
                ValidationAlert(
                    level=ValidationAlertLevel.INFO,
                    field="volume_peso",
                    message=f"Volume/weight format not recognized: {vol_peso}",
                    original_value=vol_peso,
                )
            )

        return alerts

    def _validate_promotion_consistency(self, product: Product) -> list[ValidationAlert]:
        """Validate promotion flag consistency."""
        alerts = []

        # If has promotional price, should have promocao_ativa = True
        if product.preco_promocional and product.preco_promocional < product.preco_regular:
            if not product.promocao_ativa:
                alerts.append(
                    ValidationAlert(
                        level=ValidationAlertLevel.INFO,
                        field="promocao_ativa",
                        message="Product has promotional price but promocao_ativa is False",
                        original_value=False,
                        corrected_value=True,
                    )
                )

        # If has promotional rule, should have proper type
        if product.regra_promocional:
            rule = product.regra_promocional
            if rule.type.value == "progressive_discount" and not rule.discount_tiers:
                alerts.append(
                    ValidationAlert(
                        level=ValidationAlertLevel.WARNING,
                        field="regra_promocional",
                        message="Progressive discount rule has no discount tiers defined",
                    )
                )
            elif rule.type.value == "combo" and not rule.combo_codes:
                alerts.append(
                    ValidationAlert(
                        level=ValidationAlertLevel.WARNING,
                        field="regra_promocional",
                        message="Combo rule has no combo codes defined",
                    )
                )

        return alerts

    def validate_batch(self, products: list[Product]) -> dict[str, list[ValidationAlert]]:
        """Validate multiple products.

        Args:
            products: List of products to validate

        Returns:
            Dict mapping product codes to their alerts
        """
        results: dict[str, list[ValidationAlert]] = {}

        for product in products:
            alerts = self.validate(product)
            if alerts:
                results[product.codigo] = alerts

        # Check for duplicate codes
        codes = [p.codigo for p in products]
        duplicates = set(c for c in codes if codes.count(c) > 1)

        for dup_code in duplicates:
            if dup_code not in results:
                results[dup_code] = []
            results[dup_code].append(
                ValidationAlert(
                    level=ValidationAlertLevel.WARNING,
                    field="codigo",
                    message=f"Duplicate product code found: {dup_code}",
                    original_value=dup_code,
                )
            )

        return results

    def auto_correct(self, product: Product) -> Product:
        """Attempt to auto-correct validation issues.

        Args:
            product: Product with potential issues

        Returns:
            Corrected product (or original if no corrections possible)
        """
        # Create a copy of the product data
        corrected_data = product.model_dump()
        corrections_made = []

        # Normalize category
        if product.categoria and not product.categoria_normalizada:
            corrected_data["categoria_normalizada"] = self._normalizer.normalize(
                product.categoria
            )
            corrections_made.append("categoria_normalizada")

        # Fix promocao_ativa flag
        if (
            product.preco_promocional
            and product.preco_promocional < product.preco_regular
            and not product.promocao_ativa
        ):
            corrected_data["promocao_ativa"] = True
            corrections_made.append("promocao_ativa")

        # Calculate economia if missing
        if (
            product.preco_promocional
            and product.preco_regular
            and not product.economia
        ):
            corrected_data["economia"] = round(
                product.preco_regular - product.preco_promocional, 2
            )
            corrections_made.append("economia")

        # Swap prices if promotional > regular (likely OCR error)
        if (
            product.preco_promocional
            and product.preco_promocional > product.preco_regular
        ):
            corrected_data["preco_regular"] = product.preco_promocional
            corrected_data["preco_promocional"] = product.preco_regular
            corrections_made.append("prices_swapped")

            # Add alert about the swap
            corrected_data["alertas"] = list(product.alertas)
            corrected_data["alertas"].append(
                ValidationAlert(
                    level=ValidationAlertLevel.WARNING,
                    field="preco_regular",
                    message="Prices were swapped (promotional was higher than regular)",
                    original_value=product.preco_regular,
                    corrected_value=product.preco_promocional,
                )
            )

        if corrections_made:
            self._logger.debug(
                "Auto-corrections applied",
                codigo=product.codigo,
                corrections=corrections_made,
            )

        return Product(**corrected_data)

    def get_validation_summary(
        self, alerts_by_product: dict[str, list[ValidationAlert]]
    ) -> dict[str, Any]:
        """Generate summary of validation results.

        Args:
            alerts_by_product: Dict mapping product codes to alerts

        Returns:
            Summary statistics
        """
        total_alerts = sum(len(alerts) for alerts in alerts_by_product.values())

        errors = sum(
            1
            for alerts in alerts_by_product.values()
            for a in alerts
            if a.level == ValidationAlertLevel.ERROR
        )
        warnings = sum(
            1
            for alerts in alerts_by_product.values()
            for a in alerts
            if a.level == ValidationAlertLevel.WARNING
        )
        infos = sum(
            1
            for alerts in alerts_by_product.values()
            for a in alerts
            if a.level == ValidationAlertLevel.INFO
        )

        # Group by field
        by_field: dict[str, int] = {}
        for alerts in alerts_by_product.values():
            for alert in alerts:
                by_field[alert.field] = by_field.get(alert.field, 0) + 1

        return {
            "products_with_issues": len(alerts_by_product),
            "total_alerts": total_alerts,
            "by_level": {
                "errors": errors,
                "warnings": warnings,
                "info": infos,
            },
            "by_field": by_field,
        }
