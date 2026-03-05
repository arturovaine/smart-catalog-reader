"""Abstract interfaces (ports) following the Dependency Inversion Principle."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Protocol

from PIL import Image

from catalog_extractor.domain.models import (
    Catalog,
    ExtractionResult,
    PageImage,
    Product,
    ValidationAlert,
)


class PDFProcessor(ABC):
    """Interface for PDF to image conversion."""

    @abstractmethod
    def convert_to_images(
        self,
        pdf_path: Path,
        dpi: int = 200,
        start_page: int | None = None,
        end_page: int | None = None,
    ) -> list[PageImage]:
        """Convert PDF pages to images.

        Args:
            pdf_path: Path to the PDF file
            dpi: Resolution for conversion
            start_page: Optional start page (1-indexed)
            end_page: Optional end page (1-indexed, inclusive)

        Returns:
            List of PageImage objects
        """
        ...

    @abstractmethod
    def get_page_count(self, pdf_path: Path) -> int:
        """Get total number of pages in PDF."""
        ...

    @abstractmethod
    def convert_single_page(
        self,
        pdf_path: Path,
        page_number: int,
        dpi: int = 200,
    ) -> PageImage:
        """Convert a single page to image."""
        ...


class LLMClient(ABC):
    """Interface for LLM-based extraction."""

    @abstractmethod
    def extract_products(
        self,
        image: Image.Image,
        page_number: int,
        prompt: str | None = None,
    ) -> ExtractionResult:
        """Extract products from a page image using LLM vision.

        Args:
            image: PIL Image of the catalog page
            page_number: Page number for context
            prompt: Optional custom extraction prompt

        Returns:
            ExtractionResult with extracted products
        """
        ...

    @abstractmethod
    def extract_batch(
        self,
        pages: list[PageImage],
        prompt: str | None = None,
    ) -> list[ExtractionResult]:
        """Extract products from multiple pages in parallel.

        Args:
            pages: List of PageImage objects
            prompt: Optional custom extraction prompt

        Returns:
            List of ExtractionResult objects
        """
        ...


class CategoryNormalizer(Protocol):
    """Interface for category normalization using fuzzy matching."""

    def normalize(self, raw_category: str | None) -> str:
        """Normalize a category to a master category.

        Args:
            raw_category: Raw category string from extraction

        Returns:
            Normalized category string
        """
        ...

    def add_category(self, category: str) -> None:
        """Add a new master category."""
        ...

    def get_categories(self) -> list[str]:
        """Get list of master categories."""
        ...

    def get_synonyms(self, category: str) -> list[str]:
        """Get synonyms mapped to a master category."""
        ...


class ProductValidator(ABC):
    """Interface for product data validation."""

    @abstractmethod
    def validate(self, product: Product) -> list[ValidationAlert]:
        """Validate a product and return alerts.

        Args:
            product: Product to validate

        Returns:
            List of validation alerts
        """
        ...

    @abstractmethod
    def validate_batch(self, products: list[Product]) -> dict[str, list[ValidationAlert]]:
        """Validate multiple products.

        Args:
            products: List of products to validate

        Returns:
            Dict mapping product codes to their alerts
        """
        ...

    @abstractmethod
    def auto_correct(self, product: Product) -> Product:
        """Attempt to auto-correct validation issues.

        Args:
            product: Product with potential issues

        Returns:
            Corrected product (or original if no corrections possible)
        """
        ...


class StorageRepository(ABC):
    """Interface for data persistence."""

    @abstractmethod
    def save_catalog(self, catalog: Catalog, output_path: Path | None = None) -> Path:
        """Save extracted catalog data.

        Args:
            catalog: Catalog object to save
            output_path: Optional custom output path

        Returns:
            Path where data was saved
        """
        ...

    @abstractmethod
    def load_catalog(self, path: Path) -> Catalog:
        """Load a previously saved catalog."""
        ...

    @abstractmethod
    def save_checkpoint(
        self,
        catalog: Catalog,
        last_processed_page: int,
    ) -> Path:
        """Save extraction checkpoint for resuming."""
        ...

    @abstractmethod
    def load_checkpoint(self, catalog_name: str) -> tuple[Catalog, int] | None:
        """Load checkpoint if exists.

        Returns:
            Tuple of (partial catalog, last processed page) or None
        """
        ...

    @abstractmethod
    def list_catalogs(self, directory: Path) -> list[Path]:
        """List available PDF catalogs in directory."""
        ...
