"""CLI entry point for the catalog extractor."""

import sys
from pathlib import Path
from typing import Annotated, Optional

import structlog
import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table

from catalog_extractor.config.settings import Settings
from catalog_extractor.container import create_container

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.dev.ConsoleRenderer(colors=True),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

app = typer.Typer(
    name="catalog-extractor",
    help="Extract product data from cosmetics catalogs using AI vision.",
    add_completion=False,
)
console = Console()


@app.command()
def extract(
    pdf_path: Annotated[
        Path,
        typer.Argument(
            help="Path to the PDF catalog file",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
        ),
    ],
    output: Annotated[
        Optional[Path],
        typer.Option(
            "--output", "-o",
            help="Output JSON file path",
        ),
    ] = None,
    catalog_name: Annotated[
        Optional[str],
        typer.Option(
            "--name", "-n",
            help="Catalog name (defaults to filename)",
        ),
    ] = None,
    brand: Annotated[
        Optional[str],
        typer.Option(
            "--brand", "-b",
            help="Brand name (e.g., 'O Boticário', 'Natura')",
        ),
    ] = None,
    resume: Annotated[
        bool,
        typer.Option(
            "--resume/--no-resume",
            help="Resume from checkpoint if available",
        ),
    ] = True,
    pages: Annotated[
        Optional[str],
        typer.Option(
            "--pages", "-p",
            help="Specific pages to extract (e.g., '1-10' or '1,5,10')",
        ),
    ] = None,
) -> None:
    """Extract products from a catalog PDF."""
    try:
        settings = Settings()
    except Exception as e:
        console.print(f"[red]Error loading settings: {e}[/red]")
        console.print("[yellow]Make sure GEMINI_API_KEY is set in .env file[/yellow]")
        raise typer.Exit(1)

    container = create_container(settings)
    service = container.extraction_service()

    console.print(f"\n[bold blue]Smart Catalog Reader[/bold blue]")
    console.print(f"Processing: [cyan]{pdf_path.name}[/cyan]\n")

    # Parse pages if specified
    page_list: list[int] | None = None
    if pages:
        page_list = _parse_pages(pages)
        console.print(f"Extracting specific pages: {page_list}")

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("Extracting...", total=100)

            def update_progress(current: int, total: int) -> None:
                progress.update(task, completed=int((current / total) * 100))

            if page_list:
                # Extract specific pages
                results = service.extract_pages(pdf_path, page_list, catalog_name)

                # Create minimal catalog for results
                from catalog_extractor.domain.models import Catalog
                catalog = Catalog(
                    nome=catalog_name or pdf_path.stem,
                    marca=brand or "Unknown",
                    total_paginas=len(page_list),
                    source_file=pdf_path,
                )
                for result in results:
                    if result.success:
                        catalog.produtos.extend(result.products)
            else:
                # Full extraction
                catalog = service.extract_catalog(
                    pdf_path,
                    catalog_name=catalog_name,
                    brand=brand,
                    resume=resume,
                    progress_callback=update_progress,
                )

        # Save results
        output_path = service.save_results(catalog, output)

        # Display summary
        _display_summary(catalog, output_path)

    except KeyboardInterrupt:
        console.print("\n[yellow]Extraction interrupted. Progress saved to checkpoint.[/yellow]")
        raise typer.Exit(130)
    except Exception as e:
        console.print(f"\n[red]Error during extraction: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def validate(
    json_path: Annotated[
        Path,
        typer.Argument(
            help="Path to extracted JSON file",
            exists=True,
            file_okay=True,
        ),
    ],
) -> None:
    """Validate an extracted catalog and show issues."""
    try:
        settings = Settings()
    except Exception:
        # Validation doesn't need API key
        settings = Settings(gemini_api_key="not-needed")

    container = create_container(settings)
    storage = container.storage()
    validator = container.validator()

    console.print(f"\n[bold blue]Validating: {json_path.name}[/bold blue]\n")

    catalog = storage.load_catalog(json_path)
    alerts = validator.validate_batch(catalog.produtos)
    summary = validator.get_validation_summary(alerts)

    # Display results
    table = Table(title="Validation Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Total Products", str(len(catalog.produtos)))
    table.add_row("Products with Issues", str(summary["products_with_issues"]))
    table.add_row("Errors", f"[red]{summary['by_level']['errors']}[/red]")
    table.add_row("Warnings", f"[yellow]{summary['by_level']['warnings']}[/yellow]")
    table.add_row("Info", str(summary["by_level"]["info"]))

    console.print(table)

    if summary["by_field"]:
        console.print("\n[bold]Issues by Field:[/bold]")
        for field, count in sorted(summary["by_field"].items(), key=lambda x: -x[1]):
            console.print(f"  {field}: {count}")


@app.command()
def list_catalogs(
    directory: Annotated[
        Path,
        typer.Argument(
            help="Directory containing PDF catalogs",
            exists=True,
            file_okay=False,
            dir_okay=True,
        ),
    ] = Path("data/catalogs"),
) -> None:
    """List available PDF catalogs in a directory."""
    pdfs = sorted(directory.glob("*.pdf"))

    if not pdfs:
        console.print(f"[yellow]No PDF files found in {directory}[/yellow]")
        return

    table = Table(title=f"Available Catalogs in {directory}")
    table.add_column("Filename", style="cyan")
    table.add_column("Size", style="green")

    for pdf in pdfs:
        size_mb = pdf.stat().st_size / (1024 * 1024)
        table.add_row(pdf.name, f"{size_mb:.1f} MB")

    console.print(table)


@app.command()
def info() -> None:
    """Show configuration and system information."""
    try:
        settings = Settings()
        api_configured = True
    except Exception:
        api_configured = False

    table = Table(title="Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("API Key Configured", "[green]Yes[/green]" if api_configured else "[red]No[/red]")

    if api_configured:
        table.add_row("Gemini Model", settings.gemini_model)
        table.add_row("Tier", "Paid" if settings.is_paid_tier else "Free")
        table.add_row("Max Workers", str(settings.max_workers))
        table.add_row("Default DPI", str(settings.dpi_default))
        table.add_row("Fuzzy Threshold", str(settings.fuzzy_match_threshold))
        table.add_row("Catalogs Dir", str(settings.catalogs_dir))
        table.add_row("Output Dir", str(settings.output_dir))

    console.print(table)


def _parse_pages(pages_str: str) -> list[int]:
    """Parse page specification string into list of page numbers."""
    pages: list[int] = []

    for part in pages_str.split(","):
        part = part.strip()
        if "-" in part:
            start, end = part.split("-")
            pages.extend(range(int(start), int(end) + 1))
        else:
            pages.append(int(part))

    return sorted(set(pages))


def _display_summary(catalog, output_path: Path) -> None:
    """Display extraction summary."""
    console.print("\n[bold green]Extraction Complete![/bold green]\n")

    table = Table(title="Extraction Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Catalog", catalog.nome)
    table.add_row("Brand", catalog.marca)
    table.add_row("Total Pages", str(catalog.total_paginas))
    table.add_row("Pages Processed", str(catalog.paginas_processadas))
    table.add_row("Products Extracted", str(len(catalog.produtos)))

    if catalog.paginas_com_erro:
        table.add_row(
            "Failed Pages",
            f"[yellow]{len(catalog.paginas_com_erro)}[/yellow] ({catalog.paginas_com_erro})"
        )

    # Category breakdown
    categories = {}
    for p in catalog.produtos:
        cat = p.categoria_normalizada or "Outros"
        categories[cat] = categories.get(cat, 0) + 1

    table.add_row("", "")
    table.add_row("[bold]Categories[/bold]", "")
    for cat, count in sorted(categories.items(), key=lambda x: -x[1])[:5]:
        table.add_row(f"  {cat}", str(count))

    console.print(table)
    console.print(f"\n[dim]Output saved to: {output_path}[/dim]\n")


if __name__ == "__main__":
    app()
