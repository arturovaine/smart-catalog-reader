"""Domain models representing catalog entities."""

from datetime import date
from enum import Enum
from pathlib import Path
from typing import Any

from PIL import Image
from pydantic import BaseModel, Field, field_validator


class PromotionType(str, Enum):
    """Types of promotions found in catalogs."""

    NONE = "none"
    SIMPLE_DISCOUNT = "simple_discount"
    PROGRESSIVE_DISCOUNT = "progressive_discount"
    COMBO = "combo"
    BUY_X_PAY_Y = "buy_x_pay_y"
    PACK = "pack"


class ValidationAlertLevel(str, Enum):
    """Severity levels for validation alerts."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class ValidationAlert(BaseModel):
    """Alert generated during data validation."""

    level: ValidationAlertLevel
    field: str
    message: str
    original_value: Any = None
    corrected_value: Any = None


class PromotionalRule(BaseModel):
    """Represents complex promotional rules."""

    type: PromotionType = PromotionType.NONE
    description: str | None = None
    conditions: dict[str, Any] = Field(default_factory=dict)
    # For progressive discounts: {"1_unit": 0.20, "2_units": 0.30, "3_plus": 0.40}
    discount_tiers: dict[str, float] = Field(default_factory=dict)
    # For combos: list of product codes included
    combo_codes: list[str] = Field(default_factory=list)
    # Related pages for cross-reference
    related_pages: list[int] = Field(default_factory=list)


class Product(BaseModel):
    """Represents a product extracted from the catalog."""

    # Identification
    codigo: str = Field(..., min_length=1, description="Product code (typically 5 digits)")
    nome: str = Field(..., min_length=1, description="Product name")

    # Categorization
    linha: str | None = Field(default=None, description="Product line (e.g., Cuide-se Bem)")
    categoria: str | None = Field(default=None, description="Raw category from extraction")
    categoria_normalizada: str | None = Field(
        default=None, description="Normalized category after fuzzy matching"
    )

    # Physical attributes
    volume_peso: str | None = Field(default=None, description="Volume or weight (e.g., 200ml)")
    quantidade: str | None = Field(default=None, description="Quantity in pack")

    # Pricing
    preco_regular: float = Field(default=0.0, ge=0, description="Regular price")
    preco_promocional: float | None = Field(default=None, ge=0, description="Promotional price")
    economia: float | None = Field(default=None, ge=0, description="Savings amount")

    # Promotions
    promocao_ativa: bool = Field(default=False)
    regra_promocional: PromotionalRule | None = None

    # Characteristics
    caracteristicas: list[str] = Field(default_factory=list)

    # Metadata
    pagina: int = Field(..., ge=1, description="Page number in catalog")
    quadrante: str | None = Field(default=None, description="Position on page for validation")

    # Validation
    alertas: list[ValidationAlert] = Field(default_factory=list)

    @field_validator("codigo")
    @classmethod
    def normalize_codigo(cls, v: str) -> str:
        """Ensure codigo is stripped and padded if needed."""
        return v.strip().zfill(5) if v.strip().isdigit() else v.strip()

    @field_validator("preco_regular", mode="before")
    @classmethod
    def parse_regular_price(cls, v: Any) -> float:
        """Parse regular price, defaulting to 0.0 if None."""
        if v is None:
            return 0.0
        if isinstance(v, (int, float)):
            return float(v)
        if isinstance(v, str):
            cleaned = v.replace("R$", "").replace(" ", "").replace(".", "").replace(",", ".")
            try:
                return float(cleaned)
            except ValueError:
                return 0.0
        return 0.0

    @field_validator("preco_promocional", mode="before")
    @classmethod
    def parse_promotional_price(cls, v: Any) -> float | None:
        """Parse promotional price from various formats."""
        if v is None:
            return None
        if isinstance(v, (int, float)):
            return float(v)
        if isinstance(v, str):
            cleaned = v.replace("R$", "").replace(" ", "").replace(".", "").replace(",", ".")
            try:
                return float(cleaned)
            except ValueError:
                return None
        return None

    @property
    def desconto_percentual(self) -> float | None:
        """Calculate discount percentage."""
        if self.preco_promocional and self.preco_regular > 0:
            return round((1 - self.preco_promocional / self.preco_regular) * 100, 2)
        return None


class PageImage(BaseModel):
    """Represents a converted page image."""

    model_config = {"arbitrary_types_allowed": True}

    page_number: int = Field(..., ge=1)
    image: Image.Image
    dpi: int = Field(default=200)
    source_file: Path

    @property
    def dimensions(self) -> tuple[int, int]:
        """Get image dimensions (width, height)."""
        return self.image.size


class Catalog(BaseModel):
    """Represents a complete catalog."""

    nome: str = Field(..., description="Catalog name (e.g., O Boticário - Ciclo 03)")
    marca: str = Field(..., description="Brand name")
    ciclo: str | None = Field(default=None, description="Cycle identifier")
    vigencia_inicio: date | None = Field(default=None, description="Validity start date")
    vigencia_fim: date | None = Field(default=None, description="Validity end date")
    total_paginas: int = Field(default=0, ge=0)
    source_file: Path

    # Extracted data
    produtos: list[Product] = Field(default_factory=list)
    regras_promocionais_globais: list[PromotionalRule] = Field(default_factory=list)

    # Processing metadata
    paginas_processadas: int = Field(default=0, ge=0)
    paginas_com_erro: list[int] = Field(default_factory=list)


class ExtractionResult(BaseModel):
    """Result of extracting products from a single page."""

    page_number: int
    success: bool
    products: list[Product] = Field(default_factory=list)
    promotional_rules: list[PromotionalRule] = Field(default_factory=list)
    error_message: str | None = None
    raw_response: str | None = Field(default=None, exclude=True)
    retry_count: int = Field(default=0)
    processing_time_ms: float = Field(default=0.0)
