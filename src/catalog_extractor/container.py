"""Dependency Injection container using dependency-injector."""

from dependency_injector import containers, providers

from catalog_extractor.application.extraction_service import CatalogExtractionService
from catalog_extractor.application.validator import ProductValidatorService
from catalog_extractor.config.settings import Settings, get_settings
from catalog_extractor.infrastructure.llm_client import GeminiClient
from catalog_extractor.infrastructure.normalizer import FuzzyCategoryNormalizer
from catalog_extractor.infrastructure.pdf_processor import PDF2ImageProcessor
from catalog_extractor.infrastructure.storage import JSONStorageRepository


class Container(containers.DeclarativeContainer):
    """Dependency Injection container for the application."""

    # Configuration
    config = providers.Singleton(get_settings)

    # Infrastructure layer
    pdf_processor = providers.Singleton(
        PDF2ImageProcessor,
        default_dpi=config.provided.dpi_default,
        high_dpi=config.provided.dpi_high,
    )

    llm_client = providers.Singleton(
        GeminiClient,
        api_key=config.provided.gemini_api_key,
        model_name=config.provided.gemini_model,
        max_workers=config.provided.max_workers,
        max_retries=config.provided.max_retries,
    )

    normalizer = providers.Singleton(
        FuzzyCategoryNormalizer,
        threshold=config.provided.fuzzy_match_threshold,
    )

    storage = providers.Singleton(
        JSONStorageRepository,
        output_dir=config.provided.output_dir,
    )

    # Application layer
    validator = providers.Singleton(
        ProductValidatorService,
        normalizer=normalizer,
    )

    extraction_service = providers.Singleton(
        CatalogExtractionService,
        pdf_processor=pdf_processor,
        llm_client=llm_client,
        normalizer=normalizer,
        validator=validator,
        storage=storage,
    )


def create_container(settings: Settings | None = None) -> Container:
    """Create and wire the DI container.

    Args:
        settings: Optional settings override

    Returns:
        Configured container
    """
    container = Container()

    if settings:
        container.config.override(providers.Object(settings))

    return container
