# Boticário & Natura Catalog Data Analysis Guide

> Comprehensive analysis framework for cosmetics retail data extracted from O Boticário and Natura sales catalogs.

---

## Table of Contents

1. [Dataset Overview](#dataset-overview)
2. [Data Schema](#data-schema)
3. [Analysis Categories](#analysis-categories)
   - [Pricing & Promotions Analysis](#1-pricing--promotions-analysis)
   - [Category & Product Line Analysis](#2-category--product-line-analysis)
   - [Promotional Strategy Analysis](#3-promotional-strategy-analysis)
   - [Data Quality Analysis](#4-data-quality-analysis)
   - [Advanced Analytics](#5-advanced-analytics)
4. [Notebook Structure](#notebook-structure)
5. [Key Metrics & KPIs](#key-metrics--kpis)
6. [Visualization Recommendations](#visualization-recommendations)

---

## Dataset Overview

| Attribute | Value |
|-----------|-------|
| **Brands** | O Boticário, Natura |
| **Total Catalogs** | 33 PDF files |
| **Total Products** | 40,000+ extracted records |
| **Cycles Covered** | 17 cycles (O Boticário), 16 cycles (Natura) |
| **Data Volume** | ~2.4 GB raw PDFs |
| **Extraction Method** | Google Gemini Vision AI |

### Data Sources

```
data/output/
├── boticario_ciclo_01_YYYYMMDD_HHMMSS.json
├── boticario_ciclo_02_YYYYMMDD_HHMMSS.json
├── ...
├── natura_ciclo_03_YYYYMMDD_HHMMSS.json
├── natura_ciclo_04_YYYYMMDD_HHMMSS.json
└── ...
```

---

## Data Schema

### Product Entity

| Field | Type | Description |
|-------|------|-------------|
| `codigo` | string | Product SKU (4-6 digits) |
| `nome` | string | Product name |
| `linha` | string | Product line (e.g., "Nativa SPA", "Cuide-se Bem") |
| `categoria` | string | Raw category from extraction |
| `categoria_normalizada` | string | Standardized category |
| `volume_peso` | string | Volume/weight (e.g., "200ml", "400g") |
| `quantidade` | string | Quantity in pack |
| `preco_regular` | float | Regular price (BRL) |
| `preco_promocional` | float | Promotional price (BRL) |
| `economia` | float | Savings amount (BRL) |
| `desconto_percentual` | float | Discount percentage |
| `promocao_ativa` | boolean | Promotion active flag |
| `regra_promocional` | object | Promotional rule details |
| `caracteristicas` | array | Features (e.g., ["Vegano", "Dermatologicamente Testado"]) |
| `pagina` | integer | Page number in catalog |
| `quadrante` | string | Position on page |
| `alertas` | array | Validation alerts |

### Promotional Rule Types

| Type | Description |
|------|-------------|
| `none` | No promotion |
| `simple_discount` | Fixed percentage or value discount |
| `progressive_discount` | Tiered discounts (buy more, save more) |
| `combo` | Bundle with other products |
| `buy_x_pay_y` | Buy X units, pay for Y |
| `pack` | Multi-unit pack pricing |

### Normalized Categories

| Category | Examples |
|----------|----------|
| Perfumaria | Fragrances, eau de parfum, body spray |
| Maquiagem | Lipstick, foundation, blush, mascara |
| Corpo e Banho | Body lotion, shower gel, soap |
| Cabelos | Shampoo, conditioner, hair masks |
| Skincare | Facial care, anti-aging, serums |
| Infantil | Children's products |
| Masculino | Men's line |
| Unhas | Nail care |
| Acessórios | Accessories |
| Kits e Presentes | Gift sets |
| Proteção Solar | Sunscreen |
| Desodorantes | Deodorants |

---

## Analysis Categories

### 1. Pricing & Promotions Analysis

#### 1.1 Discount Distribution Analysis

**Objective:** Understand the distribution and patterns of discounts across the product portfolio.

**Key Questions:**
- What is the average discount percentage by category?
- How do discounts vary between brands?
- What are the most common discount ranges?

**Metrics:**
- Mean, median, std of `desconto_percentual`
- Discount frequency by range (0-10%, 10-20%, 20-30%, etc.)
- Outlier detection (discounts > 50%)

**Visualizations:**
- Histogram of discount percentages
- Box plots by category
- Violin plots comparing brands

#### 1.2 Price Range Analysis

**Objective:** Segment products by price tiers and understand pricing strategy.

**Key Questions:**
- What are the natural price clusters?
- How does pricing differ by category?
- What is the price premium for certain product lines?

**Metrics:**
- Price percentiles (P25, P50, P75, P90)
- Price range by category
- Regular vs promotional price ratio

**Visualizations:**
- Price distribution histograms
- Category-wise price box plots
- Scatter plot: regular vs promotional prices

#### 1.3 Savings Analysis

**Objective:** Quantify monetary savings offered to consumers.

**Key Questions:**
- What is the total potential savings per catalog?
- Which categories offer highest absolute savings?
- Correlation between price and savings amount?

**Metrics:**
- Total `economia` by catalog/cycle
- Average savings by category
- Savings as percentage of regular price

---

### 2. Category & Product Line Analysis

#### 2.1 Category Distribution

**Objective:** Map the product portfolio composition.

**Key Questions:**
- How many products per category?
- Which categories dominate each brand?
- Category evolution across cycles?

**Metrics:**
- Product count per `categoria_normalizada`
- Category share percentage
- Category growth rate across cycles

**Visualizations:**
- Pie/donut charts for category share
- Stacked bar charts by brand
- Treemap visualization

#### 2.2 Product Line Analysis

**Objective:** Identify key product lines and their characteristics.

**Key Questions:**
- What are the top 20 product lines?
- Which lines have most promotions?
- Average price point by product line?

**Metrics:**
- Product count per `linha`
- Promotion rate by line
- Average `preco_regular` by line

**Visualizations:**
- Horizontal bar chart of top lines
- Bubble chart (size=count, color=avg_price)

#### 2.3 Volume/Weight Analysis

**Objective:** Understand product sizing patterns.

**Key Questions:**
- What are standard sizes by category?
- Price per ml/g analysis?
- Size vs discount correlation?

**Metrics:**
- Extract numeric volume from `volume_peso`
- Calculate price per unit (ml/g)
- Mode sizes by category

**Visualizations:**
- Distribution of volumes by category
- Scatter: volume vs price
- Box plots of size ranges

#### 2.4 Brand Comparison

**Objective:** Compare O Boticário vs Natura portfolios.

**Key Questions:**
- Portfolio size comparison?
- Pricing strategy differences?
- Promotion intensity differences?

**Metrics:**
- Total products per brand
- Average prices per brand/category
- Promotion rates per brand

**Visualizations:**
- Side-by-side comparisons
- Radar charts for multi-dimensional comparison

---

### 3. Promotional Strategy Analysis

#### 3.1 Promotion Type Distribution

**Objective:** Understand which promotional mechanics are used most.

**Key Questions:**
- Distribution of `regra_promocional.type`?
- Do certain categories favor specific promotion types?
- Brand differences in promotion strategies?

**Metrics:**
- Count by promotion type
- Cross-tabulation: category x promotion type
- Brand-wise promotion type distribution

**Visualizations:**
- Stacked bar charts
- Heatmaps for category x promotion type

#### 3.2 Progressive Discount Analysis

**Objective:** Deep dive into tiered discount structures.

**Key Questions:**
- What are common tier structures?
- Maximum discount achievable?
- Which categories use progressive discounts?

**Metrics:**
- Parse `discount_tiers` structure
- Count tier configurations (2-tier, 3-tier, etc.)
- Max discount per tier structure

**Visualizations:**
- Tier structure frequency
- Line plots showing discount progression

#### 3.3 Combo Analysis

**Objective:** Identify product bundling patterns.

**Key Questions:**
- Which products are commonly bundled?
- Cross-category combos?
- Combo pricing vs individual pricing?

**Metrics:**
- Extract `combo_codes` relationships
- Build product co-occurrence matrix
- Calculate combo discount vs sum of individual prices

**Visualizations:**
- Network graph of combo relationships
- Heatmap of category co-occurrences

#### 3.4 Promotion Density Over Time

**Objective:** Track promotional intensity across sales cycles.

**Key Questions:**
- Does promotion rate increase/decrease over cycles?
- Seasonal patterns in promotions?
- Category-specific seasonality?

**Metrics:**
- `products_with_promotion / total_products` per cycle
- Monthly/cycle trend analysis
- Category promotion rate over time

**Visualizations:**
- Line chart of promotion rate by cycle
- Heatmap: category x cycle promotion intensity

---

### 4. Data Quality Analysis

#### 4.1 Validation Alert Analysis

**Objective:** Assess extraction quality and common issues.

**Key Questions:**
- What are most common validation issues?
- Error rate by field?
- Quality trends across catalogs?

**Metrics:**
- Count by `alertas.level` (info, warning, error)
- Frequency by `alertas.field`
- Error rate per catalog

**Visualizations:**
- Bar chart of alert types
- Pareto chart for field issues
- Trend line of error rates

#### 4.2 Auto-correction Analysis

**Objective:** Understand data cleaning patterns.

**Key Questions:**
- What corrections are most common?
- Original vs corrected value comparison?
- Correction success rate?

**Metrics:**
- Count corrections by type
- `original_value` vs `corrected_value` comparison
- Percentage of products with corrections

**Visualizations:**
- Sankey diagram of corrections
- Before/after distributions

#### 4.3 Missing Data Analysis

**Objective:** Identify gaps in extracted data.

**Key Questions:**
- Which fields have highest null rates?
- Missing data patterns by category?
- Impact on analysis?

**Metrics:**
- Null percentage per field
- Missing data correlation matrix
- Complete case percentage

**Visualizations:**
- Missing data heatmap
- Bar chart of null rates

#### 4.4 Category Normalization Quality

**Objective:** Evaluate fuzzy matching effectiveness.

**Key Questions:**
- Raw to normalized mapping accuracy?
- Uncategorized products?
- Ambiguous mappings?

**Metrics:**
- Unique raw categories vs normalized
- "Outros" category percentage
- Low-confidence mappings

**Visualizations:**
- Alluvial diagram: raw → normalized
- Distribution of matching scores

---

### 5. Advanced Analytics

#### 5.1 Price Clustering

**Objective:** Identify natural product tiers using unsupervised learning.

**Method:** K-Means clustering on price features

**Features:**
- `preco_regular`
- `preco_promocional` (imputed if null)
- `desconto_percentual`
- Volume (numeric)

**Expected Output:**
- 3-5 product tiers (Economy, Standard, Premium, Luxury)
- Cluster profiles with characteristics
- Silhouette score for validation

**Visualizations:**
- Scatter plot with cluster colors
- Elbow plot for optimal K
- Radar chart of cluster profiles

#### 5.2 NLP Analysis on Product Names

**Objective:** Extract insights from product naming patterns.

**Techniques:**
- Tokenization and word frequency
- TF-IDF for important terms
- Named entity extraction (scents, ingredients)

**Insights:**
- Most common ingredients mentioned
- Scent family identification (floral, citrus, woody)
- Benefit keywords (hidratante, nutritivo, anti-idade)

**Visualizations:**
- Word clouds by category
- Bar charts of top terms
- Topic modeling visualization

#### 5.3 Product Similarity & Recommendations

**Objective:** Build content-based recommendation engine.

**Approach:**
1. Feature engineering (category, line, price tier, features)
2. TF-IDF on product names
3. Cosine similarity matrix
4. K-nearest neighbors for recommendations

**Use Cases:**
- "Similar products" suggestions
- Substitute finder (same category, similar price)
- Cross-sell opportunities

**Visualizations:**
- Similarity heatmap (sample)
- t-SNE/UMAP for product embedding visualization

#### 5.4 Market Basket Analysis

**Objective:** Identify products frequently appearing together.

**Method:**
- Use page co-occurrence as proxy for association
- Apply Apriori algorithm for frequent itemsets
- Calculate support, confidence, lift

**Insights:**
- Product association rules
- Category co-occurrence patterns
- Bundle optimization suggestions

**Visualizations:**
- Network graph of associations
- Heatmap of lift values

#### 5.5 Time Series Analysis

**Objective:** Detect trends and patterns across sales cycles.

**Analyses:**
- Price trends by category
- Promotion intensity trends
- New product introductions
- Product lifecycle stages

**Methods:**
- Moving averages
- Seasonal decomposition
- Trend detection

**Visualizations:**
- Multi-line time series plots
- Seasonal pattern charts

---

## Notebook Structure

### Recommended Kaggle Notebook Organization

```
📓 boticario_natura_analysis.ipynb
│
├── 1. Setup & Configuration
│   ├── Import libraries
│   ├── Configure plotting style
│   └── Define helper functions
│
├── 2. Data Loading
│   ├── Load all JSON files
│   ├── Concatenate into master DataFrame
│   └── Initial data inspection
│
├── 3. Data Preprocessing
│   ├── Parse volume/weight
│   ├── Handle missing values
│   ├── Feature engineering
│   └── Data type conversions
│
├── 4. Exploratory Data Analysis (EDA)
│   ├── Dataset overview
│   ├── Univariate analysis
│   ├── Bivariate analysis
│   └── Correlation analysis
│
├── 5. Pricing & Promotions Analysis
│   ├── Discount distribution
│   ├── Price analysis
│   └── Savings analysis
│
├── 6. Category & Product Analysis
│   ├── Category distribution
│   ├── Product line analysis
│   ├── Volume analysis
│   └── Brand comparison
│
├── 7. Promotional Strategy Analysis
│   ├── Promotion type analysis
│   ├── Progressive discounts
│   ├── Combo analysis
│   └── Temporal patterns
│
├── 8. Data Quality Analysis
│   ├── Validation alerts
│   ├── Missing data
│   └── Normalization quality
│
├── 9. Advanced Analytics
│   ├── Price clustering
│   ├── NLP analysis
│   ├── Recommendations
│   └── Market basket
│
└── 10. Conclusions & Insights
    ├── Key findings
    ├── Business recommendations
    └── Future work
```

---

## Key Metrics & KPIs

### Business Metrics

| Metric | Formula | Description |
|--------|---------|-------------|
| **Promotion Rate** | `products_with_promotion / total_products` | % of products on sale |
| **Average Discount** | `mean(desconto_percentual)` | Typical discount offered |
| **Category Concentration** | `top_3_categories_count / total_products` | Portfolio concentration |
| **Price Premium** | `brand_avg_price / market_avg_price` | Brand positioning |
| **Savings Intensity** | `sum(economia) / sum(preco_regular)` | Total value given back |

### Data Quality Metrics

| Metric | Formula | Description |
|--------|---------|-------------|
| **Extraction Accuracy** | `1 - (error_alerts / total_products)` | Data quality score |
| **Completeness** | `1 - (missing_values / total_fields)` | Data completeness |
| **Category Coverage** | `categorized_products / total_products` | Normalization success |

---

## Visualization Recommendations

### Recommended Libraries

```python
# Core
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go

# Specialized
from wordcloud import WordCloud
import networkx as nx
```

### Color Palettes

```python
# Brand colors
BOTICARIO_COLORS = ['#006847', '#00A859', '#7DC242']  # Green tones
NATURA_COLORS = ['#F57C00', '#FF9800', '#FFB74D']     # Orange tones

# Category palette
CATEGORY_PALETTE = 'Set2'  # Seaborn palette

# Sequential for metrics
METRIC_PALETTE = 'YlOrRd'  # Yellow-Orange-Red
```

### Plot Styling

```python
# Kaggle-friendly settings
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['figure.figsize'] = (12, 6)
plt.rcParams['font.size'] = 11
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['axes.labelsize'] = 12
```

---

## Getting Started

### Prerequisites

```bash
pip install pandas numpy matplotlib seaborn plotly
pip install scikit-learn scipy
pip install wordcloud networkx
pip install mlxtend  # For association rules
```

### Quick Start

```python
import pandas as pd
import json
from pathlib import Path

# Load all catalog data
data_dir = Path('data/output')
all_products = []

for json_file in data_dir.glob('*.json'):
    with open(json_file) as f:
        catalog = json.load(f)
        for product in catalog['products']:
            product['source_file'] = json_file.name
            product['brand'] = 'boticario' if 'boticario' in json_file.name else 'natura'
            all_products.append(product)

df = pd.DataFrame(all_products)
print(f"Loaded {len(df)} products from {len(list(data_dir.glob('*.json')))} catalogs")
```

---

## Contributing

For improvements or additional analyses, please refer to the main project repository.

## License

This analysis framework is part of the Smart Catalog Reader project.
