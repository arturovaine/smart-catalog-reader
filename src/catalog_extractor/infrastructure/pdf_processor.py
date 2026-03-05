"""PDF to image conversion implementation using pdf2image."""

from pathlib import Path

import structlog
from pdf2image import convert_from_path, pdfinfo_from_path
from PIL import Image

from catalog_extractor.domain.interfaces import PDFProcessor
from catalog_extractor.domain.models import PageImage

logger = structlog.get_logger()


class PDF2ImageProcessor(PDFProcessor):
    """PDF processor implementation using pdf2image library."""

    def __init__(self, default_dpi: int = 200, high_dpi: int = 300) -> None:
        """Initialize processor with DPI settings.

        Args:
            default_dpi: Default resolution for conversion
            high_dpi: Higher resolution for retry attempts
        """
        self._default_dpi = default_dpi
        self._high_dpi = high_dpi
        self._logger = logger.bind(component="PDF2ImageProcessor")

    def get_page_count(self, pdf_path: Path) -> int:
        """Get total number of pages in PDF."""
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        info = pdfinfo_from_path(str(pdf_path))
        return info.get("Pages", 0)

    def convert_to_images(
        self,
        pdf_path: Path,
        dpi: int | None = None,
        start_page: int | None = None,
        end_page: int | None = None,
    ) -> list[PageImage]:
        """Convert PDF pages to images.

        Args:
            pdf_path: Path to PDF file
            dpi: Resolution (uses default if not specified)
            start_page: First page to convert (1-indexed)
            end_page: Last page to convert (1-indexed, inclusive)

        Returns:
            List of PageImage objects
        """
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        dpi = dpi or self._default_dpi
        total_pages = self.get_page_count(pdf_path)

        self._logger.info(
            "Converting PDF to images",
            pdf=pdf_path.name,
            total_pages=total_pages,
            dpi=dpi,
            start_page=start_page,
            end_page=end_page,
        )

        # Prepare page range parameters
        kwargs: dict = {"dpi": dpi}
        if start_page:
            kwargs["first_page"] = start_page
        if end_page:
            kwargs["last_page"] = end_page

        # Convert pages
        images: list[Image.Image] = convert_from_path(str(pdf_path), **kwargs)

        # Calculate starting page number
        first_page_num = start_page or 1

        # Wrap in PageImage objects
        page_images = [
            PageImage(
                page_number=first_page_num + idx,
                image=img,
                dpi=dpi,
                source_file=pdf_path,
            )
            for idx, img in enumerate(images)
        ]

        self._logger.info(
            "Conversion complete",
            pages_converted=len(page_images),
        )

        return page_images

    def convert_single_page(
        self,
        pdf_path: Path,
        page_number: int,
        dpi: int | None = None,
    ) -> PageImage:
        """Convert a single page to image.

        Args:
            pdf_path: Path to PDF file
            page_number: Page number (1-indexed)
            dpi: Resolution (uses default if not specified)

        Returns:
            PageImage object
        """
        dpi = dpi or self._default_dpi

        self._logger.debug(
            "Converting single page",
            pdf=pdf_path.name,
            page=page_number,
            dpi=dpi,
        )

        images = convert_from_path(
            str(pdf_path),
            dpi=dpi,
            first_page=page_number,
            last_page=page_number,
        )

        if not images:
            raise ValueError(f"Could not convert page {page_number}")

        return PageImage(
            page_number=page_number,
            image=images[0],
            dpi=dpi,
            source_file=pdf_path,
        )

    def convert_with_retry(
        self,
        pdf_path: Path,
        page_number: int,
    ) -> PageImage:
        """Convert page with automatic DPI retry on failure.

        First attempts with default DPI, then retries with high DPI.

        Args:
            pdf_path: Path to PDF file
            page_number: Page number (1-indexed)

        Returns:
            PageImage object
        """
        try:
            return self.convert_single_page(pdf_path, page_number, self._default_dpi)
        except Exception as e:
            self._logger.warning(
                "Retrying with higher DPI",
                page=page_number,
                error=str(e),
                retry_dpi=self._high_dpi,
            )
            return self.convert_single_page(pdf_path, page_number, self._high_dpi)
