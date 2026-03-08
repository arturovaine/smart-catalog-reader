# Smart Catalog Reader

An intelligent PDF catalog extraction system that uses **Google Gemini Vision AI** to automatically extract structured product data from cosmetics catalogs.

<p align="center">
  <img src="docs/images/project-cover.png" alt="Smart Catalog Reader - AI-powered product extraction" width="50%">
</p>

## Technical Flow

```
       SMART CATALOG READER | TECHNICAL FLOW
       ====================================

       [ INPUT ]            [ AI ENGINE ]             [ OUTPUT ]
      +-----------+        +--------------------+     +-------------+
      |  PDF File |───────▶| GEMINI VISION AI   |────▶|  JSON DATA  |
      +-----------+        +---------┬----------+     +-------------+
                                     │
                                     ▼
                      ┌───────────────────────────────┐
                      │      EXTRACTION PIPELINE      │
                      └──────────────┬────────────────┘
                                     │
      1. IMAGE PREP   ▶ PDF to high-res images (200 DPI)
                                     │
      2. BATCHING     ▶ Convert 5 pages/batch, parallel API calls
                                     │
      3. AI VISION    ▶ Extract: Code, Name, Price, Promos
                                     │
      4. REFINEMENT   ▶ Fuzzy Match: Normalize Categories
                                     │
      5. VALIDATION   ▶ Auto-Correction & Data Checks
                                     │
      6. CHECKPOINT   ▶ Save progress every 10 pages
                                     │
                                     ▼
                      +-------------------------------+
                      |      DATA SAMPLE (JSON)       |
                      |-------------------------------|
                      | {                             |
                      |   "codigo": "85675",          |
                      |   "nome": "Creme Relaxante",  |
                      |   "preco_regular": 69.90,     |
                      |   "preco_promocional": 55.90, |
                      |   "categoria_normalizada":    |
                      |       "Corpo e Banho"         |
                      | }                             |
                      +-------------------------------+
```

## Overview

This tool processes PDF catalogs from brands like **O Boticário** and **Natura**, converting each page into images and using AI vision to extract:

- **Product details**: code, name, product line, category, volume/weight
- **Pricing**: regular price, promotional price, savings, discount percentage
- **Promotions**: simple discounts, progressive discounts, combos, buy-x-pay-y
- **Features**: vegan, dermatologist tested, sustainability badges, etc.
- **Validation**: automatic data validation with alerts and auto-corrections

The extracted data is normalized, validated, and exported to structured JSON format, ready for integration with e-commerce platforms, analytics systems, or inventory management.

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

### Sample Output

<table>
<tr>
<th>O Boticário</th>
<th>Natura</th>
</tr>
<tr>
<td>

```json
{
  "code": "85675",
  "name": "Creme Relaxante Hidratante Corporal",
  "product_line": "Cuide-se Bem",
  "category": "Hidratação",
  "normalized_category": "Corpo e Banho",
  "volume_weight": "200 g",
  "regular_price": 69.9,
  "promotional_price": 55.9,
  "savings": 14.0,
  "discount_percentage": 20.03,
  "promotion_active": true,
  "promotional_rule": {
    "type": "simple_discount",
    "description": "ECONOMIZE R$ 14,00"
  },
  "features": ["Vegano", "Sensação relaxante"],
  "page": 2
}
```

</td>
<td>

```json
{
  "code": "204459",
  "name": "Desodorante Hidratante Perfumado Luna",
  "product_line": "Natura Luna Nuit",
  "category": "Corpo e Banho",
  "normalized_category": "Corpo e Banho",
  "volume_weight": "300 ml",
  "regular_price": 95.9,
  "promotional_price": 66.9,
  "savings": 29.0,
  "discount_percentage": 30.24,
  "promotion_active": true,
  "promotional_rule": {
    "type": "simple_discount",
    "description": "Economize R$ 29,00"
  },
  "features": ["08 pontos"],
  "page": 9
}
```

</td>
</tr>
</table>

### Full Output Structure

<details>
<summary>Click to expand complete JSON output example</summary>

```json
{
  "metadata": {
    "name": "boticario-c03",
    "brand": "O Boticário",
    "cycle": null,
    "validity_start": null,
    "validity_end": null,
    "total_pages": 197,
    "source_file": "data/catalogs/boticario-c03.pdf",
    "pages_processed": 197,
    "pages_with_errors": [],
    "exported_at": "2026-03-05T21:42:52.364339"
  },
  "global_promotional_rules": [],
  "products": [
    {
      "code": "85675",
      "name": "Creme Relaxante Hidratante Corporal Cuide-se Bem Cereja de Fases",
      "product_line": "Cuide-se Bem",
      "category": "Hidratação",
      "normalized_category": "Corpo e Banho",
      "volume_weight": "200 g",
      "quantity": null,
      "regular_price": 69.9,
      "promotional_price": 55.9,
      "savings": 14.0,
      "discount_percentage": 20.03,
      "promotion_active": true,
      "promotional_rule": {
        "type": "simple_discount",
        "description": "ECONOMIZE R$ 14,00",
        "conditions": {},
        "discount_tiers": {},
        "combo_codes": [],
        "related_pages": []
      },
      "features": [
        "Vegano",
        "Sensação relaxante",
        "Ajuda a aliviar o cansaço"
      ],
      "page": 2,
      "quadrant": "bottom-left",
      "alerts": []
    },
    {
      "code": "85679",
      "name": "Sabonete em Barra Cuide-se Bem Cereja de Fases",
      "product_line": "Cuide-se Bem",
      "category": "Limpeza",
      "normalized_category": "Corpo e Banho",
      "volume_weight": "4 unidades de 80 g cada",
      "quantity": null,
      "regular_price": 36.9,
      "promotional_price": 28.9,
      "savings": 8.0,
      "discount_percentage": 21.68,
      "promotion_active": true,
      "promotional_rule": {
        "type": "simple_discount",
        "description": "ECONOMIZE R$ 8,00",
        "conditions": {},
        "discount_tiers": {},
        "combo_codes": [],
        "related_pages": []
      },
      "features": [
        "Vegano",
        "Limpa sem ressecar"
      ],
      "page": 2,
      "quadrant": "bottom-left",
      "alerts": []
    }
  ],
  "statistics": {
    "total_products": 1638,
    "products_with_promotion": 539,
    "categories": [
      "Outros",
      "Unhas",
      "Maquiagem",
      "Perfumaria",
      "Cabelos",
      "Corpo e Banho"
    ],
    "product_lines": [
      "Beijinho",
      "Intense",
      "Egeo",
      "Escudo de Força e Brilho",
      "BOTI.SUN kids",
      "Skin.q",
      "Boti.Sun"
    ]
  }
}
```

</details>

## Extraction Pipeline (Detailed Flow)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              INPUT: PDF Catalog                                 │
│                          (e.g., boticario-c03.pdf)                              │
└─────────────────────────────────────┬───────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │                         1. PDF PROCESSING                                 │  │
│  │                         ──────────────────                                │  │
│  │   ┌─────────────┐      ┌─────────────┐      ┌─────────────┐               │  │
│  │   │   Page 1    │      │   Page 2    │      │   Page N    │               │  │
│  │   │    PDF      │ ───► │    PDF      │ ───► │    PDF      │               │  │
│  │   └──────┬──────┘      └──────┬──────┘      └──────┬──────┘               │  │
│  │          │                    │                    │                      │  │
│  │          ▼                    ▼                    ▼                      │  │
│  │   ┌─────────────┐      ┌─────────────┐      ┌─────────────┐               │  │
│  │   │   Image 1   │      │   Image 2   │      │   Image N   │               │  │
│  │   │  (PIL/PNG)  │      │  (PIL/PNG)  │      │  (PIL/PNG)  │               │  │
│  │   │  DPI: 200   │      │  DPI: 200   │      │  DPI: 200   │               │  │
│  │   └─────────────┘      └─────────────┘      └─────────────┘               │  │
│  │                                                                           │  │
│  │   Library: pdf2image (poppler)                                            │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────┬───────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │                     2. BATCH PROCESSING (5 pages/batch)                   │  │
│  │                     ───────────────────────────────────                   │  │
│  │                                                                           │  │
│  │   ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐     │  │
│  │   │ Batch 1 │   │ Batch 2 │   │ Batch 3 │   │   ...   │   │ Batch N │     │  │
│  │   │ Pages   │   │ Pages   │   │ Pages   │   │         │   │ Pages   │     │  │
│  │   │  1-5    │   │  6-10   │   │ 11-15   │   │         │   │196-197  │     │  │
│  │   └────┬────┘   └────┬────┘   └────┬────┘   └────┬────┘   └────┬────┘     │  │
│  │        │             │             │             │             │          │  │
│  │        └─────────────┴─────────────┴─────────────┴─────────────┘          │  │
│  │                                    │                                      │  │
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
│  │                                                                           │  │
│  │   ┌──────────────────────────────────────────────────────────────────┐    │  │
│  │   │                     Gemini 2.5 Flash API                         │    │  │
│  │   │  ┌─────────────────────────────────────────────────────────────┐ │    │  │
│  │   │  │  PROMPT:                                                    │ │    │  │
│  │   │  │  - Extract product code, name, line, category               │ │    │  │
│  │   │  │  - Extract regular_price, promotional_price                 │ │    │  │
│  │   │  │  - Identify promotion type (simple, progressive, combo)     │ │    │  │
│  │   │  │  - Extract features (vegan, dermatologist tested, etc.)     │ │    │  │
│  │   │  │  - Detect page type (products, advertising, index)          │ │    │  │
│  │   │  └─────────────────────────────────────────────────────────────┘ │    │  │
│  │   │                              │                                   │    │  │
│  │   │                              ▼                                   │    │  │
│  │   │  ┌─────────────────────────────────────────────────────────────┐ │    │  │
│  │   │  │  OUTPUT: JSON with products[]                               │ │    │  │
│  │   │  │  {                                                          │ │    │  │
│  │   │  │    "produtos": [...],                                       │ │    │  │
│  │   │  │    "regras_promocionais_globais": [...],                    │ │    │  │
│  │   │  │    "tipo_pagina": "products"                                │ │    │  │
│  │   │  │  }                                                          │ │    │  │
│  │   │  └─────────────────────────────────────────────────────────────┘ │    │  │
│  │   └──────────────────────────────────────────────────────────────────┘    │  │
│  │                                                                           │  │
│  │   Retry Logic: Exponential backoff (tenacity) for rate limits             │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────┬───────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │                      4. CATEGORY NORMALIZATION                            │  │
│  │                      ─────────────────────────                            │  │
│  │                                                                           │  │
│  │   Raw Category              Fuzzy Match (thefuzz)         Normalized      │  │
│  │   ─────────────             ────────────────────          ──────────      │  │
│  │   "Hidratação"        ───►  score: 85  ───────────►  "Corpo e Banho"      │  │
│  │   "Perfume Feminino"  ───►  score: 90  ───────────►  "Perfumaria"         │  │
│  │   "Batom"             ───►  score: 88  ───────────►  "Maquiagem"          │  │
│  │   "Shampoo"           ───►  score: 92  ───────────►  "Cabelos"            │  │
│  │   "Desconhecido"      ───►  score: 45  ───────────►  "Outros"             │  │
│  │                                                                           │  │
│  │   Master Categories: Perfumaria, Maquiagem, Corpo e Banho, Cabelos,       │  │
│  │                      Skincare, Infantil, Masculino, Unhas, Acessórios,    │  │
│  │                      Kits e Presentes, Proteção Solar, Desodorantes       │  │
│  │                                                                           │  │
│  │   Threshold: 75 (configurable)                                            │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────┬───────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │                    5. VALIDATION & AUTO-CORRECTION                        │  │
│  │                    ───────────────────────────────                        │  │
│  │                                                                           │  │
│  │   ┌─────────────────────────────────────────────────────────────────┐     │  │
│  │   │  VALIDATION RULES:                                              │     │  │
│  │   │  ├── Code: 4-6 digits, alphanumeric                             │     │  │
│  │   │  ├── Name: min 3 chars, no suspicious characters                │     │  │
│  │   │  ├── Price: range 0.01 - 10,000 BRL                             │     │  │
│  │   │  ├── Discount: max 80%                                          │     │  │
│  │   │  ├── Promotional consistency: flags match prices                │     │  │
│  │   │  └── Duplicate detection: unique product codes                  │     │  │
│  │   └─────────────────────────────────────────────────────────────────┘     │  │
│  │                                                                           │  │
│  │   ┌─────────────────────────────────────────────────────────────────┐     │  │
│  │   │  AUTO-CORRECTIONS:                                              │     │  │
│  │   │  ├── Swap prices if promotional > regular                       │     │  │
│  │   │  ├── Calculate savings if missing                               │     │  │
│  │   │  ├── Set promotion_active flag if promo price exists            │     │  │
│  │   │  └── Normalize category if missing                              │     │  │
│  │   └─────────────────────────────────────────────────────────────────┘     │  │
│  │                                                                           │  │
│  │   Alerts: ERROR (critical) │ WARNING (review) │ INFO (informational)      │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────┬───────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │                       6. CHECKPOINTING (every 10 pages)                   │  │
│  │                       ─────────────────────────────────                   │  │
│  │                                                                           │  │
│  │   .checkpoints/                                                           │  │
│  │   └── boticario-c03.checkpoint.json                                       │  │
│  │       {                                                                   │  │
│  │         "catalog": { ... },            ◄── Full catalog state             │  │
│  │         "last_processed_page": 110,    ◄── Resume point                   │  │
│  │         "checkpoint_time": "..."       ◄── Timestamp                      │  │
│  │       }                                                                   │  │
│  │                                                                           │  │
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
│  │                                                                           │  │
│  │   data/output/boticario-c03_20260305_214252.json                          │  │
│  │   ┌─────────────────────────────────────────────────────────────────┐     │  │
│  │   │  {                                                              │     │  │
│  │   │    "metadata": {                                                │     │  │
│  │   │      "name": "boticario-c03",                                   │     │  │
│  │   │      "brand": "O Boticário",                                    │     │  │
│  │   │      "total_pages": 197,                                        │     │  │
│  │   │      "pages_processed": 197                                     │     │  │
│  │   │    },                                                           │     │  │
│  │   │    "global_promotional_rules": [...],                           │     │  │
│  │   │    "products": [ 1638 products ],                               │     │  │
│  │   │    "statistics": {                                              │     │  │
│  │   │      "total_products": 1638,                                    │     │  │
│  │   │      "products_with_promotion": 1200,                           │     │  │
│  │   │      "categories": ["Maquiagem", "Corpo e Banho", ...]          │     │  │
│  │   │    }                                                            │     │  │
│  │   │  }                                                              │     │  │
│  │   └─────────────────────────────────────────────────────────────────┘     │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Clean Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                                                                 │
│   ┌──────────────────────────────────────────────────────────────────────────┐  │
│   │                           PRESENTATION LAYER                             │  │
│   │                                                                          │  │
│   │   ┌─────────────────────────────────────────────────────────────────┐    │  │
│   │   │                      CLI (Typer + Rich)                         │    │  │
│   │   │                       main.py                                   │    │  │
│   │   │  ┌──────────┐  ┌──────────┐  ┌───────────┐  ┌──────────┐        │    │  │
│   │   │  │ extract  │  │ validate │  │   list    │  │   info   │        │    │  │
│   │   │  │ command  │  │ command  │  │  command  │  │ command  │        │    │  │
│   │   │  └──────────┘  └──────────┘  └───────────┘  └──────────┘        │    │  │
│   │   │                      │                                          │    │  │
│   │   │                      ▼                                          │    │  │
│   │   │            Progress Bar │ Tables │ Console Output               │    │  │
│   │   └─────────────────────────────────────────────────────────────────┘    │  │
│   └──────────────────────────────────────────────────────────────────────────┘  │
│                                       │                                         │
│                                       ▼                                         │
│   ┌──────────────────────────────────────────────────────────────────────────┐  │
│   │                      DEPENDENCY INJECTION LAYER                          │  │
│   │                                                                          │  │
│   │   ┌─────────────────────────────────────────────────────────────────┐    │  │
│   │   │            DI Container (dependency-injector)                   │    │  │
│   │   │                      container.py                               │    │  │
│   │   │                                                                 │    │  │
│   │   │   Settings ─────┬──────────────────────────────────────────┐    │    │  │
│   │   │                 │                                          │    │    │  │
│   │   │   Providers:    │                                          │    │    │  │
│   │   │   ├── pdf_processor ──► Singleton                          │    │    │  │
│   │   │   ├── llm_client ─────► Singleton                          │    │    │  │
│   │   │   ├── normalizer ─────► Singleton                          │    │    │  │
│   │   │   ├── validator ──────► Singleton                          │    │    │  │
│   │   │   ├── storage ────────► Singleton                          │    │    │  │
│   │   │   └── extraction_service ► Factory                         │    │    │  │
│   │   └─────────────────────────────────────────────────────────────────┘    │  │
│   └──────────────────────────────────────────────────────────────────────────┘  │
│                                       │                                         │
│                                       ▼                                         │
│   ┌──────────────────────────────────────────────────────────────────────────┐  │
│   │                         APPLICATION LAYER                                │  │
│   │                        (Use Cases / Services)                            │  │
│   │                                                                          │  │
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
│   │                    │                                                     │  │
│   │      Orchestrates: │                                                     │  │
│   │      PDF ──► LLM ──► Normalize ──► Validate ──► Store                    │  │
│   └──────────────────────────────────────────────────────────────────────────┘  │
│                                       │                                         │
│                                       ▼                                         │
│   ┌──────────────────────────────────────────────────────────────────────────┐  │
│   │                           DOMAIN LAYER                                   │  │
│   │                     (Entities / Interfaces / Ports)                      │  │
│   │                                                                          │  │
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
│                                       │                                         │
│                                       ▼                                         │
│   ┌──────────────────────────────────────────────────────────────────────────┐  │
│   │                       INFRASTRUCTURE LAYER                               │  │
│   │                    (Concrete Implementations / Adapters)                 │  │
│   │                                                                          │  │
│   │   ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐       │  │
│   │   │PDF2ImageProcessor│  │   GeminiClient   │  │FuzzyCategoryNorm.│       │  │
│   │   │ pdf_processor.py │  │   llm_client.py  │  │  normalizer.py   │       │  │
│   │   │                  │  │                  │  │                  │       │  │
│   │   │ Implements:      │  │ Implements:      │  │ Implements:      │       │  │
│   │   │ PDFProcessor     │  │ LLMClient        │  │ CategoryNormalizer       │  │
│   │   │                  │  │                  │  │                  │       │  │
│   │   │ Uses:            │  │ Uses:            │  │ Uses:            │       │  │
│   │   │ - pdf2image      │  │ - google-genai   │  │ - thefuzz        │       │  │
│   │   │ - Pillow         │  │ - tenacity       │  │ - rapidfuzz      │       │  │
│   │   └──────────────────┘  └──────────────────┘  └──────────────────┘       │  │
│   │                                                                          │  │
│   │   ┌──────────────────────────────────────────────────────────────┐       │  │
│   │   │               JSONStorageRepository                          │       │  │
│   │   │                    storage.py                                │       │  │
│   │   │                                                              │       │  │
│   │   │   Implements: StorageRepository                              │       │  │
│   │   │                                                              │       │  │
│   │   │   Methods:                                                   │       │  │
│   │   │   ├── save_catalog()        - Save to JSON                   │       │  │
│   │   │   ├── load_catalog()        - Load from JSON                 │       │  │
│   │   │   ├── save_checkpoint()     - Save progress                  │       │  │
│   │   │   ├── load_checkpoint()     - Resume progress                │       │  │
│   │   │   ├── delete_checkpoint()   - Cleanup                        │       │  │
│   │   │   └── list_catalogs()       - List PDFs                      │       │  │
│   │   └──────────────────────────────────────────────────────────────┘       │  │
│   └──────────────────────────────────────────────────────────────────────────┘  │
│                                                                                 │
│   ┌──────────────────────────────────────────────────────────────────────────┐  │
│   │                        EXTERNAL DEPENDENCIES                             │  │
│   │                                                                          │  │
│   │     ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐                │  │
│   │     │ Gemini  │   │ Poppler │   │  JSON   │   │  File   │                │  │
│   │     │   API   │   │  (PDF)  │   │  Files  │   │ System  │                │  │
│   │     └─────────┘   └─────────┘   └─────────┘   └─────────┘                │  │
│   └──────────────────────────────────────────────────────────────────────────┘  │
│                                                                                 │
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
│                                                                                │
│  ┌─────────────┐      ┌─────────────┐      ┌─────────────┐      ┌───────────┐  │
│  │             │      │             │      │             │      │           │  │
│  │  PDF File   │─────►│ PDF2Image   │─────►│   Gemini    │─────►│ Normalizer│  │
│  │  (Input)    │      │  Processor  │      │   Client    │      │           │  │
│  │             │      │             │      │             │      │           │  │
│  └─────────────┘      └─────────────┘      └─────────────┘      └─────┬─────┘  │
│        │                    │                    │                    │        │
│        │                    │                    │                    │        │
│        │              ┌─────┴─────┐        ┌─────┴─────┐        ┌─────┴─────┐  │
│        │              │  PIL      │        │   JSON    │        │  Fuzzy    │  │
│        │              │  Images   │        │  Response │        │  Matched  │  │
│        │              └───────────┘        └───────────┘        └───────────┘  │
│        │                                                              │        │
│        │                                                              ▼        │
│        │                                                      ┌─────────────┐  │
│        │                                                      │             │  │
│        │                                                      │  Validator  │  │
│        │                                                      │             │  │
│        │                                                      └─────┬───────┘  │
│        │                                                            │          │
│        │                                                      ┌─────┴─────┐    │
│        │                                                      │ Validated │    │
│        │                                                      │ Products  │    │
│        │                                                      │ + Alerts  │    │
│        │                                                      └─────┬─────┘    │
│        │                                                            │          │
│        │              ┌───────────────────────────────────┐         │          │
│        │              │         Checkpoint                │◄────────┤          │
│        │              │    (every 10 pages)               │         │          │
│        │              └───────────────────────────────────┘         │          │
│        │                                                            │          │
│        │                                                            ▼          │
│        │                                                    ┌─────────────┐    │
│        └───────────────────────────────────────────────────►│   Storage   │    │
│                         source_file reference               │ Repository  │    │
│                                                             └──────┬──────┘    │
│                                                                    │           │
└────────────────────────────────────────────────────────────────────┼─────────-─┘
                                                                     │
                                                                     ▼
                                              ┌────────────────────────────────────┐
                                              │         Output JSON                │
                                              │  data/output/catalog_YYYYMMDD.json │
                                              └────────────────────────────────────┘
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
