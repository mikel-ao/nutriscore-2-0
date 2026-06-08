# Nutriscore 2.0: Towards More Transparent Food Labelling

> **Continuation of:** [Exploratory Data Analysis - Nutriscore is Incomplete and Manipulable](https://github.com/mikel-ao/food-labelling-audit.git)
>
> **Presentation:** [Canva](https://canva.link/m8gp6zmxdfyloks)
>
> **Prototype:** [Nutriscore 2.0](https://nutriscore2-0.streamlit.app/)

## 📋 Executive Summary

This unsupervised ML project is the **evolution of the prior exploratory analysis** that concluded the **classic Nutri-Score** (based solely on nutrients) is incomplete and manipulable. A product can hold a Nutri-Score A while being ultra-processed and packed with chemical additives. Nutriscore 2.0 addresses this by combining 3 dimensions:

- **Nutrients** (Nutriscore 1–5)
- **Processing** (NOVA 1–4)
- **Additives** (Safety Index based on PubMed)

**Result:** 4 clear categories + additive risk information

---

## 🎯 Problem Context

### Why Nutriscore 2.0?

In 2026, **millions of food products** circulate in European markets, yet consumers only have **ONE global labelling system**: Nutri-Score. However:

| Limitation | Impact |
|-----------|--------|
| Only analyses **nutrients** | Ignores whether the product is ultra-processed |
| Does not consider **chemical additives** | A "Nutriscore A" product can contain 651 permitted but risky additives |
| Susceptible to **formulation optimisation** | Companies can improve the score without improving actual health impact |

---

## 📊 Data

- **836,897 food products** from Open Food Facts
- **651 additives** classified using PubMed (10,400+ searches)
- **4 clusters** validated with K-Means + Hierarchical Clustering

---

## 🔬 Methodology

**Step 1: Classify Additives (SSI)**
- PubMed API: 651 additives × 16 keywords
- Filters: semantic negations, weighting by study type
- Validation against EFSA (if withdrawn → AVOIDABLE)

**Step 2: Food Clustering (K-Means)**
- Features: Nutriscore + NOVA + Total additives
- K=4 validated by: Elbow, Silhouette, Hierarchical Clustering

**Step 3: Final Mapping**
- Each food item = Cluster + Dominant additive risk
- 12 total categories (4 clusters × 3 risk levels)

---

![Elbow Plot](outputs/plots/food_products/metodo_codo_alimentos2.png)
![Silhouette Score](outputs/plots/food_products/silhouette_4_clusters2.png)
![Dendrogram Validation](outputs/plots/food_products/dendrograma_ward_validacion.png)

**Conclusion:** K=4 validated by two independent methods → **ROBUST**.

---

## 📈 Results: The 4 Clusters

### Cluster Profile Matrix

![Cluster Profile Matrix](outputs/plots/food_products/matriz2.png)

### Detailed Profile per Cluster

| Cluster | Profile | Risk | % |
|---------|---------|------|---|
| **0** | Deceptive Industrial Design | | |
| **1** | Ultra-Processed with High Additive Load | | |
| **2** | Natural Base | | |
| **3** | Processed/Ultra-Processed with Low Nutritional Profile | | |

---

### 3D Visualisation

![3D Cluster Scatter Plot](outputs/plots/food_products/dispersion.png)

**Interpretation:**
- Each point = 1 food product (836k points)
- X = Nutriscore (1–5), Y = NOVA (1–4), Z = Total additives (0–20+)
- Colours = K-Means clusters
- Clear and natural separation between groups

**Code:** `notebooks/03_visualizacion_resultados.ipynb`

---

![Nutriscore 2.0 Concept](outputs/plots/food_products/A.png)
![Nutriscore 2.0 Concept](outputs/plots/food_products/2.png)

---

## 📁 Project Structure

```
Directory structure:
└── mikel-ao-aditive_info/
    ├── README.md
    ├── requirements.txt
    ├── outputs/
    │   ├── report/
    │   ├── plots/
    │   └── presentation/
    └── src/
        ├── data/
        │   ├── maestro_aditivos_limpio.csv
        │   ├── maestro_aditivos_raw.csv
        │   ├── ssi/                              --> Additive classification process
        │   └── alimentos_con_semaforo_final.csv  --> Final classification for model training
        ├── models/
        │   ├── scaler_alimentos.pkl
        │   └── kmeans_alimentos.pkl
        ├── notebooks/
        │   ├── 01_extraccion_dataset_aditivos.ipynb
        │   ├── 02_clasificacion_aditivos.ipynb
        │   ├── 03_extraccion_dataset_alimentos.ipynb
        │   ├── 04_fusion_aditivos_alimentos.ipynb
        │   └── 05_clasificacion_final.ipynb
        ├── resources/
        │   └── streamlit/
        │       ├── app.py
        │       ├── pipeline.py
        │       └── requirements.txt
        └── utils/
            ├── __init__.py
            ├── ESTRUCTURA_PROYECTO.txt
            ├── pipeline_maestro.py
            ├── run_pipeline_v2.sh
            └── verificar_barcode_entrenamiento.py  --> Verifies whether the model is predicting or classifying an already-trained sample.
```

---

## 🚀 How to Run the Project

### Prerequisites

- **Python 3.9+**
- **Jupyter Notebook** or **JupyterLab**
- Internet connection (for PubMed API)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/tu-usuario/nutriscore-2.0.git
cd nutriscore-2.0

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
cp .env.example .env
# Edit .env with your PubMed credentials
```

### Required Environment Variables

```bash
# .env
NCBI_EMAIL="your_email@example.com"
NCBI_API_KEY="your_pubmed_api_key"
NOMBRE_HERRAMIENTA="NutriscorePyProject"
```

**Getting a PubMed API key:**
1. Register at [NCBI Account](https://www.ncbi.nlm.nih.gov/account/)
2. Generate an API key under "Account Settings"
3. Paste it into `.env`

### Logical Pipeline (Important to Understand)

```
STAGE 1: Classify Additives (SSI)
├─ Input: 651 additives + PubMed
├─ Output: aditivos_ssi.csv (651 rows)
│   └─ Columns: [E_code, name, SSI_score, SSI_category]
│      └─ SSI_category: SAFE (73%) | CAUTION (13%) | AVOIDABLE (14%)
└─ Note: WITHOUT this, there is no additive risk data

STAGE 2: Food Clustering (K-Means)
├─ Input: 836k food products + 3 features (Nutriscore, NOVA, total_additives)
├─ Output: alimentos_clustering.csv (836k rows)
│   └─ Columns: [product_id, cluster (0–3), ...]
└─ Note: Independent of SSI (pure clustering)

STAGE 3: Map Additives to Food Products
├─ Input:
│   ├─ alimentos_clustering.csv (assigned cluster)
│   ├─ aditivos_ssi.csv (SSI per E_code)
│   └─ additives_tags for each product
├─ Output: nutriscore_2_0_final.csv (836k rows, 12 categories)
│   └─ Columns: [cluster, dominant_risk, final_category]
└─ Algorithm: For each food product:
   1. Read additives_tags → ["E100", "E101", "E102"]
   2. Look up SSI for each → [SAFE, CAUTION, SAFE]
   3. Winner = MAX(risks) → CAUTION
   4. Category = f"{cluster}_{final_risk}" → "0_CAUTION"
```

---

## 📚 Data Sources

### APIs and Datasets Used

| Source | Description | URL | Documentation |
|--------|-------------|-----|---------------|
| **Open Food Facts** | Food product database | `https://world.openfoodfacts.org` | [Docs](https://world.openfoodfacts.org/data) |
| **Open Food Facts API - Additives** | Taxonomy of 651 EU-permitted additives | `https://world.openfoodfacts.org/data/taxonomies/additives.json` | [JSON](https://world.openfoodfacts.org/data) |
| **Open Food Facts - Parquet Dataset** | 836k+ products with nutritional metadata | `https://huggingface.co/datasets/openfoodfacts/product-database/resolve/main/food.parquet?download=true` | [HuggingFace](https://huggingface.co/datasets/openfoodfacts/product-database) |
| **NCBI PubMed API** | Scientific paper search engine | `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi` | [API Docs](https://www.ncbi.nlm.nih.gov/books/NBK25499/) |
| **EFSA (European Food Safety Authority)** | Food additive regulations | `https://www.efsa.europa.eu` | [Database](https://www.efsa.europa.eu/en/food-additives-evaluations) |

### Download Specifications

**food.parquet (836,897 products)**
```
Size: ~2.5 GB
Download time: 30–60 minutes (10Mbps connection)
Main columns: product_name, nutriscore_grade, nova_group, additives, packaging, etc.
Source: Open Food Facts + HuggingFace Hub
```

**additives.json (651 additives)**
```
Size: ~5 MB
Main columns: E_number, name, vegan, vegetarian, risk_level, etc.
Source: Open Food Facts API
```

---

## 📊 Dependencies

**Python:** 3.9 or higher

**Main libraries:**

```
# requirements.txt
pandas==2.0.3
numpy==1.24.3
scikit-learn==1.3.0
matplotlib==3.7.2
seaborn==0.12.2
requests==2.31.0
scipy==1.11.1
streamlit==1.26.0
pyarrow==12.0.1
python-dotenv==1.0.0       # For reading .env
jupyter==1.0.0             # For running notebooks
plotly==5.16.1             # For 3D visualisations
```

**Quick install:**

```bash
pip install -r requirements.txt
```

**Compatibility notes:**

- **Mac M1/M2:** May require `conda` instead of `pip` for numpy/scipy
  ```bash
  conda install -c conda-forge scikit-learn scipy
  ```

- **Windows + WSL2:** Ensure `python-dotenv` is installed
  ```bash
  pip install python-dotenv --upgrade
  ```

---

## ⚠️ Known Limitations

| Limitation | Description | Future Solution |
|-----------|-------------|-----------------|
| **Additive synergy** | SSI analyses additives individually, not interactions | Study dangerous combinations in PubMed |
| **OFF data completeness** | Not all listed products have detailed additive data | Use only products with complete data |
| **Regulatory changes** | If EFSA withdraws/approves an additive, SSI changes | Automated pipeline with daily updates |
| **Geographic bias** | Data primarily from Western Europe | Expand to more regions |
| **Base ingredients** | Does not analyse specific sugars/saturated fats | Integrate detailed nutritional labels |

---

## 🤝 Contributing

Contributions are welcome. For major changes:

1. Fork the repository
2. Create a branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 👤 Author

**Mikel Añibarro Ortega**
Data Science | Bootcamp The Bridge, Campus Bilbao (2026)

### 📌 Connect with me

- 🔗 LinkedIn: [mikelanibarroortega](https://www.linkedin.com/in/mikelanibarroortega/)
- 🔬 ORCID: [0000-0002-2835-5079](https://orcid.org/0000-0002-2835-5079)
- 📧 Email: mklanibarro@gmail.com
- 🗂️ Portfolio: [@mikel-ao]((https://mikel-ao.github.io/my_portfolio/))

---

## 📚 References

### Related Repositories
- [Open Food Facts GitHub](https://github.com/openfoodfacts)
- [NOVA Food Classification](https://www.fao.org/documents/card/en/c/CA5644EN)

