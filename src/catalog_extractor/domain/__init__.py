"""Domain layer - entities and interfaces."""

from catalog_extractor.domain.models import (
    Catalog,
    ExtractionResult,
    PageImage,
    Product,
    PromotionalRule,
    ValidationAlert,
)
from catalog_extractor.domain.interfaces import (
    CategoryNormalizer,
    LLMClient,
    PDFProcessor,
    ProductValidator,
    StorageRepository,
)

__all__ = [
    "Catalog",
    "CategoryNormalizer",
    "ExtractionResult",
    "LLMClient",
    "PageImage",
    "PDFProcessor",
    "Product",
    "ProductValidator",
    "PromotionalRule",
    "StorageRepository",
    "ValidationAlert",
]
