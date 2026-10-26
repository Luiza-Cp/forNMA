# forNMA

Tools for single-cell image analysis and phenotype integration, including registration, segmentation, tracking, plotting, UMAP, and statistical analyses (one-way, two-way, chi-square).

## Features

- Image pipeline: registration → segmentation (+feature extraction) → tracking → drawing overlays.
- NMA plots (dot/heatmap/joint) with reusable settings.
- General plotting module (box/violin/dot/bar/scatter/line/rolling-average/CPD).
- UMAP utilities: compute embeddings, elbow plot, and color by column or KMeans.
- Statistics:
  - One-way (ANOVA or Kruskal, with Tukey/Dunn post-hoc when appropriate).
  - Two-way (Type II ANOVA or Scheirer-Ray-Hare, with Tukey/Dunn post-hoc).
  - Chi-square global + pairwise post-hoc with multiple-testing correction.
  - Chi-square subgroup comparisons (2×2 per category with correction).
- Consistent logging and structured CSV outputs.

## Installation

For the desktop CPU installers (Windows, Linux and macOS), see
[packaging/README.md](packaging/README.md). These packages bundle Python,
the web interface, CPU analysis dependencies, Cellpose models and napari-TRACE.
Desktop installers are built directly from the current source tree; generated
packages and dependency folders are not stored with the source code.

```bash
# Editable install during development
pip install -e .

# (Optional) From TestPyPI once published:
# pip install --index-url https://test.pypi.org/simple fornma
```

Python 3.10–3.12 is supported; desktop CPU installers are built with Python 3.11.
See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and validation.
The project uses the [BSD 3-Clause license](LICENSE).

## Command-line interface

After installation, the entrypoint is:

```bash
fornma -h
```

### Registration

```bash
fornma registration <paths...> <path_to_save> [--crop True|False]
```

- Registers images across frames/channels found in the given folders.

### Segmentation

```bash
fornma segmentation <parameters.toml> [--preview]
```

- Runs segmentation and feature extraction from a TOML configuration.

```bash
fornma segmentation init-config <destination>
```
- Copies the default parameters.toml into <destination> (file or folder). Used to configure segmentation

Example:

```bash
fornma segmentation init-config ./my_config_folder
```

### Tracking & Drawing

```bash
fornma tracking <Results.csv> <path_to_save> [--max_distance INT] [--time_window INT]   [--max_split_distance INT] [--max_gap_closing_distance INT] [--allow_merging True|False]

fornma draw_tracking <tracking.csv> <images_folder> <path_to_save> [--rescale_intensity True|False]
```

### Filters

```bash
fornma filter <Results.csv> <path_to_save> <column1> <column2> [--draw] [--path_to_pkl PATH]
```

### NMA

```bash
# Create / update settings from a control table
fornma NMA settings <control_table.csv> [--area_standard_deviation FLOAT] [--NII_standard_deviation FLOAT] [--headless True|False]

# Display current settings
fornma NMA show_settings

# Heatmap
fornma NMA heatmap_plot <tables...> <saving_path> [--overtime] [--single] [--jointplot]

# Dot plot
fornma NMA dot_plot <tables...> <saving_path> [--column1 COL] [--column2 COL] [--sample_size INT] [--single] [--overtime]
```

### Generic plots

```bash
fornma plot box     <Results.csv> <path_to_save> <y> [--hue COL] [--dot COL] [--conditions ...] [--gate] [--x COL]
fornma plot violin  <Results.csv> <y> <path_to_save> [--hue COL] [--dot COL] [--conditions ...] [--gate] [--x COL]
fornma plot dot     <Results.csv> <y> <path_to_save> [--hue COL] [--conditions ...] [--gate] [--x COL]
fornma plot bar     <Results.csv> <y> <path_to_save> [--conditions ...] [--gate] [--x COL]
fornma plot scatter <Results.csv> <x> <y> <path_to_save> [--hue COL] [--size COL] [--conditions ...] [--gate]
fornma plot line    <Results.csv> <path_to_save> <y> [--frames ...] [--confidence_interval INT] [--style COL] [--hue COL] [--size COL] [--conditions ...] [--gate] [--x COL]
fornma plot rolling-average <Results.csv> <path_to_save> <y> <n> [--conditions ...] [--gate] [--x COL]
fornma plot cpd     <Results.csv> <path_to_save> <frames ...> [--control NAME] [--conditions ...] [--gate] [--x COL] [--y COL]
```

---

## UMAP module

Compute embeddings, elbow plot, and color by column or KMeans.

### 1) Compute embedding

```bash
fornma umap run <csv...> <out_dir> [--columns COL1 COL2 ...] [--n_neighbors INT] [--min_dist FLOAT] [--metric Euclidean|...] [--scale/--no-scale]
```

**Outputs in `<out_dir>`**
- `Results with umap coordinates.csv` (original table + `UMAP1`, `UMAP2`)
- `umap_YYYYMMDD-HHMMSS.png`
- `logs-fornma.txt` (created automatically when using `out_dir`)

**Example**

```bash
fornma umap run   ./data/example.csv   ./results   --columns Area
```

### 2) Elbow plot

```bash
fornma umap elbow "<out_dir>/Results with umap coordinates.csv" <out_dir> [--k_min INT] [--k_max INT]
```

Produces `elbow_plot.png`.

### 3) Color UMAP

By existing column:

```bash
fornma umap color "<out_dir>/Results with umap coordinates.csv" <out_dir> --color_col Condition
```

By KMeans clusters:

```bash
fornma umap color "<out_dir>/Results with umap coordinates.csv" <out_dir> --use_clusters --n_clusters 4
```

Produces `umap_colored_*.png` (+ optional clustered CSV when using KMeans).

---

## Statistics module

All statistical subcommands accept **one or more CSVs**; they are concatenated after validating the presence of a non-empty `Condition` column. Logs are **forced** to `<save_dir>/logs-fornma.txt` whenever `--save_dir` is provided.

### 1) One-way analysis

```bash
fornma stats oneway <csv...> <numeric_col> <group_col>   --save_dir <out_dir> [--alpha FLOAT] [--pairs_of_interest ...] [--log_file PATH]
```

- Chooses ANOVA (with Tukey) if Shapiro/Levene pass; otherwise Kruskal (with Dunn).
- Saves:
  - `<out_dir>/oneway_main.csv` (ANOVA table or Kruskal summary),
  - `<out_dir>/oneway_posthoc.csv` (if applicable),
  - `<out_dir>/oneway_summary.csv`.

**Example**

```bash
fornma stats oneway   ./data/example.csv   Area Condition   --save_dir ./results
```

### 2) Two-way analysis

```bash
fornma stats twoway <csv...> <numeric_col> <group_col1> <group_col2>   --save_dir <out_dir> [--alpha FLOAT] [--pairs_of_interest ...] [--log_file PATH]
```

- Uses Type II ANOVA (with Tukey on cells) if assumptions are OK; otherwise Scheirer-Ray-Hare (with optional Dunn).
- Saves:
  - `<out_dir>/twoway_main.csv` (ANOVA table or SRH results),
  - `<out_dir>/twoway_posthoc.csv` (if applicable),
  - `<out_dir>/twoway_summary.csv`.

**Example**

```bash
fornma stats twoway   ./data/example.csv   Area Condition NMA_category   --save_dir ./results
```

### 3) Chi-square (global + post-hoc)

```bash
fornma stats chi2 <csv...> <group_col> <category_col>   --save_dir <out_dir> [--expected_min FLOAT] [--correction_method auto|bonferroni|fdr_bh] [--num_simulations INT] [--log_file PATH]
```

- Global test (asymptotic; Monte Carlo fallback when expected counts are low).
- Pairwise post-hoc between group levels with multiple-testing correction.
- Saves:
  - `<out_dir>/chi2_contingency.csv` (counts),
  - `<out_dir>/chi2_percentages.csv` (% per column),
  - `<out_dir>/chi2_expected.csv` (expected counts, if available),
  - `<out_dir>/chi2_posthoc.csv` (if applicable).

**Example**

```bash
fornma stats chi2   ./data/example.csv   Condition NMA_category   --save_dir ./results
```

### 4) Chi-square subgroup comparisons

```bash
fornma stats chi2-subgroups <csv...> <group_col> <condition_col>   --save_dir <out_dir> [--expected_min FLOAT] [--correction_method bonferroni|fdr_bh|auto] [--log_file PATH]
```

- For each level in `<group_col>`, compares proportions between pairs of `<condition_col>` (2×2).
- Uses Fisher for low expected counts; otherwise chi-square.
- Saves:
  - `<out_dir>/chi2_subgroups_subgroup_results.csv` (flattened 2×2 tables + p-values),
  - `<out_dir>/chi2_subgroups_proportions.csv` (% per condition).

**Example**

```bash
fornma stats chi2-subgroups   ./data/example.csv   NMA_category Condition   --save_dir ./results
```

---

## Python API (optional)

You can also call functions/classes directly:

```python
import pandas as pd
from fornma.Statistics.Helpers import AnalysisHelper
from fornma.Statistics.OneWay import OneWayAnalysis

helper = AnalysisHelper(alpha=0.05, log_file="logs-fornma.txt")
df = helper.load_and_concat("/path/to/data.csv")
res = OneWayAnalysis(df, numeric_col="Area", group_col="Condition", helper=helper).run()
print(res["main_result"])
```

UMAP:

```python
from fornma.UMAP import perform_clustering
perform_clustering(path="/path/to/data.csv", saving_path="out", columns=["Area"])
```

---

## Outputs & logging

- When `--save_dir` is provided, logs are **always written** to `<save_dir>/logs-fornma.txt`.
- CSV outputs follow consistent naming (`*_main.csv`, `*_posthoc.csv`, `*_summary.csv`, etc.).

---

## Requirements

Core: `numpy`, `pandas`, `scipy`, `matplotlib`, `scikit-learn`, `umap-learn`.Stats: `statsmodels`, `scikit-posthocs`.Imaging: `scikit-image`, `opencv-python`, `pillow`, (`cellpose<4` if you use segmentation).Plots: `seaborn` (optional).

Your `pyproject.toml` / `environment.yml` should pin compatible versions (example):

- numpy~=1.26, pandas~=2.3, scipy~=1.16, matplotlib~=3.10, seaborn~=0.13  
- scikit-image~=0.25, scikit-learn~=1.7, pillow~=11.1, opencv-python~=4.10  
- umap-learn~=0.5.9, statsmodels, scikit-posthocs

---

## Troubleshooting

- **Command not found (`fornma`)**: reinstall in editable mode and ensure `[project.scripts] fornma = "fornma.cli:main"` is present.
- **Import errors (`src.fornma` vs `fornma`)**: use absolute package imports `fornma.*`.
- **Argparse errors**: run `fornma -h` or `fornma stats oneway -h` to confirm arguments.
- **Slow runs**: large datasets + normality/homoscedasticity tests + post-hoc can take time; try a subset first.

---

## Contributing

- Open issues and PRs with reproducible examples.
- Keep CLI help in **English**.
- Add tests for new subcommands and ensure outputs are logged and saved.

---

## License

BSD 3-Clause License.

---

## Citation

If you use **forNMA** in academic work, please cite the software and link to the repository/TestPyPI page.

---

## Changelog

See `CHANGELOG.md` (or Git tags) for version history once published.
