# Smart Catalog Reader

Extract product data from cosmetics catalogs using AI vision (Gemini).

## Sample Catalogs

| O Boticário - Ciclo 03 | Natura - Ciclo 03 |
|:----------------------:|:-----------------:|
| ![O Boticário Cover](docs/images/boticario-cover.png) | ![Natura Cover](docs/images/natura-cover.png) |

### Extraction Results

| Metric | O Boticário C03 | Natura C03 | Total |
|--------|---------------:|------------:|------:|
| **Pages Processed** | 197 | 164 | 361 |
| **Products Extracted** | 1,638 | 1,206 | 2,844 |
| **Maquiagem** | 601 | 393 | 994 |
| **Corpo e Banho** | 328 | 309 | 637 |
| **Perfumaria** | 277 | 191 | 468 |
| **Cabelos** | 174 | 187 | 361 |
| **Outros** | 258 | 126 | 384 |

**Catalog Sources:**
- [O Boticário Catalogs](https://brcatalogos.com.br/oboticario/)
- [Natura Catalogs](https://brcatalogos.com.br/revista-natura/)

## Extraction Pipeline (Detailed Flow)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              INPUT: PDF Catalog                                  │
│                          (e.g., boticario-c03.pdf)                              │
└─────────────────────────────────────┬───────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │                         1. PDF PROCESSING                                  │  │
│  │                         ──────────────────                                 │  │
│  │   ┌─────────────┐      ┌─────────────┐      ┌─────────────┐               │  │
│  │   │   Page 1    │      │   Page 2    │      │   Page N    │               │  │
│  │   │    PDF      │ ───► │    PDF      │ ───► │    PDF      │               │  │
│  │   └──────┬──────┘      └──────┬──────┘      └──────┬──────┘               │  │
│  │          │                    │                    │                       │  │
│  │          ▼                    ▼                    ▼                       │  │
│  │   ┌─────────────┐      ┌─────────────┐      ┌─────────────┐               │  │
│  │   │   Image 1   │      │   Image 2   │      │   Image N   │               │  │
│  │   │  (PIL/PNG)  │      │  (PIL/PNG)  │      │  (PIL/PNG)  │               │  │
│  │   │  DPI: 200   │      │  DPI: 200   │      │  DPI: 200   │               │  │
│  │   └─────────────┘      └─────────────┘      └─────────────┘               │  │
│  │                                                                            │  │
│  │   Library: pdf2image (poppler)                                            │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────┬───────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │                     2. BATCH PROCESSING (5 pages/batch)                   │  │
│  │                     ───────────────────────────────────                   │  │
│  │                                                                            │  │
│  │   ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐    │  │
│  │   │ Batch 1 │   │ Batch 2 │   │ Batch 3 │   │   ...   │   │ Batch N │    │  │
│  │   │ Pages   │   │ Pages   │   │ Pages   │   │         │   │ Pages   │    │  │
│  │   │  1-5    │   │  6-10   │   │ 11-15   │   │         │   │196-197  │    │  │
│  │   └────┬────┘   └────┬────┘   └────┬────┘   └────┬────┘   └────┬────┘    │  │
│  │        │             │             │             │             │          │  │
│  │        └─────────────┴─────────────┴─────────────┴─────────────┘          │  │
│  │                                    │                                       │  │
│  │                    ┌───────────────┴───────────────┐                      │  │
│  │                    │      ThreadPoolExecutor       │                      │  │
│  │                    │    (max_workers: 2 or 10)     │                      │  │
│  │                    └───────────────────────────────┘                      │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────┬───────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │                      3. LLM EXTRACTION (Gemini Vision)                    │  │
│  │                      ─────────────────────────────────                    │  │
│  │                                                                            │  │
│  │   ┌──────────────────────────────────────────────────────────────────┐    │  │
│  │   │                     Gemini 2.5 Flash API                         │    │  │
│  │   │  ┌─────────────────────────────────────────────────────────────┐ │    │  │
│  │   │  │  PROMPT:                                                     │ │    │  │
│  │   │  │  - Extract product code, name, line, category               │ │    │  │
│  │   │  │  - Extract regular_price, promotional_price                 │ │    │  │
│  │   │  │  - Identify promotion type (simple, progressive, combo)     │ │    │  │
│  │   │  │  - Extract features (vegan, dermatologist tested, etc.)     │ │    │  │
│  │   │  │  - Detect page type (products, advertising, index)          │ │    │  │
│  │   │  └─────────────────────────────────────────────────────────────┘ │    │  │
│  │   │                              │                                    │    │  │
│  │   │                              ▼                                    │    │  │
│  │   │  ┌─────────────────────────────────────────────────────────────┐ │    │  │
│  │   │  │  OUTPUT: JSON with products[]                               │ │    │  │
│  │   │  │  {                                                          │ │    │  │
│  │   │  │    "produtos": [...],                                       │ │    │  │
│  │   │  │    "regras_promocionais_globais": [...],                   │ │    │  │
│  │   │  │    "tipo_pagina": "products"                               │ │    │  │
│  │   │  │  }                                                          │ │    │  │
│  │   │  └─────────────────────────────────────────────────────────────┘ │    │  │
│  │   └──────────────────────────────────────────────────────────────────┘    │  │
│  │                                                                            │  │
│  │   Retry Logic: Exponential backoff (tenacity) for rate limits            │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────┬───────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │                      4. CATEGORY NORMALIZATION                            │  │
│  │                      ─────────────────────────                            │  │
│  │                                                                            │  │
│  │   Raw Category              Fuzzy Match (thefuzz)         Normalized      │  │
│  │   ─────────────             ────────────────────          ──────────      │  │
│  │   "Hidratação"        ───►  score: 85  ───────────►  "Corpo e Banho"     │  │
│  │   "Perfume Feminino"  ───►  score: 90  ───────────►  "Perfumaria"        │  │
│  │   "Batom"             ───►  score: 88  ───────────►  "Maquiagem"         │  │
│  │   "Shampoo"           ───►  score: 92  ───────────►  "Cabelos"           │  │
│  │   "Desconhecido"      ───►  score: 45  ───────────►  "Outros"            │  │
│  │                                                                            │  │
│  │   Master Categories: Perfumaria, Maquiagem, Corpo e Banho, Cabelos,       │  │
│  │                      Skincare, Infantil, Masculino, Unhas, Acessórios,    │  │
│  │                      Kits e Presentes, Proteção Solar, Desodorantes       │  │
│  │                                                                            │  │
│  │   Threshold: 75 (configurable)                                            │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────┬───────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │                    5. VALIDATION & AUTO-CORRECTION                        │  │
│  │                    ───────────────────────────────                        │  │
│  │                                                                            │  │
│  │   ┌─────────────────────────────────────────────────────────────────┐     │  │
│  │   │  VALIDATION RULES:                                               │     │  │
│  │   │  ├── Code: 4-6 digits, alphanumeric                             │     │  │
│  │   │  ├── Name: min 3 chars, no suspicious characters                │     │  │
│  │   │  ├── Price: range 0.01 - 10,000 BRL                             │     │  │
│  │   │  ├── Discount: max 80%                                          │     │  │
│  │   │  ├── Promotional consistency: flags match prices                │     │  │
│  │   │  └── Duplicate detection: unique product codes                  │     │  │
│  │   └─────────────────────────────────────────────────────────────────┘     │  │
│  │                                                                            │  │
│  │   ┌─────────────────────────────────────────────────────────────────┐     │  │
│  │   │  AUTO-CORRECTIONS:                                               │     │  │
│  │   │  ├── Swap prices if promotional > regular                       │     │  │
│  │   │  ├── Calculate savings if missing                               │     │  │
│  │   │  ├── Set promotion_active flag if promo price exists           │     │  │
│  │   │  └── Normalize category if missing                              │     │  │
│  │   └─────────────────────────────────────────────────────────────────┘     │  │
│  │                                                                            │  │
│  │   Alerts: ERROR (critical) │ WARNING (review) │ INFO (informational)      │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────┬───────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │                       6. CHECKPOINTING (every 10 pages)                   │  │
│  │                       ─────────────────────────────────                   │  │
│  │                                                                            │  │
│  │   .checkpoints/                                                           │  │
│  │   └── boticario-c03.checkpoint.json                                       │  │
│  │       {                                                                    │  │
│  │         "catalog": { ... },            ◄── Full catalog state            │  │
│  │         "last_processed_page": 110,    ◄── Resume point                  │  │
│  │         "checkpoint_time": "..."       ◄── Timestamp                     │  │
│  │       }                                                                    │  │
│  │                                                                            │  │
│  │   On interrupt (Ctrl+C): Progress saved, resume with --resume             │  │
│  │   On completion: Checkpoint deleted automatically                         │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────┬───────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │                         7. JSON PERSISTENCE                               │  │
│  │                         ───────────────────                               │  │
│  │                                                                            │  │
│  │   data/output/boticario-c03_20260305_214252.json                          │  │
│  │   ┌─────────────────────────────────────────────────────────────────┐     │  │
│  │   │  {                                                               │     │  │
│  │   │    "metadata": {                                                 │     │  │
│  │   │      "name": "boticario-c03",                                   │     │  │
│  │   │      "brand": "O Boticário",                                    │     │  │
│  │   │      "total_pages": 197,                                        │     │  │
│  │   │      "pages_processed": 197                                     │     │  │
│  │   │    },                                                            │     │  │
│  │   │    "global_promotional_rules": [...],                           │     │  │
│  │   │    "products": [ 1638 products ],                               │     │  │
│  │   │    "statistics": {                                               │     │  │
│  │   │      "total_products": 1638,                                    │     │  │
│  │   │      "products_with_promotion": 1200,                           │     │  │
│  │   │      "categories": ["Maquiagem", "Corpo e Banho", ...]          │     │  │
│  │   │    }                                                             │     │  │
│  │   │  }                                                               │     │  │
│  │   └─────────────────────────────────────────────────────────────────┘     │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Clean Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                                                                  │
│   ┌──────────────────────────────────────────────────────────────────────────┐  │
│   │                           PRESENTATION LAYER                              │  │
│   │                                                                           │  │
│   │   ┌─────────────────────────────────────────────────────────────────┐    │  │
│   │   │                      CLI (Typer + Rich)                          │    │  │
│   │   │                       main.py                                    │    │  │
│   │   │  ┌──────────┐  ┌──────────┐  ┌───────────┐  ┌──────────┐       │    │  │
│   │   │  │ extract  │  │ validate │  │   list    │  │   info   │       │    │  │
│   │   │  │ command  │  │ command  │  │  command  │  │ command  │       │    │  │
│   │   │  └──────────┘  └──────────┘  └───────────┘  └──────────┘       │    │  │
│   │   │                      │                                          │    │  │
│   │   │                      ▼                                          │    │  │
│   │   │            Progress Bar │ Tables │ Console Output               │    │  │
│   │   └─────────────────────────────────────────────────────────────────┘    │  │
│   └──────────────────────────────────────────────────────────────────────────┘  │
│                                       │                                          │
│                                       ▼                                          │
│   ┌──────────────────────────────────────────────────────────────────────────┐  │
│   │                      DEPENDENCY INJECTION LAYER                          │  │
│   │                                                                           │  │
│   │   ┌─────────────────────────────────────────────────────────────────┐    │  │
│   │   │            DI Container (dependency-injector)                    │    │  │
│   │   │                      container.py                                │    │  │
│   │   │                                                                  │    │  │
│   │   │   Settings ─────┬──────────────────────────────────────────┐    │    │  │
│   │   │                 │                                          │    │    │  │
│   │   │   Providers:    │                                          │    │    │  │
│   │   │   ├── pdf_processor ──► Singleton                         │    │    │  │
│   │   │   ├── llm_client ─────► Singleton                         │    │    │  │
│   │   │   ├── normalizer ─────► Singleton                         │    │    │  │
│   │   │   ├── validator ──────► Singleton                         │    │    │  │
│   │   │   ├── storage ────────► Singleton                         │    │    │  │
│   │   │   └── extraction_service ► Factory                        │    │    │  │
│   │   └─────────────────────────────────────────────────────────────────┘    │  │
│   └──────────────────────────────────────────────────────────────────────────┘  │
│                                       │                                          │
│                                       ▼                                          │
│   ┌──────────────────────────────────────────────────────────────────────────┐  │
│   │                         APPLICATION LAYER                                │  │
│   │                        (Use Cases / Services)                            │  │
│   │                                                                           │  │
│   │   ┌─────────────────────────────────┐  ┌────────────────────────────┐    │  │
│   │   │   CatalogExtractionService      │  │  ProductValidatorService   │    │  │
│   │   │   extraction_service.py         │  │  validator.py              │    │  │
│   │   │                                 │  │                            │    │  │
│   │   │   Methods:                      │  │  Methods:                  │    │  │
│   │   │   ├── extract_catalog()         │  │  ├── validate()            │    │  │
│   │   │   ├── extract_pages()           │  │  ├── validate_batch()      │    │  │
│   │   │   ├── retry_failed_pages()      │  │  ├── auto_correct()        │    │  │
│   │   │   ├── save_results()            │  │  └── get_validation_summary│    │  │
│   │   │   └── get_validation_report()   │  │                            │    │  │
│   │   └────────────────┬────────────────┘  └────────────────────────────┘    │  │
│   │                    │                                                      │  │
│   │      Orchestrates: │                                                      │  │
│   │      PDF ──► LLM ──► Normalize ──► Validate ──► Store                    │  │
│   └──────────────────────────────────────────────────────────────────────────┘  │
│                                       │                                          │
│                                       ▼                                          │
│   ┌──────────────────────────────────────────────────────────────────────────┐  │
│   │                           DOMAIN LAYER                                   │  │
│   │                     (Entities / Interfaces / Ports)                      │  │
│   │                                                                           │  │
│   │   ┌─────────────────────────────────┐  ┌────────────────────────────┐    │  │
│   │   │        models.py                │  │      interfaces.py         │    │  │
│   │   │                                 │  │      (Ports/Contracts)     │    │  │
│   │   │   Entities:                     │  │                            │    │  │
│   │   │   ├── Product                   │  │   Abstract Classes:        │    │  │
│   │   │   ├── Catalog                   │  │   ├── PDFProcessor         │    │  │
│   │   │   ├── PromotionalRule           │  │   ├── LLMClient            │    │  │
│   │   │   ├── ExtractionResult          │  │   ├── CategoryNormalizer   │    │  │
│   │   │   ├── PageImage                 │  │   ├── ProductValidator     │    │  │
│   │   │   └── ValidationAlert           │  │   └── StorageRepository    │    │  │
│   │   │                                 │  │                            │    │  │
│   │   │   Enums:                        │  │   These define contracts   │    │  │
│   │   │   ├── PromotionType             │  │   that infrastructure      │    │  │
│   │   │   └── ValidationAlertLevel      │  │   must implement           │    │  │
│   │   └─────────────────────────────────┘  └────────────────────────────┘    │  │
│   └──────────────────────────────────────────────────────────────────────────┘  │
│                                       │                                          │
│                                       ▼                                          │
│   ┌──────────────────────────────────────────────────────────────────────────┐  │
│   │                       INFRASTRUCTURE LAYER                               │  │
│   │                    (Concrete Implementations / Adapters)                 │  │
│   │                                                                           │  │
│   │   ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐       │  │
│   │   │ PDF2ImageProcessor│  │   GeminiClient   │  │FuzzyCategoryNorm.│       │  │
│   │   │ pdf_processor.py │  │   llm_client.py  │  │  normalizer.py   │       │  │
│   │   │                  │  │                  │  │                  │       │  │
│   │   │ Implements:      │  │ Implements:      │  │ Implements:      │       │  │
│   │   │ PDFProcessor     │  │ LLMClient        │  │ CategoryNormalizer│      │  │
│   │   │                  │  │                  │  │                  │       │  │
│   │   │ Uses:            │  │ Uses:            │  │ Uses:            │       │  │
│   │   │ - pdf2image      │  │ - google-genai   │  │ - thefuzz        │       │  │
│   │   │ - Pillow         │  │ - tenacity       │  │ - rapidfuzz      │       │  │
│   │   └──────────────────┘  └──────────────────┘  └──────────────────┘       │  │
│   │                                                                           │  │
│   │   ┌──────────────────────────────────────────────────────────────┐       │  │
│   │   │               JSONStorageRepository                          │       │  │
│   │   │                    storage.py                                │       │  │
│   │   │                                                              │       │  │
│   │   │   Implements: StorageRepository                              │       │  │
│   │   │                                                              │       │  │
│   │   │   Methods:                                                   │       │  │
│   │   │   ├── save_catalog()        - Save to JSON                  │       │  │
│   │   │   ├── load_catalog()        - Load from JSON                │       │  │
│   │   │   ├── save_checkpoint()     - Save progress                 │       │  │
│   │   │   ├── load_checkpoint()     - Resume progress               │       │  │
│   │   │   ├── delete_checkpoint()   - Cleanup                       │       │  │
│   │   │   └── list_catalogs()       - List PDFs                     │       │  │
│   │   └──────────────────────────────────────────────────────────────┘       │  │
│   └──────────────────────────────────────────────────────────────────────────┘  │
│                                                                                  │
│   ┌──────────────────────────────────────────────────────────────────────────┐  │
│   │                        EXTERNAL DEPENDENCIES                             │  │
│   │                                                                           │  │
│   │     ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐               │  │
│   │     │ Gemini  │   │ Poppler │   │  JSON   │   │  File   │               │  │
│   │     │   API   │   │  (PDF)  │   │  Files  │   │ System  │               │  │
│   │     └─────────┘   └─────────┘   └─────────┘   └─────────┘               │  │
│   └──────────────────────────────────────────────────────────────────────────┘  │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Data Flow Diagram

```
                          ┌─────────────────────────────────────┐
                          │           User Request              │
                          │   catalog-extractor extract foo.pdf │
                          └──────────────────┬──────────────────┘
                                             │
                                             ▼
┌────────────────────────────────────────────────────────────────────────────────┐
│                                                                                 │
│  ┌─────────────┐      ┌─────────────┐      ┌─────────────┐      ┌───────────┐ │
│  │             │      │             │      │             │      │           │ │
│  │  PDF File   │─────►│ PDF2Image   │─────►│   Gemini    │─────►│ Normalizer│ │
│  │  (Input)    │      │  Processor  │      │   Client    │      │           │ │
│  │             │      │             │      │             │      │           │ │
│  └─────────────┘      └─────────────┘      └─────────────┘      └─────┬─────┘ │
│        │                    │                    │                    │       │
│        │                    │                    │                    │       │
│        │              ┌─────┴─────┐        ┌─────┴─────┐        ┌─────┴─────┐ │
│        │              │  PIL      │        │   JSON    │        │  Fuzzy    │ │
│        │              │  Images   │        │  Response │        │  Matched  │ │
│        │              └───────────┘        └───────────┘        └───────────┘ │
│        │                                                              │       │
│        │                                                              ▼       │
│        │                                                      ┌─────────────┐ │
│        │                                                      │             │ │
│        │                                                      │  Validator  │ │
│        │                                                      │             │ │
│        │                                                      └─────┬───────┘ │
│        │                                                            │         │
│        │                                                      ┌─────┴─────┐   │
│        │                                                      │ Validated │   │
│        │                                                      │ Products  │   │
│        │                                                      │ + Alerts  │   │
│        │                                                      └─────┬─────┘   │
│        │                                                            │         │
│        │              ┌───────────────────────────────────┐         │         │
│        │              │         Checkpoint                │◄────────┤         │
│        │              │    (every 10 pages)               │         │         │
│        │              └───────────────────────────────────┘         │         │
│        │                                                            │         │
│        │                                                            ▼         │
│        │                                                    ┌─────────────┐   │
│        └───────────────────────────────────────────────────►│   Storage   │   │
│                         source_file reference               │ Repository  │   │
│                                                             └──────┬──────┘   │
│                                                                    │          │
└────────────────────────────────────────────────────────────────────┼──────────┘
                                                                     │
                                                                     ▼
                                              ┌──────────────────────────────────┐
                                              │         Output JSON              │
                                              │  data/output/catalog_YYYYMMDD.json│
                                              └──────────────────────────────────┘
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

This project is licensed under the [Creative Commons Attribution-NonCommercial 4.0 International License (CC BY-NC 4.0)](LICENSE).

You are free to share and adapt this work for non-commercial purposes with attribution.
