# -*- coding: utf-8 -*-

"""Compare future opinion changes for Top25% and Bottom25% IdeoP users.

Use the final Fig. 2c regression-matched sample and select groups within each
quarter_pair and political_bias. bias_change is MediaScore(q+1)-MediaScore(q).
This version compares both tails using boxplots and exports group differences.
"""
from pathlib import Path as _ReleasePath
import sys as _release_sys
_release_root = next(_p for _p in _ReleasePath(__file__).resolve().parents if (_p / 'runtime_config.py').is_file())
_release_sys.path.insert(0, str(_release_root))
from runtime_config import project_path


import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


ROOT_DIR = project_path('data', 'intermediate/Openmindness/media/连续的/total')

BRIDGE_INPUT_CSV = os.path.join(
    ROOT_DIR,
    'transition_openmindness_analysis/regression_matched_7x7_transition/transition_7x7_regression_matched_user_level.csv'
)

REGRESSION_RESULTS_CSV = os.path.join(
    ROOT_DIR,
    'regression_outputs/regression_results_total.csv'
)

OUT_DIR = os.path.join(
    ROOT_DIR,
    'transition_openmindness_analysis/top25_vs_bottom25_openmindness_bias_change_boxplot'
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
    for i in range(len(QUARTERS)-1)
]

# Keep only the three middle user categories: LL, C and RL.
POLITICAL_BIAS_ORDER = [
    "left_leaning",
    "center",
    "right_leaning",
]

POLITICAL_BIAS_LABELS = {
    "left_leaning": "LL",
    "center": "C",
    "right_leaning": "RL",
}

# Configure political-category colors.
node_color_config = {
    # "left": (51/255, 102/255, 153/255),
    "left_leaning": (181/255, 216/255, 243/255),
    "center": (240/255, 230/255, 140/255),
    "right_leaning": (255/255, 153/255, 153/255),
    # "right": (204/255, 102/255, 102/255),
    # "extreme_right": (139/255, 26/255, 26/255),
}


def load_sample():

    df = pd.read_csv(
        BRIDGE_INPUT_CSV,
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
        df[c] = pd.to_numeric(
            df[c],
            errors="coerce"
        )

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

    return df



def validate_fig2c(df):

    reg = pd.read_csv(
        REGRESSION_RESULTS_CSV,
        encoding="utf-8-sig"
    )

    reg["quarter_pair"] = (
        reg["quarter_pair"]
        .astype(str)
        .str.strip()
    )

    reg["political_bias"] = (
        reg["political_bias"]
        .astype(str)
        .str.strip()
    )

    reg["n_obs"] = pd.to_numeric(
        reg["n_obs"],
        errors="coerce"
    )

    bridge = (
        df.groupby(
            [
                "quarter_pair",
                "political_bias"
            ]
        )
        .size()
        .reset_index(name="bridge_n_obs")
    )

    check = bridge.merge(
        reg[
            [
                "quarter_pair",
                "political_bias",
                "n_obs"
            ]
        ],
        on=[
            "quarter_pair",
            "political_bias"
        ],
        how="outer"
    )

    check["difference"] = (
        check["bridge_n_obs"]
        -
        check["n_obs"]
    )

    check.to_csv(
        os.path.join(
            OUT_DIR,
            "fig2c_sample_validation.csv"
        ),
        index=False,
        encoding="utf-8-sig"
    )

    print(check)

    return check



def select_top_bottom25(df):

    results = []

    audit = []

    for qp in QUARTER_PAIRS:

        for pb in POLITICAL_BIAS_ORDER:

            sub = df[
                (df["quarter_pair"] == qp)
                &
                (df["political_bias"] == pb)
            ].copy()

            n = len(sub)

            if n == 0:
                continue


            n25 = int(
                np.ceil(
                    n * 0.25
                )
            )


            sub_high = (
                sub.sort_values(
                    [
                        "IdeoP",
                        "user_id"
                    ],
                    ascending=[
                        False,
                        True
                    ],
                    kind="mergesort"
                )
                .head(n25)
                .copy()
            )

            sub_low = (
                sub.sort_values(
                    [
                        "IdeoP",
                        "user_id"
                    ],
                    ascending=[
                        True,
                        True
                    ],
                    kind="mergesort"
                )
                .head(n25)
                .copy()
            )


            sub_high["openmindness_group"] = "Top25%"
            sub_low["openmindness_group"] = "Bottom25%"


            results.extend(
                [
                    sub_high,
                    sub_low
                ]
            )


            audit.append(
                {
                    "quarter_pair": qp,
                    "political_bias": pb,
                    "n_total": n,
                    "n_top25": len(sub_high),
                    "n_bottom25": len(sub_low),
                    "top25_mean_IdeoP": sub_high["IdeoP"].mean(),
                    "bottom25_mean_IdeoP": sub_low["IdeoP"].mean()
                }
            )


    selected = pd.concat(
        results,
        ignore_index=True
    )

    pd.DataFrame(audit).to_csv(
        os.path.join(
            OUT_DIR,
            "selection_audit.csv"
        ),
        index=False,
        encoding="utf-8-sig"
    )

    selected.to_csv(
        os.path.join(
            OUT_DIR,
            "top25_bottom25_openmindness_user_level.csv"
        ),
        index=False,
        encoding="utf-8-sig"
    )

    return selected



def calculate_group_stats(df):

    stats = (
        df.groupby(
            [
                "political_bias",
                "openmindness_group"
            ]
        )
        ["bias_change"]
        .agg(
            n="count",
            mean="mean",
            median="median",
            std="std",
            mean_abs=lambda x: np.abs(x).mean()
        )
        .reset_index()
    )

    stats.to_csv(
        os.path.join(
            OUT_DIR,
            "boxplot_group_statistics.csv"
        ),
        index=False,
        encoding="utf-8-sig"
    )

    return stats



def plot_boxplot(df):

    fig, ax = plt.subplots(
        figsize=(14, 6),
        dpi=300
    )

    positions = []
    data = []
    labels = []

    width = 0.18

    for i, pb in enumerate(POLITICAL_BIAS_ORDER):

        for j, group in enumerate(
            [
                "Top25%",
                "Bottom25%"
            ]
        ):

            values = df[
                (df["political_bias"] == pb)
                &
                (df["openmindness_group"] == group)
            ]["bias_change"].values


            data.append(values)

            positions.append(
                i + (j-0.5)*0.25
            )

            labels.append(
                group
            )


    bp = ax.boxplot(
        data,
        positions=positions,
        widths=width,
        patch_artist=True,
        showfliers=False
    )

    # ========================================================
    # Configure group colors and hatches.
    # Use the corresponding political-category color.
    # Distinguish Top25% and Bottom25% with different fill hatches.
    # ========================================================
    for idx, patch in enumerate(bp["boxes"]):

        # Index interpretation:
        # L-Top25, L-Bottom25, LL-Top25, LL-Bottom25 ...
        pb_idx = idx // 2
        group_idx = idx % 2

        pb = POLITICAL_BIAS_ORDER[pb_idx]

        patch.set_facecolor(
            node_color_config[pb]
        )

        if group_idx == 0:
            # Top25%
            patch.set_hatch("")
            patch.set_alpha(0.85)
        else:
            # Bottom25%
            patch.set_hatch("//")
            patch.set_alpha(0.45)

        patch.set_edgecolor("black")

    # Use black median lines and whiskers.
    for median in bp["medians"]:
        median.set_color("black")
        median.set_linewidth(1.5)

    for whisker in bp["whiskers"]:
        whisker.set_color("black")

    for cap in bp["caps"]:
        cap.set_color("black")


    ax.axhline(
        0,
        linestyle="--",
        linewidth=1
    )


    ax.set_xticks(
        range(len(POLITICAL_BIAS_ORDER))
    )

    ax.set_xticklabels(
        [
            POLITICAL_BIAS_LABELS[x]
            for x in POLITICAL_BIAS_ORDER
        ]
    )


    ax.set_xlabel(
    "User Ideological Category"
    )

    ax.set_ylabel(
        "Bias Change (MediaScore q+1 - q)"
    )


    ax.set_title(
    "Bias Change of High- and Low-Permeability Users"
    )


    ax.grid(
        axis="y",
        linestyle="--",
        alpha=0.3
    )


    from matplotlib.lines import Line2D

    from matplotlib.patches import Patch

    legend = [
        Patch(
            facecolor="white",
            edgecolor="black",
            label="High Ideological Permeability(Top 25%)"
        ),
        Patch(
            facecolor="white",
            edgecolor="black",
            hatch="//",
            label="Low Ideological Permeability(Bottom 25%)"
        )
    ]

    ax.legend(
        handles=legend,
        frameon=False
    )

    # ========================================================
    # Add significance brackets and *** annotations above the three group comparisons.
    # ========================================================
    # Set the y-coordinate of each significance bracket.
    # Bracket heights are approximately 0.8 for LL and 1.35 for C and RL.
    y_ratios = [0.95, 1.48, 1.48]  # Bracket heights for LL, C and RL, respectively.
    h = 0.03  # Height of the short vertical bracket ends.

    for i in range(len(POLITICAL_BIAS_ORDER)):
        # Find x positions for the current Top25% and Bottom25% boxes.
        x1 = i - 0.125  # i + (0 - 0.5) * 0.25
        x2 = i + 0.125  # i + (1 - 0.5) * 0.25
        y = y_ratios[i]

        # Draw the bracket through (x1,y-h), (x1,y), (x2,y), (x2,y-h).
        ax.plot([x1, x1, x2, x2], [y - h, y, y, y - h], lw=1.2, c='black')

        # Center the *** annotation above the bracket.
        ax.text((x1 + x2) * 0.5, y + 0.01, "***", ha='center', va='bottom', color='black', fontsize=12, fontweight='bold')

    # Expand the y-axis range to avoid clipping significance annotations.
    ax.set_ylim(-1.5, 1.7)

    plt.tight_layout()


    path = os.path.join(
        OUT_DIR,
        "Top25_vs_Bottom25_openmindness_bias_change_boxplot.png"
    )

    plt.savefig(
        path,
        bbox_inches="tight"
    )

    plt.close()

    return path



def main():

    print("Loading Fig.2c matched sample...")

    df = load_sample()

    print(
        "sample:",
        len(df)
    )

    validate_fig2c(df)

    selected = select_top_bottom25(df)

    calculate_group_stats(selected)

    fig = plot_boxplot(selected)

    print(
        "Finished:",
        fig
    )


if __name__ == "__main__":
    main()
