# Smart Catalog Reader

Extract product data from cosmetics catalogs using AI vision (Gemini).

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                           CLI (Typer)                                │
│                         src/catalog_extractor/main.py               │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Dependency Injection Container                    │
│                      src/catalog_extractor/container.py             │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
           ┌─────────────────────┼─────────────────────┐
           ▼                     ▼                     ▼
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│   Application    │  │   Application    │  │   Application    │
│ ExtractionService│  │    Validator     │  │   (Orchestrator) │
└────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘
         │                     │                     │
         └─────────────────────┼─────────────────────┘
                               │
         ┌─────────────────────┼─────────────────────┐
         ▼                     ▼                     ▼
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│  Infrastructure  │  │  Infrastructure  │  │  Infrastructure  │
│  PDFProcessor    │  │   GeminiClient   │  │  CategoryNorm.   │
│  (pdf2image)     │  │   (LLM Vision)   │  │  (thefuzz)       │
└──────────────────┘  └──────────────────┘  └──────────────────┘
                               │
                               ▼
                    ┌──────────────────┐
                    │  Infrastructure  │
                    │ JSONStorage      │
                    │ (Persistence)    │
                    └──────────────────┘
```

## Features

- **PDF to Image Conversion**: Convert catalog pages with configurable DPI
- **AI Vision Extraction**: Use Gemini to extract product data from images
- **Category Normalization**: Fuzzy matching to normalize categories
- **Data Validation**: Validate extracted data with auto-correction
- **Checkpointing**: Resume interrupted extractions
- **Rate Limiting**: Exponential backoff for API rate limits
- **Progress Tracking**: Real-time progress with Rich

## Installation

```bash
# Clone the repository
cd smart-catalog-reader

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install -e .

# For development
pip install -e ".[dev]"
```

## Configuration

Create a `.env` file (see `.env.example`):

```bash
# Required
GEMINI_API_KEY=your_api_key_here

# Optional
IS_PAID_TIER=false
GEMINI_MODEL=gemini-2.5-flash
DPI_DEFAULT=200
FUZZY_MATCH_THRESHOLD=75
```

## Usage

### Extract a catalog

```bash
# Basic extraction
catalog-extractor extract data/catalogs/boticario-c03.pdf

# With options
catalog-extractor extract data/catalogs/natura-c03.pdf \
  --name "Natura Ciclo 03" \
  --brand "Natura" \
  --output data/output/natura-c03.json

# Extract specific pages
catalog-extractor extract data/catalogs/boticario-c03.pdf --pages "1-10,50,100-110"
```

### Validate extracted data

```bash
catalog-extractor validate data/output/natura-c03.json
```

### List available catalogs

```bash
catalog-extractor list-catalogs data/catalogs/
```

### Show configuration

```bash
catalog-extractor info
```

## Project Structure

```
smart-catalog-reader/
├── src/catalog_extractor/
│   ├── domain/                 # Domain entities and interfaces
│   │   ├── models.py          # Product, Catalog, etc.
│   │   └── interfaces.py      # Abstract interfaces (ports)
│   ├── infrastructure/         # Concrete implementations
│   │   ├── pdf_processor.py   # PDF to image conversion
│   │   ├── llm_client.py      # Gemini API integration
│   │   ├── normalizer.py      # Category normalization
│   │   └── storage.py         # JSON persistence
│   ├── application/            # Use cases and services
│   │   ├── extraction_service.py
│   │   └── validator.py
│   ├── config/                 # Configuration
│   │   └── settings.py
│   ├── container.py            # Dependency injection
│   └── main.py                 # CLI entry point
├── data/
│   ├── catalogs/               # Input PDFs (gitignored)
│   └── output/                 # Extracted JSONs (gitignored)
├── tests/
├── pyproject.toml
└── README.md
```

## Output Format

```json
{
  "metadata": {
    "nome": "O Boticário - Ciclo 03",
    "marca": "O Boticário",
    "total_paginas": 197,
    "exported_at": "2025-03-05T18:30:00"
  },
  "produtos": [
    {
      "codigo": "85675",
      "nome": "Creme Relaxante Hidratante Corporal Cuide-se Bem",
      "linha": "Cuide-se Bem",
      "categoria": "Hidratação",
      "categoria_normalizada": "Corpo e Banho",
      "volume_peso": "200g",
      "preco_regular": 69.90,
      "preco_promocional": 55.90,
      "desconto_percentual": 20.03,
      "promocao_ativa": true,
      "regra_promocional": {
        "tipo": "simple_discount",
        "descricao": "Desconto direto"
      },
      "caracteristicas": ["Vegano", "Sensação relaxante"],
      "pagina": 2,
      "alertas": []
    }
  ],
  "estatisticas": {
    "total_produtos": 1250,
    "produtos_com_promocao": 890,
    "categorias": ["Corpo e Banho", "Perfumaria", "Maquiagem", ...],
    "linhas": ["Cuide-se Bem", "Botik", "Nativa SPA", ...]
  }
}
```

## Development

```bash
# Run tests
pytest

# Run tests with coverage
pytest --cov=catalog_extractor

# Type checking
mypy src/

# Linting
ruff check src/
```

## SOLID Principles Applied

- **Single Responsibility**: Each class has one reason to change
- **Open/Closed**: Extend via new implementations, not modifications
- **Liskov Substitution**: Interfaces define contracts
- **Interface Segregation**: Small, focused interfaces
- **Dependency Inversion**: Depend on abstractions, not concretions

## License

MIT
