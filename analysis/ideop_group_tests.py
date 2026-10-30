# -*- coding: utf-8 -*-
"""Robustness tests comparing Top25% and Bottom25% ideological-permeability users.

Prefer the final sample exported by the boxplot script so rank-sum and
permutation tests use the same selected observations. If that file is absent,
rebuild the sample from regression-matched data with the same selection rule.
"""
from pathlib import Path as _ReleasePath
import sys as _release_sys
_release_root = next(_p for _p in _ReleasePath(__file__).resolve().parents if (_p / 'runtime_config.py').is_file())
_release_sys.path.insert(0, str(_release_root))
from runtime_config import project_path


import os
import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu


ROOT_DIR = project_path('data', 'intermediate/Openmindness/media/连续的/total')

# Original regression-matched user-level data.
RAW_INPUT_CSV = os.path.join(
    ROOT_DIR,
    'transition_openmindness_analysis/regression_matched_7x7_transition/transition_7x7_regression_matched_user_level.csv'
)

# Final Top25/Bottom25 sample written by the boxplot script.
BOXPLOT_SELECTED_CSV = os.path.join(
    ROOT_DIR,
    'transition_openmindness_analysis/top25_vs_bottom25_openmindness_bias_change_boxplot/top25_bottom25_openmindness_user_level.csv'
)

# Output directory for robustness tests.
OUT_DIR = os.path.join(
    ROOT_DIR,
    'transition_openmindness_analysis/robustness_tests'
)

os.makedirs(OUT_DIR, exist_ok=True)


QUARTERS = [
    "2019_12_2020_01_2020_02",
    "2020_03_2020_04_2020_05",
    "2020_06_2020_07_2020_08",
    "2020_09_2020_10",
    "2020_11_2020_12",
    "2021_01_2021_02",
]

QUARTER_PAIRS = [
    f"{QUARTERS[i]}_to_{QUARTERS[i+1]}"
    for i in range(len(QUARTERS) - 1)
]

# Use the category list specified below, consistent with the boxplot analysis.
POLITICAL_BIAS_ORDER = [
    # "left",
    "left_leaning",
    "center",
    "right_leaning",
    # "right",
    # "extreme_right",
]


def load_boxplot_selected_sample():
    """Read the boxplot's exported Top25/Bottom25 sample for consistent observations."""
    df = pd.read_csv(
        BOXPLOT_SELECTED_CSV,
        encoding="utf-8-sig",
        dtype={
            "user_id": str,
            "quarter_pair": str,
            "political_bias": str,
        }
    )

    df.columns = df.columns.str.strip()

    # Convert numeric columns explicitly.
    numeric_cols = ["bias_change", "IdeoP", "total_appear_count"]
    for c in numeric_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    # Normalize the group-column name.
    if "openmindness_group" in df.columns:
        pass
    elif "group" in df.columns:
        df = df.rename(columns={"group": "openmindness_group"})
    else:
        raise ValueError(
            "Selected sample file must contain 'openmindness_group' or 'group' column."
        )

    # Apply basic input cleaning.
    required_cols = ["quarter_pair", "political_bias", "bias_change", "openmindness_group"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in selected sample: {missing}")

    df = df.dropna(subset=required_cols).copy()

    # Keep the configured categories and Top25/Bottom25 groups.
    df = df[
        df["political_bias"].isin(POLITICAL_BIAS_ORDER)
        & df["openmindness_group"].isin(["Top25%", "Bottom25%"])
    ].copy()

    return df


def build_selected_sample_from_raw():
    """Rebuild Top25/Bottom25 groups from regression-matched data when no boxplot sample exists."""
    df = pd.read_csv(
        RAW_INPUT_CSV,
        encoding="utf-8-sig",
        dtype={
            "user_id": str,
            "quarter_pair": str,
            "political_bias": str
        }
    )

    df.columns = df.columns.str.strip()

    numeric_cols = [
        "bias_change",
        "IdeoP",
        "total_appear_count"
    ]

    for c in numeric_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    # Match the selection procedure used by the boxplot script.
    df = df.dropna(
        subset=[
            "user_id",
            "quarter_pair",
            "political_bias",
            "bias_change",
            "IdeoP",
            "total_appear_count"
        ]
    )

    df = df[
        (np.isfinite(df["bias_change"])) &
        (np.isfinite(df["IdeoP"])) &
        (df["total_appear_count"] >= 2)
    ].copy()

    results = []
    audit = []

    for qp in QUARTER_PAIRS:
        for pb in POLITICAL_BIAS_ORDER:
            sub = df[
                (df["quarter_pair"] == qp) &
                (df["political_bias"] == pb)
            ].copy()

            n = len(sub)

            if n == 0:
                continue

            n25 = int(np.ceil(n * 0.25))

            sub_high = (
                sub.sort_values(
                    ["IdeoP", "user_id"],
                    ascending=[False, True],
                    kind="mergesort"
                )
                .head(n25)
                .copy()
            )

            sub_low = (
                sub.sort_values(
                    ["IdeoP", "user_id"],
                    ascending=[True, True],
                    kind="mergesort"
                )
                .head(n25)
                .copy()
            )

            sub_high["openmindness_group"] = "Top25%"
            sub_low["openmindness_group"] = "Bottom25%"

            results.extend([sub_high, sub_low])

            audit.append({
                "quarter_pair": qp,
                "political_bias": pb,
                "n_total": n,
                "n_top25": len(sub_high),
                "n_bottom25": len(sub_low),
                "top25_mean_IdeoP": sub_high["IdeoP"].mean(),
                "bottom25_mean_IdeoP": sub_low["IdeoP"].mean()
            })

    selected = pd.concat(results, ignore_index=True)

    # Save an audit table for inspection.
    pd.DataFrame(audit).to_csv(
        os.path.join(OUT_DIR, "selection_audit_rebuilt_for_robustness.csv"),
        index=False,
        encoding="utf-8-sig"
    )

    # Save the selected sample actually used for this robustness run.
    selected.to_csv(
        os.path.join(OUT_DIR, "selected_top25_bottom25_used_in_robustness.csv"),
        index=False,
        encoding="utf-8-sig"
    )

    return selected


def load_analysis_sample():
    """Prefer the exported boxplot sample; otherwise reconstruct it with the same rule."""
    if os.path.exists(BOXPLOT_SELECTED_CSV):
        print("Using boxplot-selected sample directly:")
        print(BOXPLOT_SELECTED_CSV)
        df = load_boxplot_selected_sample()

        # Copy the selected sample to the robustness output directory for provenance.
        df.to_csv(
            os.path.join(OUT_DIR, "selected_top25_bottom25_used_in_robustness.csv"),
            index=False,
            encoding="utf-8-sig"
        )

        return df
    else:
        print("Boxplot-selected sample not found.")
        print("Rebuilding selected sample using the exact same logic as the boxplot script...")
        return build_selected_sample_from_raw()


def summarize_group_stats(df):
    """Export group means for the robustness sample for comparison with boxplot statistics."""
    stats = (
        df.groupby(["political_bias", "openmindness_group"])["bias_change"]
        .agg(
            n="count",
            mean="mean",
            median="median",
            std="std"
        )
        .reset_index()
    )

    stats.to_csv(
        os.path.join(OUT_DIR, "robustness_group_statistics.csv"),
        index=False,
        encoding="utf-8-sig"
    )

    return stats


def run_mann_whitney_tests(df):
    """Run two-sided Mann-Whitney U / Wilcoxon rank-sum tests on the selected sample."""
    results = []

    for pb in POLITICAL_BIAS_ORDER:
        top = df[
            (df["political_bias"] == pb) &
            (df["openmindness_group"] == "Top25%")
        ]["bias_change"].dropna()

        bottom = df[
            (df["political_bias"] == pb) &
            (df["openmindness_group"] == "Bottom25%")
        ]["bias_change"].dropna()

        if len(top) == 0 or len(bottom) == 0:
            continue

        stat, p = mannwhitneyu(
            top,
            bottom,
            alternative="two-sided"
        )

        results.append({
            "political_bias": pb,
            "top_mean": top.mean(),
            "bottom_mean": bottom.mean(),
            "difference": top.mean() - bottom.mean(),
            "U": stat,
            "p_value": p
        })

    result = pd.DataFrame(results)

    result.to_csv(
        os.path.join(OUT_DIR, "wilcoxon_rank_sum_results.csv"),
        index=False,
        encoding="utf-8-sig"
    )

    return result


def run_permutation(df, n_perm=5000, seed=42):
    """Run a permutation test on the selected boxplot sample.
    
    Calculate p = (b+1)/(B+1) so the reported permutation p-value is never zero.
    """
    rng = np.random.default_rng(seed)
    results = []

    for pb in POLITICAL_BIAS_ORDER:
        sub = df[df["political_bias"] == pb].copy()

        top = sub[sub["openmindness_group"] == "Top25%"]["bias_change"].values
        bottom = sub[sub["openmindness_group"] == "Bottom25%"]["bias_change"].values

        if len(top) == 0 or len(bottom) == 0:
            continue

        observed = top.mean() - bottom.mean()

        values = sub["bias_change"].values
        labels = sub["openmindness_group"].values

        null = []

        for _ in range(n_perm):
            shuffled = rng.permutation(labels)

            diff = (
                values[shuffled == "Top25%"].mean()
                - values[shuffled == "Bottom25%"].mean()
            )
            null.append(diff)

        null = np.array(null)

        b = np.sum(np.abs(null) >= abs(observed))
        p = (b + 1) / (n_perm + 1)

        results.append({
            "political_bias": pb,
            "observed_difference": observed,
            "permutation_p": p,
            "n_perm": n_perm,
            "num_extreme_permutations": int(b)
        })

    result = pd.DataFrame(results)

    result.to_csv(
        os.path.join(OUT_DIR, "permutation_test_results.csv"),
        index=False,
        encoding="utf-8-sig"
    )

    return result


def main():
    df = load_analysis_sample()

    print("\nSelected sample size:", len(df))

    # Export descriptive statistics for comparison with boxplot_group_statistics.
    stats = summarize_group_stats(df)
    print("\nGroup statistics used in robustness:")
    print(stats.to_string(index=False))

    wilcoxon_result = run_mann_whitney_tests(df)
    print("\nWilcoxon results:")
    print(wilcoxon_result.to_string(index=False))

    permutation_result = run_permutation(df, n_perm=5000, seed=42)
    print("\nPermutation results:")
    print(permutation_result.to_string(index=False))

    print("\nFinished.")
    print("Outputs saved to:", OUT_DIR)


if __name__ == "__main__":
    main()