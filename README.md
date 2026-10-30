# Retweeting patterns and the 2020 US presidential election

Core research code for **Retweeting patterns in asymmetric political information ecosystems signal electoral outcomes in the 2020 US presidential election**.

This repository provides research code for media and politician ideology scoring, ideological permeability (IdeoP), regression, audience co-exposure, retweet communities and state-level analysis. It includes the study's label tables and a sample of raw post records. Prepare the inputs described below, configure the data and output directories, and run the modules relevant to your analysis.

## Installation

Use Python 3.11. Create and activate a virtual environment, then install the analysis dependencies:

```shell
python -m pip install -r requirements.txt
```

Optional dependencies: `igraph` for raw Top1% network extraction; `kaleido` for Plotly static export; `joblib` for parallel state-level Bootstrap and `umap-learn` for state-level embedding. Install these packages when using the corresponding analysis. Gephi is installed separately.

## Configuration

Copy the supplied `config.example.json` to `config.local.json` to customize these directories:

| Setting | Purpose | Default, relative to the repository root |
| --- | --- | --- |
| `DATA_ROOT` | Analysis input tables and account audience data | `./data` |
| `OUTPUT_ROOT` | Generated scores, networks, statistics and figures | `./outputs` |
| `LABELS_ROOT` | The four label CSVs included in this repository | `./labels` |

The defaults can be used without a local configuration file. Environment variables with these names override the JSON settings. `config.local.json` is ignored by Git. These settings control file locations; analysis parameters are defined in the scripts. Choose a separate `OUTPUT_ROOT` for each run to preserve earlier results.

## Modules and paper correspondence

| Modules | Purpose | Main input → output |
| --- | --- | --- |
| `src/media/*/score.py`, `src/politicians/score_*.py` | Media/politician scoring | Source-separated exposures + labels → sums/counts or matched politician relations |
| `src/classification/` | User categories, quarterly aggregation, common users | Prepared score means/counts → category and transition tables |
| `analysis/figure1.py` | Fig.1 composition, monthly categories and transitions | User categories + exposure/transition tables → statistics and plots |
| `analysis/consumption_ideop.py` | Fig.2 consumption matrices and IdeoP | Source scores + matched media relations → source/total IdeoP and distributions |
| `analysis/ideop_regression.py`, `analysis/ideop_regression_sensitivity.py` | Fig.2 robust regression and sensitivity | Adjacent-period scores + origin IdeoP → regression results and plots |
| `analysis/transition_bridge.py`, `analysis/ideop_group_*.py` | Matched transitions and group comparisons | Matched user records → summaries, boxplots and tests |
| `analysis/media_coexposure.py` | Fig.3 media audience overlap | Per-account user sets + ideology → Jaccard-weight CSV and selected-network statistics |
| `analysis/politician_coexposure.py` | Fig.3 politician audience overlap | Per-account user sets + ideology → selected-network GEXF |
| `analysis/cross_camp_overlap.py` | Fig.3 cross-camp comparison | Selected media-network GEXF + audience sets and user scores → overlap summaries and plots |
| `analysis/retweet_communities.py`, `analysis/community_coverage.py` | Fig.4 core networks and communities | Retweet edges or prepared node/edge tables + scores → Louvain, metrics, distributions and coverage |
| `analysis/state_map.py` | State classification and mapping | Prepared state scores + election percentages → ROC/LOSO statistics and map |
| `state_level_modeling/supervised_umap.py` | State-level composition and electoral-margin visualization | Prepared state feature matrix + vote percentages → supervised UMAP plot and feature–embedding correlations |
| `state_level_modeling/bootstrap_regression.py` | Fig.5c final OLS model and real-label Bootstrap | Prepared state features + vote percentages + existing Bootstrap log → final coefficients, scaling parameters, fitted margins and diagnostics; optional Bootstrap stage generates coefficient/OOB logs |
| `state_level_modeling/regression_plot.py` | Fig. S10 and Fig. S13 visualization | Exported final-model coefficient summaries and state margins → coefficient/stability and observed-versus-predicted plots |

Run the `state_level_modeling` modules as standalone scripts after preparing the state feature matrix and installing their optional dependencies. Their analysis settings are defined near the beginning of each script.

## Included labels and sample data

The `labels/` directory contains the following four label tables:

| File | Rows | Use |
| --- | ---: | --- |
| `media-bias-final-url-cleaned.csv` | 1,061 | Media-domain ideology labels |
| `media-bias-final-username-display.csv` | 663 | Media-account ideology labels and account identifiers |
| `politician_twitter-username-bias-type-final_without_media.csv` | 4,023 | Politician username ideology labels |
| `politician_url_bias-final.csv` | 35 | Politician-domain ideology labels |

The sample file [`test data/2019-12-06-1-merged-ok.txt`](<test data/2019-12-06-1-merged-ok.txt>) contains 1,705 raw post records in UTF-8, with one JSON object per line. It illustrates the raw record format, including post identifiers, user metadata and URL entities. To inspect the first record's field names from the repository root:

```shell
python -c "import json; from pathlib import Path; p=Path('test data/2019-12-06-1-merged-ok.txt'); f=p.open(encoding='utf-8-sig'); post=json.loads(next(f)); f.close(); print(list(post.keys()))"
```

Use the included `labels/` tables for ideology matching. The file in `test data/` provides an example of the raw JSON records; the scoring scripts read monthly tables organized into Twitter-URL, external-URL and without-URL sources, using the fields and directories described below.

The study's historical Tweet-ID source is the [#Election2020 collection](https://github.com/echen102/us-pres-elections-2020). See that collection for data access information and source terms.

## Analysis input requirements

| Input | Required meaning/fields |
| --- | --- |
| Monthly source records | `retweeted_user_id` is the current user; `retweet_origin_user_id` / `quoted_origin_user_id` identify source authors; URL-based scoring also needs `retweet_expanded_urls_array` / `quoted_expanded_urls_array`. Preserve IDs as strings. |
| Media labels | `media-bias-final-url-cleaned.csv`: `domain,bias`; `media-bias-final-username-display.csv`: `Username,bias,id_str`. UTF-8/BOM and GB18030 decoding are supported. |
| Politician labels | `politician_twitter-username-bias-type-final_without_media.csv`: `username,counts,bias,type`; `politician_url_bias-final.csv`: domain at position 0, bias at position 4. Username scores use the original 4,023-row table. |
| Politician identity crosswalk | `DATA_ROOT/lookups/politician_account_ids.csv`: `user_id,username`. Supplies identity only; scoring labels come from the original username table. |
| User score tables | `user_id,total_score,appearance_count,average_bias_points` as required by the selected reader. Media scorers write sums/counts; their mean is total/count for positive counts. |
| IdeoP/consumption inputs | Source-specific user scores and matched media relations; or prepared 7×7 matrices with defined row denominators. Total IdeoP retains its numerator and event count. |
| Account audiences | Headerless first column of user IDs per media/politician account; account identity and ideology must follow the selected loader's directory/filename structure. |
| Selected media network | `OUTPUT_ROOT/coexposure/media_network_CatTop25_EdgeTop10.gexf`, containing the selected media nodes, is the network input to `analysis/cross_camp_overlap.py`. |
| Quarterly retweet networks | `<period>_top1pct_nodes.csv`: `user_id,degree`; `<period>_top1pct_edges.csv`: `source,target,weight`. Score attachment additionally requires quarterly ideology tables. |
| State inputs | Map: `州全称,州,归一化比例` and `State,Biden Percentage,Trump Percentage`. Models: prepared `State`, vote columns at positions 2/3 and numeric features beginning at position 4. Preserve the study's state/feature selection. |
| Final state model | `DATA_ROOT/state_level_modeling/state_features.csv`: 50 distinct `State` records, named `Democratic Vote Percentage` and `Republican Vote Percentage` columns, and the prepared 30 interaction-count features beginning at column position 4 (zero-based). Feature names use the study's user-category/media-category naming convention. |
| State Bootstrap log | `DATA_ROOT/state_level_modeling/Variable_Selection_Raw_Log.csv`: `Iteration` plus the same 30 feature columns. Supply 10,000 distinct valid iterations; selected post-Lasso OLS coefficients are numeric, and unselected entries are empty/NaN. The final study model expects seven features with selection frequency greater than 50%. |

Source-month directories are `DATA_ROOT/sources/single_url/twitter_url/output_<month>`, `.../external_url/output_<month>` and `DATA_ROOT/sources/without_url/output_<month>`. Audience sets are under `DATA_ROOT/audiences/media` and `DATA_ROOT/audiences/politicians`. Prepared state features are `DATA_ROOT/state_level_modeling/state_features.csv`. Semantic subdirectories and artifact filenames below configured roots remain visible in each reader.

Politician extraction accepts the named exposure columns and adapts them to the existing loop without selecting or duplicating rows. Legacy 20-column input is also supported: positions 2=current user, 8/9=retweet URL/author and 18/19=quote URL/author. Input rows must follow the study's source-choice convention.

Six research windows are `2019_12_2020_01_2020_02`, `2020_03_2020_04_2020_05`, `2020_06_2020_07_2020_08`, `2020_09_2020_10`, `2020_11_2020_12`, and `2021_01_2021_02`.

## Main analysis rules

- Media ideology was classified into seven categories on a scale ranging from −3 to +3, while politician ideology was classified into three categories on a scale ranging from −1 to +1.
- Combine matched score totals and counts when pooling months/sources. Unmatched exposures contribute neither a score nor a count in that dimension.
- IdeoP averages weighted distances between source-specific continuous user scores and consumed-media scores. Center users consuming beyond leaning categories, or non-Center users consuming across signs, receive distance weight 2; other distances have weight 1.
- Primary IdeoP regression requires at least two events, sequential global 1.5-IQR filtering and at least 10 records per group; sensitivity uses at least three events.
- Ridgeline analysis (Fig.2b) retains user–period observations with at least five matched media-consumption events in that period, summed across `external_url`, `twitter_url` and `without_url` (`total_appear_count >= 5`). Zero IdeoP values are summarized separately; kernel-density curves use positive values.
- High/low IdeoP comparisons (Fig. S5 and Table S12) select the highest and lowest 25% within each adjacent-period pair and origin category (LL, C and RL), with each group containing `ceil(0.25 × n)` observations. IdeoP ties are ordered by user ID. Subsequent score changes are compared within each origin category, pooling the selected period pairs, using two-sided Mann–Whitney U (Wilcoxon rank-sum) tests and two-sided mean-difference permutation tests with 5,000 permutations and seed 42.
- Media co-exposure initially selects Top25 audiences per category. Politician co-exposure initially selects the leading 80% of account count by unique audience size. The union of each node's Top10 Jaccard edges is retained, followed by isolate removal and LCC extraction.
- Retweet cores use an inclusive unweighted-degree 99th-percentile node cutoff after undirected aggregation and LCC selection. Keep induced edges; there is no Top1%-edge filter. Weighted Louvain uses resolution 1.0 and seed 42. The reported edge/node measure remains E/N.
- State-level supervised UMAP applies a centered log-ratio (CLR) transform with an additive offset of `1e-6`, followed by feature standardization. Republican minus Democratic vote percentage supplies the supervision target. UMAP uses 25 neighbors, minimum distance 0.15, two dimensions, Euclidean input distance, L2 target distance, target weight 0.7 and seed 42.
- For Fig.5c, order the 50 U.S. states by the inverse-hyperbolic-sine-transformed Republican–Democratic vote margin, retain the middle 40 states, and exclude Connecticut and Delaware to use the paper's fixed 38-state final-model sample. The prepared input contains the 30 interaction features; the module reuses the paper's feature/cohort screening results rather than recomputing Cook's distance. Apply CLR with an additive offset of `1e-6`, fit standardization parameters on those 38 states, and use the same parameters to transform all 50 states.
- The default final-model stage reads the existing 10,000-iteration Bootstrap log, selects predictors with frequency greater than 50%, and directly fits OLS on the 38-state sample. All seven stable predictors are retained. Report OLS coefficients, VIF and model diagnostics; transform fitted values back to vote-margin units using `sinh`. Separate summaries distinguish the 38 fitting states, the other 12 states and all 50 states. These final-model summaries are distinct from Bootstrap OOB statistics.
- The optional real-label Bootstrap stage uses the same fixed 38-state data and preprocessing. Each of 10,000 iterations uses its index as the random seed, samples states with replacement, fits Lasso (`alpha=0.1`) and refits OLS on the selected predictors. OOB R² and Pearson correlation are evaluated when at least three OOB states are available. When no predictor is selected, the in-bag outcome mean supplies the OOB prediction.

## Running and visualization

For example, after preparing the required inputs:

```shell
python analysis/ideop_regression.py
python analysis/politician_coexposure.py
python analysis/retweet_communities.py
```

Each module operates on the inputs in the table above. A recommended order is scoring, category/period aggregation, then the relevant figure analysis. Co-exposure analysis uses account audience sets; retweet-community analysis uses extracted quarterly node/edge tables. State analyses use prepared state-level tables.

When starting from prepared intermediate results, place each file at the location read by the selected module. For example, `analysis/cross_camp_overlap.py` reads the selected media GEXF from `OUTPUT_ROOT/coexposure/media_network_CatTop25_EdgeTop10.gexf`; `analysis/retweet_communities.py` reads the quarterly node/edge tables listed above. Intermediate filenames and subdirectories are defined in each module's path settings.

The Fig.1 analyses are available as individual functions, `consumption_ideop.py` runs IdeoP analysis by default, and `retweet_communities.py` runs community analysis and visualization from prepared node/edge tables. To call a Fig.1 function:

```shell
python -c "import runpy; m=runpy.run_path('analysis/figure1.py', run_name='core_module'); m['count_source_consumption_by_user_ideology']()"
```

Choose the source and aggregation function appropriate to your input tables. The primary scoring workflow processes `external_url`, `twitter_url` and `without_url` records separately. The first two sources are stored under `sources/single_url/`, and the third under `sources/without_url/`. You can also begin with prepared score, audience, network or state tables that meet the corresponding input requirements.

### State-level final model and figures

With the state feature table and existing Bootstrap log at the default input locations above, run:

```shell
python state_level_modeling/bootstrap_regression.py --stage final
python state_level_modeling/regression_plot.py
```

The final stage writes to `OUTPUT_ROOT/state_level_modeling/regression/`:

| File | Content |
| --- | --- |
| `7变量38州_asinh_系数.csv` | Final OLS coefficients, standard errors, p-values and confidence intervals |
| `7变量38州_asinh_标准化参数.csv` | Means and scales fitted on the 38-state sample, in feature order |
| `7变量38州_asinh_全州明细.csv` | Actual/fitted values for all 50 states and fitting-sample membership |
| `7变量38州_asinh_指标.csv` | Separate summaries for the fitting 38 states, other 12 states and all 50 states |
| `7变量38州_asinh_OLS报告.txt`, `7变量38州_asinh_模型定义.json` | OLS report, fitting-state list and selected-feature specification |
| `最终38州模型_S10指标.csv` | Final coefficients, selection frequencies, conditional sign consistency and VIF |

The plotting script reads these exported tables without refitting the model or the scaler. It writes `FigS10_38州最终模型.png/.pdf` and `全州实际与预测票差对比图_38州最终模型.png/.pdf`. In the all-state plot, arrows mark predictions outside ±100 percentage points; predictions remain unchanged in the data table.

Use `--state-features`, `--bootstrap-log` and `--output-dir` to select input/output locations for fitting. For plotting, `--input-dir` selects the fitted-result directory and `--output-dir` optionally selects a separate figure directory. Both scripts stop if their target output files already exist.

To generate a new real-label Bootstrap log instead of supplying an existing one, use the following commands with the default roots:

```shell
python state_level_modeling/bootstrap_regression.py --stage bootstrap
python state_level_modeling/bootstrap_regression.py --stage final --bootstrap-log outputs/state_level_modeling/bootstrap/Variable_Selection_Raw_Log.csv
```

The Bootstrap stage writes coefficient logs, per-iteration OOB statistics, selection frequencies and the sample/preprocessing specification under `OUTPUT_ROOT/state_level_modeling/bootstrap/`. `--jobs` controls parallel workers. 

For Gephi visualization:

1. Open a GEXF exported by the politician co-exposure or retweet-community module, or import matching node and edge CSV tables. Select an undirected graph and retain edge weights and node attributes.
2. For Fig.3-style visualization, run Louvain community detection and apply ForceAtlas2. For Fig.4, use the community labels already computed by the Python analysis.
3. Map ideology to node color and the relevant supplied attribute to node size; the Fig.3 caption uses retweet volume. Adjust edge visibility and thickness using edge weights.
4. Save the Gephi project and record the layout and appearance settings, then export the figure through Gephi's Preview panel.

## License

Project code and this documentation use the [MIT License](LICENSE). Label tables and sample data remain subject to the applicable source terms; the code license does not replace those terms.
