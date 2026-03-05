"""Main extraction service orchestrating the catalog extraction pipeline."""

from pathlib import Path
from typing import Callable

import structlog

from catalog_extractor.domain.interfaces import (
    CategoryNormalizer,
    LLMClient,
    PDFProcessor,
    ProductValidator,
    StorageRepository,
)
from catalog_extractor.domain.models import (
    Catalog,
    ExtractionResult,
    PageImage,
    Product,
)

logger = structlog.get_logger()


class CatalogExtractionService:
    """Service that orchestrates the complete catalog extraction pipeline.

    Implements the extraction workflow:
    1. Convert PDF pages to images
    2. Extract products using LLM vision
    3. Normalize categories
    4. Validate extracted data
    5. Save results with checkpointing
    """

    def __init__(
        self,
        pdf_processor: PDFProcessor,
        llm_client: LLMClient,
        normalizer: CategoryNormalizer,
        validator: ProductValidator,
        storage: StorageRepository,
        checkpoint_interval: int = 10,
    ) -> None:
        """Initialize extraction service.

        Args:
            pdf_processor: PDF to image converter
            llm_client: LLM client for extraction
            normalizer: Category normalizer
            validator: Product validator
            storage: Storage repository for persistence
            checkpoint_interval: Pages between checkpoints
        """
        self._pdf_processor = pdf_processor
        self._llm_client = llm_client
        self._normalizer = normalizer
        self._validator = validator
        self._storage = storage
        self._checkpoint_interval = checkpoint_interval
        self._logger = logger.bind(component="CatalogExtractionService")

    def extract_catalog(
        self,
        pdf_path: Path,
        catalog_name: str | None = None,
        brand: str | None = None,
        resume: bool = True,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> Catalog:
        """Extract all products from a catalog PDF.

        Args:
            pdf_path: Path to the PDF file
            catalog_name: Optional catalog name (defaults to filename)
            brand: Brand name (e.g., "O Boticário", "Natura")
            resume: Whether to resume from checkpoint if available
            progress_callback: Optional callback(current_page, total_pages)

        Returns:
            Catalog object with extracted products
        """
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        # Determine catalog metadata
        catalog_name = catalog_name or pdf_path.stem
        brand = brand or self._infer_brand(pdf_path.name)

        self._logger.info(
            "Starting catalog extraction",
            catalog=catalog_name,
            brand=brand,
            pdf=pdf_path.name,
        )

        # Get total pages
        total_pages = self._pdf_processor.get_page_count(pdf_path)

        # Check for checkpoint
        start_page = 1
        catalog = Catalog(
            nome=catalog_name,
            marca=brand,
            total_paginas=total_pages,
            source_file=pdf_path,
        )

        if resume:
            checkpoint = self._storage.load_checkpoint(catalog_name)
            if checkpoint:
                catalog, start_page = checkpoint
                start_page += 1  # Resume from next page
                self._logger.info(
                    "Resuming from checkpoint",
                    last_page=start_page - 1,
                    products_so_far=len(catalog.produtos),
                )

        # Process pages in batches
        batch_size = 5
        all_products: list[Product] = list(catalog.produtos)
        pages_with_errors: list[int] = list(catalog.paginas_com_erro)

        for batch_start in range(start_page, total_pages + 1, batch_size):
            batch_end = min(batch_start + batch_size - 1, total_pages)

            self._logger.info(
                "Processing batch",
                pages=f"{batch_start}-{batch_end}",
                total=total_pages,
            )

            # Convert batch to images
            page_images = self._pdf_processor.convert_to_images(
                pdf_path,
                start_page=batch_start,
                end_page=batch_end,
            )

            # Extract products from batch
            results = self._llm_client.extract_batch(page_images)

            # Process results
            for result in results:
                if result.success:
                    # Normalize and validate each product
                    for product in result.products:
                        product = self._process_product(product)
                        all_products.append(product)
                else:
                    pages_with_errors.append(result.page_number)
                    self._logger.warning(
                        "Page extraction failed",
                        page=result.page_number,
                        error=result.error_message,
                    )

                # Report progress
                if progress_callback:
                    progress_callback(result.page_number, total_pages)

            # Update catalog
            catalog.produtos = all_products
            catalog.paginas_processadas = batch_end
            catalog.paginas_com_erro = pages_with_errors

            # Save checkpoint
            if batch_end % self._checkpoint_interval == 0 or batch_end == total_pages:
                self._storage.save_checkpoint(catalog, batch_end)

        # Final cleanup
        self._storage.delete_checkpoint(catalog_name)

        self._logger.info(
            "Extraction complete",
            catalog=catalog_name,
            total_products=len(catalog.produtos),
            pages_with_errors=len(catalog.paginas_com_erro),
        )

        return catalog

    def extract_pages(
        self,
        pdf_path: Path,
        pages: list[int],
        catalog_name: str | None = None,
    ) -> list[ExtractionResult]:
        """Extract products from specific pages only.

        Args:
            pdf_path: Path to PDF file
            pages: List of page numbers to extract
            catalog_name: Optional catalog name

        Returns:
            List of ExtractionResult objects
        """
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        self._logger.info(
            "Extracting specific pages",
            pdf=pdf_path.name,
            pages=pages,
        )

        results: list[ExtractionResult] = []

        for page_num in pages:
            page_image = self._pdf_processor.convert_single_page(pdf_path, page_num)
            result = self._llm_client.extract_products(
                page_image.image,
                page_num,
            )

            # Process products
            if result.success:
                result.products = [
                    self._process_product(p) for p in result.products
                ]

            results.append(result)

        return results

    def _process_product(self, product: Product) -> Product:
        """Process a single product: normalize and validate.

        Args:
            product: Raw extracted product

        Returns:
            Processed product with normalized category and alerts
        """
        # Normalize category
        if product.categoria:
            product.categoria_normalizada = self._normalizer.normalize(
                product.categoria
            )

        # Validate and auto-correct
        product = self._validator.auto_correct(product)

        # Add remaining validation alerts
        alerts = self._validator.validate(product)
        product.alertas.extend(alerts)

        return product

    def _infer_brand(self, filename: str) -> str:
        """Infer brand name from filename."""
        filename_lower = filename.lower()

        brand_patterns = {
            "boticario": "O Boticário",
            "boticário": "O Boticário",
            "natura": "Natura",
            "avon": "Avon",
            "eudora": "Eudora",
            "quem disse": "Quem Disse, Berenice?",
        }

        for pattern, brand in brand_patterns.items():
            if pattern in filename_lower:
                return brand

        return "Unknown"

    def save_results(
        self,
        catalog: Catalog,
        output_path: Path | None = None,
    ) -> Path:
        """Save extraction results.

        Args:
            catalog: Catalog to save
            output_path: Optional custom output path

        Returns:
            Path where results were saved
        """
        return self._storage.save_catalog(catalog, output_path)

    def get_validation_report(self, catalog: Catalog) -> dict:
        """Generate validation report for a catalog.

        Args:
            catalog: Catalog to validate

        Returns:
            Validation report with statistics
        """
        alerts_by_product = self._validator.validate_batch(catalog.produtos)
        summary = self._validator.get_validation_summary(alerts_by_product)

        return {
            "catalog": catalog.nome,
            "total_products": len(catalog.produtos),
            "validation_summary": summary,
            "details": {
                code: [a.model_dump() for a in alerts]
                for code, alerts in alerts_by_product.items()
            },
        }

    def retry_failed_pages(
        self,
        pdf_path: Path,
        catalog: Catalog,
        use_high_dpi: bool = True,
    ) -> Catalog:
        """Retry extraction for pages that failed.

        Args:
            pdf_path: Path to PDF file
            catalog: Catalog with failed pages
            use_high_dpi: Whether to use higher DPI for retry

        Returns:
            Updated catalog
        """
        if not catalog.paginas_com_erro:
            self._logger.info("No failed pages to retry")
            return catalog

        self._logger.info(
            "Retrying failed pages",
            pages=catalog.paginas_com_erro,
            use_high_dpi=use_high_dpi,
        )

        still_failed: list[int] = []
        dpi = 300 if use_high_dpi else 200

        for page_num in catalog.paginas_com_erro:
            try:
                page_image = self._pdf_processor.convert_single_page(
                    pdf_path, page_num, dpi=dpi
                )
                result = self._llm_client.extract_products(
                    page_image.image,
                    page_num,
                )

                if result.success:
                    for product in result.products:
                        product = self._process_product(product)
                        catalog.produtos.append(product)
                else:
                    still_failed.append(page_num)

            except Exception as e:
                self._logger.error(
                    "Retry failed",
                    page=page_num,
                    error=str(e),
                )
                still_failed.append(page_num)

        catalog.paginas_com_erro = still_failed
        return catalog
