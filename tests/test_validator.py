"""Tests for product validator."""

import pytest

from catalog_extractor.application.validator import ProductValidatorService
from catalog_extractor.domain.models import (
    Product,
    PromotionalRule,
    PromotionType,
    ValidationAlertLevel,
)
from catalog_extractor.infrastructure.normalizer import FuzzyCategoryNormalizer


class TestProductValidatorService:
    """Tests for ProductValidatorService."""

    @pytest.fixture
    def normalizer(self) -> FuzzyCategoryNormalizer:
        """Create normalizer instance."""
        return FuzzyCategoryNormalizer()

    @pytest.fixture
    def validator(self, normalizer: FuzzyCategoryNormalizer) -> ProductValidatorService:
        """Create validator instance."""
        return ProductValidatorService(normalizer=normalizer)

    @pytest.fixture
    def valid_product(self) -> Product:
        """Create a valid product for testing."""
        return Product(
            codigo="85675",
            nome="Creme Hidratante Corporal Cuide-se Bem",
            linha="Cuide-se Bem",
            categoria="Hidratação",
            volume_peso="200ml",
            preco_regular=69.90,
            preco_promocional=55.90,
            promocao_ativa=True,
            pagina=5,
        )

    def test_validate_valid_product(
        self, validator: ProductValidatorService, valid_product: Product
    ) -> None:
        """Test validation of valid product."""
        alerts = validator.validate(valid_product)
        # Should have no errors
        errors = [a for a in alerts if a.level == ValidationAlertLevel.ERROR]
        assert len(errors) == 0

    def test_validate_missing_code(self, validator: ProductValidatorService) -> None:
        """Test validation catches missing code."""
        product = Product(
            codigo="",
            nome="Test Product",
            preco_regular=10.0,
            pagina=1,
        )
        alerts = validator.validate(product)
        assert any(a.field == "codigo" and a.level == ValidationAlertLevel.ERROR for a in alerts)

    def test_validate_missing_name(self, validator: ProductValidatorService) -> None:
        """Test validation catches missing/short name."""
        product = Product(
            codigo="12345",
            nome="AB",
            preco_regular=10.0,
            pagina=1,
        )
        alerts = validator.validate(product)
        assert any(a.field == "nome" and a.level == ValidationAlertLevel.ERROR for a in alerts)

    def test_validate_promo_higher_than_regular(
        self, validator: ProductValidatorService
    ) -> None:
        """Test validation catches promo price higher than regular."""
        product = Product(
            codigo="12345",
            nome="Test Product",
            preco_regular=50.0,
            preco_promocional=60.0,  # Wrong!
            pagina=1,
        )
        alerts = validator.validate(product)
        assert any(
            a.field == "preco_promocional" and a.level == ValidationAlertLevel.ERROR
            for a in alerts
        )

    def test_validate_zero_price(self, validator: ProductValidatorService) -> None:
        """Test validation catches zero price."""
        product = Product(
            codigo="12345",
            nome="Test Product",
            preco_regular=0.0,
            pagina=1,
        )
        alerts = validator.validate(product)
        assert any(
            a.field == "preco_regular" and a.level == ValidationAlertLevel.ERROR
            for a in alerts
        )

    def test_validate_unusual_discount(self, validator: ProductValidatorService) -> None:
        """Test validation warns about unusual discounts."""
        product = Product(
            codigo="12345",
            nome="Test Product",
            preco_regular=100.0,
            preco_promocional=10.0,  # 90% discount
            pagina=1,
        )
        alerts = validator.validate(product)
        assert any(
            a.field == "preco_promocional" and a.level == ValidationAlertLevel.WARNING
            for a in alerts
        )

    def test_validate_progressive_discount_without_tiers(
        self, validator: ProductValidatorService
    ) -> None:
        """Test validation warns about progressive discount without tiers."""
        product = Product(
            codigo="12345",
            nome="Test Product",
            preco_regular=100.0,
            regra_promocional=PromotionalRule(
                type=PromotionType.PROGRESSIVE_DISCOUNT,
                description="Desconto progressivo",
                # No discount_tiers defined
            ),
            pagina=1,
        )
        alerts = validator.validate(product)
        assert any(
            a.field == "regra_promocional" and a.level == ValidationAlertLevel.WARNING
            for a in alerts
        )

    def test_auto_correct_swaps_prices(
        self, validator: ProductValidatorService
    ) -> None:
        """Test auto-correct swaps inverted prices."""
        product = Product(
            codigo="12345",
            nome="Test Product",
            preco_regular=50.0,
            preco_promocional=70.0,  # Wrong order
            pagina=1,
        )
        corrected = validator.auto_correct(product)

        assert corrected.preco_regular == 70.0
        assert corrected.preco_promocional == 50.0

    def test_auto_correct_sets_promocao_ativa(
        self, validator: ProductValidatorService
    ) -> None:
        """Test auto-correct sets promocao_ativa flag."""
        product = Product(
            codigo="12345",
            nome="Test Product",
            preco_regular=100.0,
            preco_promocional=80.0,
            promocao_ativa=False,  # Should be True
            pagina=1,
        )
        corrected = validator.auto_correct(product)

        assert corrected.promocao_ativa is True

    def test_auto_correct_calculates_economia(
        self, validator: ProductValidatorService
    ) -> None:
        """Test auto-correct calculates savings."""
        product = Product(
            codigo="12345",
            nome="Test Product",
            preco_regular=100.0,
            preco_promocional=80.0,
            pagina=1,
        )
        corrected = validator.auto_correct(product)

        assert corrected.economia == 20.0

    def test_validate_batch_detects_duplicates(
        self, validator: ProductValidatorService
    ) -> None:
        """Test batch validation detects duplicate codes."""
        products = [
            Product(codigo="12345", nome="Product A", preco_regular=10.0, pagina=1),
            Product(codigo="12345", nome="Product B", preco_regular=20.0, pagina=2),
            Product(codigo="67890", nome="Product C", preco_regular=30.0, pagina=3),
        ]
        alerts = validator.validate_batch(products)

        assert "12345" in alerts
        assert any("Duplicate" in a.message for a in alerts["12345"])

    def test_get_validation_summary(
        self, validator: ProductValidatorService
    ) -> None:
        """Test validation summary generation."""
        alerts_by_product = {
            "12345": [
                validator._create_alert(ValidationAlertLevel.ERROR, "codigo", "Error"),
                validator._create_alert(ValidationAlertLevel.WARNING, "preco", "Warning"),
            ],
            "67890": [
                validator._create_alert(ValidationAlertLevel.INFO, "nome", "Info"),
            ],
        }
        # Need to create alerts manually for this test
        from catalog_extractor.domain.models import ValidationAlert

        alerts_by_product = {
            "12345": [
                ValidationAlert(level=ValidationAlertLevel.ERROR, field="codigo", message="Error"),
                ValidationAlert(level=ValidationAlertLevel.WARNING, field="preco", message="Warning"),
            ],
            "67890": [
                ValidationAlert(level=ValidationAlertLevel.INFO, field="nome", message="Info"),
            ],
        }

        summary = validator.get_validation_summary(alerts_by_product)

        assert summary["products_with_issues"] == 2
        assert summary["total_alerts"] == 3
        assert summary["by_level"]["errors"] == 1
        assert summary["by_level"]["warnings"] == 1
        assert summary["by_level"]["info"] == 1
