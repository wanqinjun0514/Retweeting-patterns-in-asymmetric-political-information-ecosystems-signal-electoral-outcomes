# -*- coding: utf-8 -*-
"""Fig. 1c / Fig. 2c bridge: regression-matched 7 x 7 transition analysis.

Reconstruct adjacent-period ideology-category transitions using the Fig. 2c
sample-selection procedure and summarize starting-period Ideological
Permeability (IdeoP).

The earlier bridge used common users and a consumption-count threshold of five.
This version requires total MediaScore at q and q+1, total IdeoP at q, and at
least two consumption records. It cleans missing/non-finite merged values,
applies full-sample IQR filtering first to average_info_openmindness and then
to bias_change, and audits sample counts against the current regression files.

Temporal alignment: IdeoP(u,q), MediaScore(u,q), MediaScore(u,q+1).
The origin category is the regression's political_bias, allowing checks of
n_obs for each window pair and starting category. origin_short_from_score
independently reclassifies the q score for boundary auditing. The target
category is calculated from the q+1 score using the seven-category intervals.
"""
from pathlib import Path as _ReleasePath
import sys as _release_sys
_release_root = next(_p for _p in _ReleasePath(__file__).resolve().parents if (_p / 'runtime_config.py').is_file())
_release_sys.path.insert(0, str(_release_root))
from runtime_config import project_path


import os
import glob
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# ============================================================
# 1. Parameters and paths
# ============================================================

QUARTERS = [
    "2019_12_2020_01_2020_02",
    "2020_03_2020_04_2020_05",
    "2020_06_2020_07_2020_08",
    "2020_09_2020_10",
    "2020_11_2020_12",
    "2021_01_2021_02",
]

QUARTER_PAIRS = [
    (QUARTERS[i], QUARTERS[i + 1])
    for i in range(len(QUARTERS) - 1)
]

POLITICAL_BIAS_FOLDERS = [
    "extreme_left",
    "left",
    "left_leaning",
    "center",
    "right_leaning",
    "right",
    "extreme_right",
]

# Keep this configuration consistent with the main Fig. 2c regression.
APPEAR_COUNT_THRESHOLD = 2
USE_IQR_OUTLIER_FILTER = True
MIN_N_PER_GROUP = 10

ROOT_DIR = project_path('data', 'intermediate/Openmindness/media/连续的/total')

TOTAL_BIAS_ROOT = (
    project_path('outputs', 'analyses/Average_Bias_Rating/media_average_rating/total_url-rating/user_bias_scores_by_quarter')
)

OPENMINDNESS_CSV = os.path.join(
    ROOT_DIR,
    'plots_ridgeline_correct_total/plot_data_total_correct.csv'
)

REGRESSION_OUT_DIR = os.path.join(
    ROOT_DIR,
    "regression_outputs"
)

REGRESSION_RESULTS_CSV = os.path.join(
    REGRESSION_OUT_DIR,
    "regression_results_total.csv"
)

REGRESSION_AUDIT_CSV = os.path.join(
    REGRESSION_OUT_DIR,
    "regression_total_data_audit_report.csv"
)

OUT_DIR = os.path.join(
    ROOT_DIR,
    'transition_openmindness_analysis/regression_matched_7x7_transition'
)

os.makedirs(OUT_DIR, exist_ok=True)

ZERO_ATOL = 1e-12
MAX_PLOT_POINTS_PER_CELL = 30_000
RANDOM_SEED = 42
PLOT_YLIM = (0, 6)


# Load current Fig. 2c audit references rather than hard-coding old counts.
# Read the following reference files for each bridge run.
#   1) regression_total_data_audit_report.csv
#   2) regression_results_total.csv
# Align the bridge with current Fig. 2c outputs to avoid differences caused only by stale reference counts.

STRICT_REFERENCE_MATCH = True

_AUDIT_REFERENCE_CACHE = None
_REGRESSION_RESULTS_CACHE = None


def load_current_regression_audit_reference(force_reload: bool = False) -> dict:
    'Load the current Fig. 2c audit and construct bridge reference counts.\n    \n    Reference file:\n    <configured external path>\n    \n    Return bias_quarter, bias_change and openmindness_after_threshold dictionaries\n    with n_rows/n_users counts, global stage counts for merged_before_cleaning,\n    after_dropna_inf and after_iqr, and the group_after_iqr DataFrame.\n    \n    The audit contains 42 window/category open-mindedness summaries. Aggregate\n    them to six windows; summing category-specific unique-user counts assumes\n    one category per user in each window.\n    '
    global _AUDIT_REFERENCE_CACHE

    if _AUDIT_REFERENCE_CACHE is not None and not force_reload:
        return _AUDIT_REFERENCE_CACHE

    if not os.path.exists(REGRESSION_AUDIT_CSV):
        raise FileNotFoundError(
            f"找不到当前 Fig.2c 审计文件：{REGRESSION_AUDIT_CSV}"
        )

    print(f"[READ-reference-audit] {REGRESSION_AUDIT_CSV}")

    audit = pd.read_csv(
        REGRESSION_AUDIT_CSV,
        encoding="utf-8-sig"
    )
    audit.columns = audit.columns.str.strip()

    required_cols = [
        "stage",
        "quarter",
        "quarter_pair",
        "political_bias",
        "n_rows",
        "n_users",
    ]
    missing = [c for c in required_cols if c not in audit.columns]
    if missing:
        raise ValueError(
            f"regression audit 缺少必要列：{missing}\n"
            f"当前列名：{list(audit.columns)}"
        )

    for c in ["stage", "quarter", "quarter_pair", "political_bias"]:
        audit[c] = audit[c].fillna("").astype(str).str.strip()

    for c in ["n_rows", "n_users"]:
        audit[c] = pd.to_numeric(audit[c], errors="coerce")

    if audit[["n_rows", "n_users"]].isna().any().any():
        bad = audit[
            audit["n_rows"].isna()
            | audit["n_users"].isna()
        ]
        raise ValueError(
            "regression audit 中存在无法转成数值的 n_rows / n_users：\n"
            + bad.to_string(index=False)
        )

    # 1. Bias scores for each research window.
    bias_quarter_df = audit[
        audit["stage"] == "bias_quarter"
    ].copy()

    bias_quarter = {}
    for _, row in bias_quarter_df.iterrows():
        bias_quarter[row["quarter"]] = {
            "n_rows": int(row["n_rows"]),
            "n_users": int(row["n_users"]),
        }

    # 2. Bias changes between adjacent windows.
    bias_change_df = audit[
        audit["stage"] == "bias_change"
    ].copy()

    bias_change = {}
    for _, row in bias_change_df.iterrows():
        bias_change[row["quarter_pair"]] = {
            "n_rows": int(row["n_rows"]),
            "n_users": int(row["n_users"]),
        }

    # 3. Thresholded starting-window open-mindedness counts: aggregate 42 category rows into six windows.
    open_df = audit[
        audit["stage"] == "openmindness_after_threshold"
    ].copy()

    open_quarter = (
        open_df.groupby("quarter", as_index=False)
        .agg(
            n_rows=("n_rows", "sum"),
            n_users=("n_users", "sum"),
        )
    )

    openmindness_after_threshold = {
        row["quarter"]: {
            "n_rows": int(row["n_rows"]),
            "n_users": int(row["n_users"]),
        }
        for _, row in open_quarter.iterrows()
    }

    # 4. Counts for the three global processing stages.
    global_reference = {}

    for stage_name in [
        "merged_before_cleaning",
        "after_dropna_inf",
        "after_iqr",
    ]:
        tmp = audit[
            (audit["stage"] == stage_name)
            & (audit["quarter_pair"] == "ALL")
            & (audit["political_bias"] == "ALL")
        ].copy()

        # Handle audit files in which ALL fields were read as missing or empty strings.
        if tmp.empty:
            tmp = audit[
                audit["stage"] == stage_name
            ].copy()

        if len(tmp) != 1:
            raise ValueError(
                f"当前 regression audit 中 stage={stage_name} "
                f"应有且仅有1条全局记录，实际找到 {len(tmp)} 条。"
            )

        row = tmp.iloc[0]
        global_reference[stage_name] = {
            "n_rows": int(row["n_rows"]),
            "n_users": int(row["n_users"]),
        }

    # 5. The 35 final regression groups.
    group_after_iqr = audit[
        audit["stage"]
        == "group_after_iqr_final_regression_sample"
    ][
        [
            "quarter_pair",
            "political_bias",
            "n_rows",
            "n_users",
        ]
    ].copy()

    group_after_iqr = group_after_iqr.rename(
        columns={
            "n_rows": "audit_n_obs",
            "n_users": "audit_n_users",
        }
    )

    _AUDIT_REFERENCE_CACHE = {
        "raw_audit": audit,
        "bias_quarter": bias_quarter,
        "bias_change": bias_change,
        "openmindness_after_threshold": openmindness_after_threshold,
        "global": global_reference,
        "group_after_iqr": group_after_iqr,
    }

    print("[OK-reference-audit] 当前 Fig.2c 审计 reference 已加载。")
    print(
        "[REFERENCE-global] "
        + " | ".join(
            f"{k}: rows={v['n_rows']:,}, users={v['n_users']:,}"
            for k, v in global_reference.items()
        )
    )

    return _AUDIT_REFERENCE_CACHE


def load_current_regression_results(force_reload: bool = False) -> pd.DataFrame:
    """Load regression_results_total.csv for the 35 bridge group-count comparisons."""
    global _REGRESSION_RESULTS_CACHE

    if _REGRESSION_RESULTS_CACHE is not None and not force_reload:
        return _REGRESSION_RESULTS_CACHE.copy()

    if not os.path.exists(REGRESSION_RESULTS_CSV):
        raise FileNotFoundError(
            f"找不到当前 Fig.2c 回归结果：{REGRESSION_RESULTS_CSV}"
        )

    print(f"[READ-reference-regression] {REGRESSION_RESULTS_CSV}")

    reg = pd.read_csv(
        REGRESSION_RESULTS_CSV,
        encoding="utf-8-sig"
    )
    reg.columns = reg.columns.str.strip()

    required_cols = [
        "quarter_pair",
        "political_bias",
        "n_obs",
    ]
    missing = [c for c in required_cols if c not in reg.columns]
    if missing:
        raise ValueError(
            f"regression_results_total.csv 缺少必要列：{missing}\n"
            f"当前列名：{list(reg.columns)}"
        )

    for c in ["quarter_pair", "political_bias"]:
        reg[c] = reg[c].fillna("").astype(str).str.strip()

    reg["n_obs"] = pd.to_numeric(
        reg["n_obs"],
        errors="coerce"
    )

    if reg["n_obs"].isna().any():
        raise ValueError(
            "regression_results_total.csv 中存在无法转成数值的 n_obs。"
        )

    dup = reg.duplicated(
        subset=["quarter_pair", "political_bias"],
        keep=False
    )
    if dup.any():
        raise ValueError(
            "regression_results_total.csv 中存在重复的 "
            "quarter_pair × political_bias 组合：\n"
            + reg.loc[
                dup,
                ["quarter_pair", "political_bias", "n_obs"]
            ].to_string(index=False)
        )

    _REGRESSION_RESULTS_CACHE = reg.copy()

    print(
        f"[OK-reference-regression] 回归结果组数={len(reg)}，"
        f"n_obs总和={int(reg['n_obs'].sum()):,}"
    )

    return reg.copy()


def validate_current_fig2c_reference_files():
    """Verify that the current Fig. 2c audit and regression outputs are consistent.
    
    Require the audit's after_iqr n_rows to equal summed regression n_obs, and
    require group-specific counts to agree for all 35 window/category groups.
    With STRICT_REFERENCE_MATCH enabled, stop on inconsistent reference files.
    """

    audit_ref = load_current_regression_audit_reference()
    reg = load_current_regression_results()

    final_ref = audit_ref["global"]["after_iqr"]

    reg_sum = int(reg["n_obs"].sum())

    total_match = (
        reg_sum
        == int(final_ref["n_rows"])
    )

    print("\n[PRECHECK] Fig.2c audit vs regression_results")
    print(
        f"  audit after_iqr rows = {final_ref['n_rows']:,}"
    )
    print(
        f"  regression n_obs sum = {reg_sum:,}"
    )
    print(
        f"  total count match = {total_match}"
    )

    audit_groups = audit_ref[
        "group_after_iqr"
    ].copy()

    compare = pd.merge(
        audit_groups,
        reg[
            [
                "quarter_pair",
                "political_bias",
                "n_obs",
            ]
        ],
        on=[
            "quarter_pair",
            "political_bias",
        ],
        how="outer",
    )

    compare[
        "audit_minus_regression"
    ] = (
        compare["audit_n_obs"]
        - compare["n_obs"]
    )

    compare[
        "is_exact_match"
    ] = (
        compare[
            "audit_n_obs"
        ]
        .eq(
            compare["n_obs"]
        )
    )

    match_n = int(
        compare[
            "is_exact_match"
        ].sum()
    )

    print(
        f"  group exact matches = "
        f"{match_n}/{len(compare)}"
    )

    out_path = os.path.join(
        OUT_DIR,
        "fig2c_audit_vs_regression_results_precheck.csv"
    )

    compare.to_csv(
        out_path,
        index=False,
        encoding="utf-8-sig"
    )

    if STRICT_REFERENCE_MATCH and (
        (not total_match)
        or match_n != len(compare)
    ):
        raise ValueError(
            "当前 Fig.2c 的 audit 文件与 regression_results_total.csv "
            "并非同一版结果，bridge 已停止。\n"
            f"请检查：{out_path}"
        )

    print(
        "[PASS] 当前 Fig.2c audit 与 regression_results_total.csv "
        "相互一致。"
    )

    return compare


# ============================================================
# 2. Category definitions
# ============================================================

CATEGORY_LABELS = [
    "Extreme bias Left",
    "Left",
    "Left leaning",
    "Center",
    "Right leaning",
    "Right",
    "Extreme bias right",
]

CATEGORY_SHORT = {
    "Extreme bias Left": "EL",
    "Left": "L",
    "Left leaning": "LL",
    "Center": "C",
    "Right leaning": "RL",
    "Right": "R",
    "Extreme bias right": "ER",
}

POLITICAL_BIAS_TO_SHORT = {
    "extreme_left": "EL",
    "left": "L",
    "left_leaning": "LL",
    "center": "C",
    "right_leaning": "RL",
    "right": "R",
    "extreme_right": "ER",
}

SHORT_ORDER = ["EL", "L", "LL", "C", "RL", "R", "ER"]


def categorize_bias_series(score_series: pd.Series) -> pd.Series:
    """Classify scores using the Fig. 1c seven-category boundaries.
    
    EL [-3,-2.5), L [-2.5,-1.5), LL [-1.5,-0.5), C [-0.5,0.5),
    RL [0.5,1.5), R [1.5,2.5), ER [2.5,3]. In particular, 0.5 belongs to RL.
    """
    x = pd.to_numeric(score_series, errors="coerce")

    bins = [
        -3.0,
        -2.5,
        -1.5,
        -0.5,
        0.5,
        1.5,
        2.5,
        np.nextafter(3.0, np.inf),
    ]

    cat = pd.cut(
        x,
        bins=bins,
        labels=CATEGORY_LABELS,
        right=False,
        include_lowest=True,
    )

    return cat.astype("object")


# ============================================================
# 3. Exact Fig.2c IQR function
# ============================================================

def remove_outliers_iqr(df: pd.DataFrame, column: str) -> pd.DataFrame:
    """Apply the Fig. 2c IQR rule to the entire merged candidate sample.
    
    Do not calculate separate cutoffs by window pair or political category.
    """
    if df.empty:
        return df

    Q1 = df[column].quantile(0.25)
    Q3 = df[column].quantile(0.75)
    IQR = Q3 - Q1

    if pd.isna(IQR) or IQR == 0:
        return df

    lower = Q1 - 1.5 * IQR
    upper = Q3 + 1.5 * IQR

    return df[
        (df[column] >= lower)
        & (df[column] <= upper)
    ].copy()


# ============================================================
# 4. Read total MediaScore exactly as Fig.2c
# ============================================================

def find_total_bias_file(quarter: str, political_bias: str) -> str:
    folder_path = os.path.join(
        TOTAL_BIAS_ROOT,
        political_bias
    )

    if not os.path.isdir(folder_path):
        print(
            f"[WARN-total-bias] 缺少 total bias 文件夹: "
            f"{folder_path}"
        )
        return ""

    exact = os.path.join(
        folder_path,
        f"{quarter}_{political_bias}_user.csv"
    )

    if os.path.exists(exact):
        return exact

    cand = glob.glob(
        os.path.join(
            folder_path,
            f"{quarter}*.csv"
        )
    )

    return cand[0] if cand else ""


def load_total_bias_quarter_from_folders(
    quarter: str
) -> pd.DataFrame:
    """Read continuous total-media scores from the seven category folders.
    
    Retain bias_folder as additional audit metadata. The regression interface
    otherwise uses user_id and average_bias_points.
    """

    parts = []

    for political_bias in POLITICAL_BIAS_FOLDERS:

        fp = find_total_bias_file(
            quarter,
            political_bias
        )

        if not fp:
            print(
                f"[WARN-total-bias] 找不到 "
                f"{political_bias} | {quarter}"
            )
            continue

        print(
            f"[READ-total-bias] "
            f"{quarter} | {political_bias} "
            f"-> {os.path.basename(fp)}"
        )

        df = pd.read_csv(fp)

        if df.empty:
            continue

        if "user_id" not in df.columns:
            print(
                f"[WARN-total-bias] 缺 user_id: {fp}"
            )
            continue

        if "average_bias_points" not in df.columns:
            print(
                f"[WARN-total-bias] "
                f"缺 average_bias_points: {fp}"
            )
            continue

        out = df[
            ["user_id", "average_bias_points"]
        ].copy()

        out["user_id"] = (
            out["user_id"]
            .astype(str)
            .str.strip()
        )

        out["average_bias_points"] = pd.to_numeric(
            out["average_bias_points"],
            errors="coerce"
        )

        out = out.dropna(
            subset=["user_id", "average_bias_points"]
        ).copy()

        out = out[
            (out["user_id"] != "")
            & (
                out["user_id"]
                .str.lower()
                != "nan"
            )
        ].copy()

        # Use this metadata for bridge auditing without changing the Fig. 2c user set.
        out["bias_folder"] = political_bias

        if not out.empty:
            parts.append(out)

    if not parts:
        return pd.DataFrame(
            columns=[
                "user_id",
                "average_bias_points",
                "bias_folder",
            ]
        )

    result = pd.concat(
        parts,
        ignore_index=True
    )

    dup_n = result.duplicated(
        subset=["user_id"]
    ).sum()

    if dup_n > 0:
        print(
            f"[WARN-total-bias] {quarter} "
            f"重复 user_id={dup_n:,}，"
            f"与 Fig.2c 一样保留第一条。"
        )

        result = result.drop_duplicates(
            subset=["user_id"],
            keep="first"
        )

    print(
        f"[OK-total-bias] {quarter} "
        f"total 用户数: {len(result):,}"
    )

    audit_ref = (
        load_current_regression_audit_reference()
    )

    ref_info = (
        audit_ref["bias_quarter"]
        .get(quarter)
    )

    if ref_info is None:
        print(
            f"[WARN-total-bias] 当前 audit 中没有 "
            f"{quarter} 的 bias_quarter reference。"
        )
    else:
        ref_rows = int(
            ref_info["n_rows"]
        )
        ref_users = int(
            ref_info["n_users"]
        )

        actual_rows = len(result)
        actual_users = (
            result["user_id"]
            .nunique()
        )

        status = (
            "MATCH"
            if (
                actual_rows == ref_rows
                and actual_users == ref_users
            )
            else (
                f"DIFF(ref_rows={ref_rows:,}, "
                f"ref_users={ref_users:,})"
            )
        )

        print(
            f"[CHECK-total-bias] {quarter}: "
            f"rows={actual_rows:,}, users={actual_users:,} "
            f"| {status}"
        )

        if STRICT_REFERENCE_MATCH and (
            actual_rows != ref_rows
            or actual_users != ref_users
        ):
            raise ValueError(
                f"{quarter} 的 total bias 与当前 Fig.2c audit 不一致："
                f"bridge=({actual_rows:,}, {actual_users:,}) | "
                f"audit=({ref_rows:,}, {ref_users:,})"
            )

    return result


def build_total_bias_by_quarter() -> dict:
    quarter_to_df = {}

    for q in QUARTERS:
        quarter_to_df[q] = (
            load_total_bias_quarter_from_folders(q)
        )

    return quarter_to_df


def build_bias_change_for_bridge() -> pd.DataFrame:
    """Build adjacent-window score changes using the Fig. 2c inclusion procedure.
    
    Also retain the q/q+1 continuous MediaScore values and category-folder
    metadata for seven-category transition construction and auditing.
    """

    quarter_to_df = (
        build_total_bias_by_quarter()
    )

    all_rows = []

    for q1, q2 in QUARTER_PAIRS:

        d1 = quarter_to_df.get(
            q1,
            pd.DataFrame()
        )

        d2 = quarter_to_df.get(
            q2,
            pd.DataFrame()
        )

        if d1.empty or d2.empty:
            print(
                f"[SKIP-total-bias] "
                f"{q1}_to_{q2} 为空"
            )
            continue

        merged = pd.merge(
            d1,
            d2,
            on="user_id",
            how="inner",
            suffixes=("_q1", "_q2"),
            validate="one_to_one",
        )

        if merged.empty:
            continue

        merged["bias_change"] = (
            merged["average_bias_points_q2"]
            - merged["average_bias_points_q1"]
        )

        merged["quarter1"] = q1
        merged["quarter2"] = q2
        merged["quarter_pair"] = (
            f"{q1}_to_{q2}"
        )

        out = merged[
            [
                "user_id",
                "quarter1",
                "quarter2",
                "quarter_pair",
                "average_bias_points_q1",
                "average_bias_points_q2",
                "bias_folder_q1",
                "bias_folder_q2",
                "bias_change",
            ]
        ].copy()

        all_rows.append(out)

        actual_n = len(out)

        audit_ref = (
            load_current_regression_audit_reference()
        )

        pair_key = f"{q1}_to_{q2}"

        ref_info = (
            audit_ref["bias_change"]
            .get(pair_key)
        )

        if ref_info is None:
            status = "NO_REFERENCE"
        else:
            ref_n = int(
                ref_info["n_rows"]
            )

            status = (
                "MATCH"
                if ref_n == actual_n
                else f"DIFF(ref={ref_n:,})"
            )

            if (
                STRICT_REFERENCE_MATCH
                and ref_n != actual_n
            ):
                raise ValueError(
                    f"bias_change 样本数与当前 Fig.2c audit 不一致："
                    f"{pair_key} | bridge={actual_n:,}, "
                    f"audit={ref_n:,}"
                )

        print(
            f"[CHECK-bias-change] "
            f"{pair_key}: "
            f"{actual_n:,} | {status}"
        )

    if not all_rows:
        return pd.DataFrame()

    result = pd.concat(
        all_rows,
        ignore_index=True
    )

    result["user_id"] = (
        result["user_id"]
        .astype(str)
        .str.strip()
    )

    return result


# ============================================================
# 5. Read TOTAL IdeoP exactly as Fig.2c
# ============================================================

def read_openmindness_for_bridge() -> pd.DataFrame:
    """Read total-source IdeoP using the Fig. 2c input and filtering procedure.
    
    Use plot_data_total_correct.csv, require total_appear_count >= 2 and retain
    the file's bias as political_bias. Do not add the earlier bridge's [0,12]
    range filter.
    """

    if not os.path.exists(
        OPENMINDNESS_CSV
    ):
        raise FileNotFoundError(
            f"找不到：{OPENMINDNESS_CSV}"
        )

    print(
        f"[READ-open-total] "
        f"{OPENMINDNESS_CSV}"
    )

    data = pd.read_csv(
        OPENMINDNESS_CSV,
        usecols=[
            "quarter",
            "user_id",
            "bias",
            "total_info_score",
            "total_appear_count",
            "average_score",
        ],
        dtype={
            "quarter": str,
            "user_id": str,
            "bias": str,
        }
    )

    data.columns = (
        data.columns.str.strip()
    )

    data["quarter"] = (
        data["quarter"]
        .astype(str)
        .str.strip()
    )

    data["user_id"] = (
        data["user_id"]
        .astype(str)
        .str.strip()
    )

    data["bias"] = (
        data["bias"]
        .astype(str)
        .str.strip()
    )

    for col in [
        "total_info_score",
        "total_appear_count",
        "average_score",
    ]:
        data[col] = pd.to_numeric(
            data[col],
            errors="coerce"
        )

    data = data.dropna(
        subset=[
            "quarter",
            "user_id",
            "bias",
            "total_info_score",
            "total_appear_count",
            "average_score",
        ]
    ).copy()

    data = data[
        (data["quarter"] != "")
        & (data["user_id"] != "")
        & (data["bias"] != "")
        & (
            data["user_id"]
            .str.lower()
            != "nan"
        )
        & (
            data["bias"]
            .str.lower()
            != "nan"
        )
    ].copy()

    data = data[
        data["quarter"].isin(QUARTERS)
        & data["bias"].isin(
            POLITICAL_BIAS_FOLDERS
        )
    ].copy()

    dup_mask = data.duplicated(
        subset=["user_id", "quarter"],
        keep=False
    )

    if dup_mask.any():

        dup_path = os.path.join(
            OUT_DIR,
            "duplicate_openmindness_user_quarter.csv"
        )

        data.loc[
            dup_mask
        ].sort_values(
            ["quarter", "user_id"]
        ).to_csv(
            dup_path,
            index=False,
            encoding="utf-8-sig"
        )

        raise ValueError(
            "openmindness 中存在重复 "
            "user_id+quarter，"
            f"明细：{dup_path}"
        )

    # Validate and recompute average_score as in Fig. 2c.
    calculated = (
        data["total_info_score"]
        / data["total_appear_count"]
    )

    valid_denominator = (
        data["total_appear_count"] > 0
    )

    inconsistent = (
        valid_denominator
        & ~np.isclose(
            data["average_score"],
            calculated,
            rtol=1e-10,
            atol=1e-12,
            equal_nan=False,
        )
    )

    if inconsistent.any():
        print(
            f"[WARN-open-total] "
            f"{int(inconsistent.sum()):,} 条 "
            f"average_score 不一致，重新计算。"
        )

        data.loc[
            valid_denominator,
            "average_score"
        ] = calculated.loc[
            valid_denominator
        ]

    invalid_numeric = (
        (data["total_appear_count"] <= 0)
        | ~np.isfinite(
            data["total_info_score"]
        )
        | ~np.isfinite(
            data["total_appear_count"]
        )
        | ~np.isfinite(
            data["average_score"]
        )
    )

    data = data.loc[
        ~invalid_numeric
    ].copy()

    # Use the main Fig. 2c count threshold.
    data = data[
        data["total_appear_count"]
        >= APPEAR_COUNT_THRESHOLD
    ].copy()

    quarter_counts = (
        data.groupby("quarter")
        .size()
        .reindex(QUARTERS)
    )

    print(
        "\n[CHECK-open-total] "
        f"appear>={APPEAR_COUNT_THRESHOLD} 各季度样本数"
    )

    audit_ref = (
        load_current_regression_audit_reference()
    )

    open_reference = (
        audit_ref[
            "openmindness_after_threshold"
        ]
    )

    for q in QUARTERS:

        actual = int(
            quarter_counts.loc[q]
        )

        ref_info = (
            open_reference.get(q)
        )

        if ref_info is None:
            status = "NO_REFERENCE"
        else:
            ref = int(
                ref_info["n_rows"]
            )

            status = (
                "MATCH"
                if actual == ref
                else f"DIFF(ref={ref:,})"
            )

            if (
                STRICT_REFERENCE_MATCH
                and actual != ref
            ):
                raise ValueError(
                    f"openmindness threshold 后样本数与当前 "
                    f"Fig.2c audit 不一致：{q} | "
                    f"bridge={actual:,}, audit={ref:,}"
                )

        print(
            f"  {q}: "
            f"{actual:,} | {status}"
        )

    out = data[
        [
            "user_id",
            "average_score",
            "bias",
            "quarter",
            "total_appear_count",
        ]
    ].copy()

    out.columns = [
        "user_id",
        "average_info_openmindness",
        "political_bias",
        "quarter",
        "total_appear_count",
    ]

    return out


# ============================================================
# 6. Construct exact Fig.2c final sample + 7×7 bridge labels
# ============================================================

def build_regression_matched_transition_sample():

    # Load the current Fig. 2c audit and regression outputs at runtime.
    # Do not use manually hard-coded counts from older runs.
    audit_ref = (
        load_current_regression_audit_reference()
    )

    global_ref = (
        audit_ref["global"]
    )

    bias_df = (
        build_bias_change_for_bridge()
    )

    open_df = (
        read_openmindness_for_bridge()
    )

    if bias_df.empty or open_df.empty:
        raise ValueError(
            "bias_df 或 open_df 为空。"
        )

    # --------------------------------------------------------
    # Stage A: same merge as Fig.2c
    # --------------------------------------------------------

    merged_df = pd.merge(
        bias_df,
        open_df,
        left_on=[
            "user_id",
            "quarter1",
        ],
        right_on=[
            "user_id",
            "quarter",
        ],
        how="inner",
        validate="many_to_one",
    ).drop(
        columns=["quarter"]
    )

    n_merge_rows = len(merged_df)
    n_merge_users = (
        merged_df["user_id"]
        .nunique()
    )

    print(
        "\n[CHECK] merged_before_cleaning"
    )

    print(
        f"rows={n_merge_rows:,}, "
        f"users={n_merge_users:,}"
    )

    merge_ref = global_ref[
        "merged_before_cleaning"
    ]

    print(
        "reference(current audit): "
        f"rows={merge_ref['n_rows']:,}, "
        f"users={merge_ref['n_users']:,}"
    )

    if STRICT_REFERENCE_MATCH and (
        n_merge_rows != merge_ref["n_rows"]
        or n_merge_users != merge_ref["n_users"]
    ):
        raise ValueError(
            "merged_before_cleaning 与当前 Fig.2c audit 不一致："
            f"bridge=({n_merge_rows:,}, {n_merge_users:,}) | "
            f"audit=({merge_ref['n_rows']:,}, {merge_ref['n_users']:,})"
        )

    # --------------------------------------------------------
    # Stage B: same missing / inf cleaning as Fig.2c
    # --------------------------------------------------------

    merged_df[
        "average_info_openmindness"
    ] = pd.to_numeric(
        merged_df[
            "average_info_openmindness"
        ],
        errors="coerce"
    )

    merged_df[
        "bias_change"
    ] = pd.to_numeric(
        merged_df[
            "bias_change"
        ],
        errors="coerce"
    )

    cleaned_df = merged_df.dropna(
        subset=[
            "bias_change",
            "average_info_openmindness",
            "political_bias",
            "quarter_pair",
        ]
    ).copy()

    cleaned_df = cleaned_df[
        ~cleaned_df.isin(
            [np.inf, -np.inf]
        ).any(axis=1)
    ].copy()

    n_clean_rows = len(cleaned_df)
    n_clean_users = (
        cleaned_df["user_id"]
        .nunique()
    )

    print(
        "\n[CHECK] after_dropna_inf"
    )

    print(
        f"rows={n_clean_rows:,}, "
        f"users={n_clean_users:,}"
    )

    clean_ref = global_ref[
        "after_dropna_inf"
    ]

    print(
        "reference(current audit): "
        f"rows={clean_ref['n_rows']:,}, "
        f"users={clean_ref['n_users']:,}"
    )

    if STRICT_REFERENCE_MATCH and (
        n_clean_rows != clean_ref["n_rows"]
        or n_clean_users != clean_ref["n_users"]
    ):
        raise ValueError(
            "after_dropna_inf 与当前 Fig.2c audit 不一致："
            f"bridge=({n_clean_rows:,}, {n_clean_users:,}) | "
            f"audit=({clean_ref['n_rows']:,}, {clean_ref['n_users']:,})"
        )

    # --------------------------------------------------------
    # Stage C: EXACT same sequential global IQR as Fig.2c
    # --------------------------------------------------------

    if USE_IQR_OUTLIER_FILTER:

        final_df = remove_outliers_iqr(
            cleaned_df,
            "average_info_openmindness"
        )

        final_df = remove_outliers_iqr(
            final_df,
            "bias_change"
        )

    else:
        final_df = cleaned_df.copy()

    n_final_rows = len(final_df)
    n_final_users = (
        final_df["user_id"]
        .nunique()
    )

    print(
        "\n[CHECK] after_iqr / "
        "final Fig.2c candidate sample"
    )

    print(
        f"rows={n_final_rows:,}, "
        f"users={n_final_users:,}"
    )

    final_ref = global_ref[
        "after_iqr"
    ]

    print(
        "reference(current audit): "
        f"rows={final_ref['n_rows']:,}, "
        f"users={final_ref['n_users']:,}"
    )

    if STRICT_REFERENCE_MATCH and (
        n_final_rows != final_ref["n_rows"]
        or n_final_users != final_ref["n_users"]
    ):
        raise ValueError(
            "after_iqr 与当前 Fig.2c audit 不一致："
            f"bridge=({n_final_rows:,}, {n_final_users:,}) | "
            f"audit=({final_ref['n_rows']:,}, {final_ref['n_users']:,})"
        )

    # --------------------------------------------------------
    # Stage D: preserve q1/q2 scores and create bridge categories
    # --------------------------------------------------------

    final_df[
        "date1_average"
    ] = pd.to_numeric(
        final_df[
            "average_bias_points_q1"
        ],
        errors="coerce"
    )

    final_df[
        "date2_average"
    ] = pd.to_numeric(
        final_df[
            "average_bias_points_q2"
        ],
        errors="coerce"
    )

    final_df[
        "IdeoP"
    ] = final_df[
        "average_info_openmindness"
    ]

    # Fig.1c score-based origin / target
    final_df[
        "origin_category_from_score"
    ] = categorize_bias_series(
        final_df[
            "date1_average"
        ]
    )

    final_df[
        "target_category_from_score"
    ] = categorize_bias_series(
        final_df[
            "date2_average"
        ]
    )

    final_df[
        "origin_short_from_score"
    ] = final_df[
        "origin_category_from_score"
    ].map(
        CATEGORY_SHORT
    )

    final_df[
        "target_short"
    ] = final_df[
        "target_category_from_score"
    ].map(
        CATEGORY_SHORT
    )

    # Fig.2c actual origin group
    final_df[
        "origin_short_regression"
    ] = final_df[
        "political_bias"
    ].map(
        POLITICAL_BIAS_TO_SHORT
    )

    # --------------------------------------------------------
    # IMPORTANT:
    # Use Fig. 2c political_bias as the bridge origin category.
    # Check the 35 group counts against regression n_obs.
    # --------------------------------------------------------

    final_df[
        "origin_short"
    ] = final_df[
        "origin_short_regression"
    ]

    final_df[
        "exact_transition"
    ] = (
        final_df["origin_short"]
        + "→"
        + final_df["target_short"]
    )

    # --------------------------------------------------------
    # Audit 1: q1 score category vs Fig.2c political_bias
    # --------------------------------------------------------

    mismatch_mask = (
        final_df[
            "origin_short_from_score"
        ]
        != final_df[
            "origin_short_regression"
        ]
    )

    mismatch_df = final_df.loc[
        mismatch_mask
    ].copy()

    mismatch_path = os.path.join(
        OUT_DIR,
        "origin_category_score_vs_regression_bias_mismatch.csv"
    )

    mismatch_df.to_csv(
        mismatch_path,
        index=False,
        encoding="utf-8-sig"
    )

    print(
        "\n[CHECK] q1 category consistency"
    )

    print(
        f"score-based vs regression political_bias "
        f"mismatch = {len(mismatch_df):,}"
    )

    if len(mismatch_df) > 0:

        print(
            "[NOTE] 这一步非常重要。"
            "如果主要集中在边界值（例如 0.5），"
            "说明 Fig.1c 分类边界与 Fig.2c political_bias "
            "历史标签存在边界口径差异。"
        )

        print(
            f"[SAVE] mismatch detail: "
            f"{mismatch_path}"
        )

    # Require a valid target category.
    invalid_target = final_df[
        final_df[
            "target_short"
        ].isna()
    ]

    if len(invalid_target) > 0:

        invalid_path = os.path.join(
            OUT_DIR,
            "invalid_target_category_after_regression_filter.csv"
        )

        invalid_target.to_csv(
            invalid_path,
            index=False,
            encoding="utf-8-sig"
        )

        raise ValueError(
            f"最终 Fig.2c 样本中有 "
            f"{len(invalid_target):,} 条 q2 score "
            f"无法映射到七分类。明细：{invalid_path}"
        )

    # --------------------------------------------------------
    # Save final user-level bridge dataset
    # --------------------------------------------------------

    keep_cols = [
        "quarter1",
        "quarter2",
        "quarter_pair",
        "user_id",

        "date1_average",
        "date2_average",
        "bias_change",

        "political_bias",
        "origin_short_regression",
        "origin_short_from_score",
        "origin_short",
        "target_short",
        "exact_transition",

        "total_appear_count",
        "IdeoP",
    ]

    final_bridge = final_df[
        keep_cols
    ].copy()

    final_path = os.path.join(
        OUT_DIR,
        "transition_7x7_regression_matched_user_level.csv"
    )

    final_bridge.to_csv(
        final_path,
        index=False,
        encoding="utf-8-sig"
    )

    # --------------------------------------------------------
    # Save bridge stage audit
    # --------------------------------------------------------

    audit_df = pd.DataFrame(
        [
            {
                "stage": "merged_before_cleaning",
                "n_rows": n_merge_rows,
                "n_users": n_merge_users,
                "reference_n_rows": merge_ref["n_rows"],
                "reference_n_users": merge_ref["n_users"],
            },
            {
                "stage": "after_dropna_inf",
                "n_rows": n_clean_rows,
                "n_users": n_clean_users,
                "reference_n_rows": clean_ref["n_rows"],
                "reference_n_users": clean_ref["n_users"],
            },
            {
                "stage": "after_iqr",
                "n_rows": n_final_rows,
                "n_users": n_final_users,
                "reference_n_rows": final_ref["n_rows"],
                "reference_n_users": final_ref["n_users"],
            },
        ]
    )

    audit_df["row_diff"] = (
        audit_df["n_rows"]
        - audit_df["reference_n_rows"]
    )

    audit_df["user_diff"] = (
        audit_df["n_users"]
        - audit_df["reference_n_users"]
    )

    audit_df["is_exact_match"] = (
        audit_df["row_diff"].eq(0)
        & audit_df["user_diff"].eq(0)
    )

    audit_path = os.path.join(
        OUT_DIR,
        "bridge_regression_sample_global_audit.csv"
    )

    audit_df.to_csv(
        audit_path,
        index=False,
        encoding="utf-8-sig"
    )

    # --------------------------------------------------------
    # Audit 2:
    # 7 target counts summed within each quarter_pair × origin
    # must equal:
    #   A) current audit group_after_iqr
    #   B) current regression_results_total.csv n_obs
    # --------------------------------------------------------

    bridge_group = (
        final_bridge.groupby(
            [
                "quarter_pair",
                "political_bias",
            ]
        )
        .agg(
            bridge_n_obs=(
                "user_id",
                "size"
            ),
            bridge_n_users=(
                "user_id",
                "nunique"
            ),
        )
        .reset_index()
    )

    bridge_7x7_sum = (
        final_bridge.groupby(
            [
                "quarter_pair",
                "political_bias",
                "target_short",
            ]
        )
        .size()
        .reset_index(
            name="n_target"
        )
    )

    target_sum_check = (
        bridge_7x7_sum.groupby(
            [
                "quarter_pair",
                "political_bias",
            ]
        )["n_target"]
        .sum()
        .reset_index(
            name="sum_7_targets"
        )
    )

    bridge_group = pd.merge(
        bridge_group,
        target_sum_check,
        on=[
            "quarter_pair",
            "political_bias",
        ],
        how="left"
    )

    bridge_group[
        "bridge_vs_7target_diff"
    ] = (
        bridge_group["bridge_n_obs"]
        - bridge_group["sum_7_targets"]
    )

    # A. The 35 groups from the current audit.
    audit_group_ref = (
        audit_ref[
            "group_after_iqr"
        ].copy()
    )

    compare = pd.merge(
        bridge_group,
        audit_group_ref,
        on=[
            "quarter_pair",
            "political_bias",
        ],
        how="outer"
    )

    compare[
        "bridge_minus_audit_n"
    ] = (
        compare["bridge_n_obs"]
        - compare["audit_n_obs"]
    )

    compare[
        "bridge_vs_audit_exact"
    ] = (
        compare["bridge_n_obs"]
        .eq(compare["audit_n_obs"])
    )

    # B. The 35 groups from regression_results_total.csv.
    reg = (
        load_current_regression_results()
    )

    reg_cols = [
        "quarter_pair",
        "political_bias",
        "n_obs",
    ]

    if "status" in reg.columns:
        reg_cols.append("status")

    compare = pd.merge(
        compare,
        reg[reg_cols],
        on=[
            "quarter_pair",
            "political_bias",
        ],
        how="outer"
    )

    compare[
        "bridge_minus_regression_n"
    ] = (
        compare["bridge_n_obs"]
        - compare["n_obs"]
    )

    compare[
        "bridge_vs_regression_exact"
    ] = (
        compare["bridge_n_obs"]
        .eq(compare["n_obs"])
    )

    compare[
        "audit_vs_regression_exact"
    ] = (
        compare["audit_n_obs"]
        .eq(compare["n_obs"])
    )

    compare[
        "all_three_exact"
    ] = (
        compare["bridge_vs_7target_diff"].eq(0)
        & compare["bridge_vs_audit_exact"]
        & compare["bridge_vs_regression_exact"]
        & compare["audit_vs_regression_exact"]
    )

    compare_path = os.path.join(
        OUT_DIR,
        "bridge_35groups_vs_current_audit_and_regression.csv"
    )

    compare.to_csv(
        compare_path,
        index=False,
        encoding="utf-8-sig"
    )

    n_bridge_audit_match = int(
        compare[
            "bridge_vs_audit_exact"
        ].sum()
    )

    n_bridge_reg_match = int(
        compare[
            "bridge_vs_regression_exact"
        ].sum()
    )

    n_all_three_match = int(
        compare[
            "all_three_exact"
        ].sum()
    )

    print(
        "\n[CHECK] 35 regression groups "
        "(bridge vs current audit vs current regression_results)"
    )

    print(
        f"bridge vs audit exact matches = "
        f"{n_bridge_audit_match}/{len(compare)}"
    )

    print(
        f"bridge vs regression exact matches = "
        f"{n_bridge_reg_match}/{len(compare)}"
    )

    print(
        f"all three exact matches = "
        f"{n_all_three_match}/{len(compare)}"
    )

    if STRICT_REFERENCE_MATCH and (
        n_all_three_match != len(compare)
    ):
        raise ValueError(
            "bridge、当前 regression audit、当前 regression_results "
            "并未在所有 quarter_pair × political_bias 组完全一致。\n"
            f"请检查：{compare_path}"
        )

    print(
        "[PASS] bridge、当前 Fig.2c audit、当前 regression_results "
        "在全局阶段和35个最终回归组上全部一致。"
    )

    print(
        "\n" + "=" * 100
    )

    print(
        "Regression-matched bridge "
        "dataset completed"
    )

    print(
        f"final rows: "
        f"{len(final_bridge):,}"
    )

    print(
        f"final unique users: "
        f"{final_bridge['user_id'].nunique():,}"
    )

    print(
        f"[SAVE] final user-level: "
        f"{final_path}"
    )

    print(
        f"[SAVE] global audit: "
        f"{audit_path}"
    )

    return final_bridge


# ============================================================
# 7. 49-cell descriptive statistics on FINAL Fig.2c sample
# ============================================================

def summarize_ideop_group(
    g: pd.DataFrame
) -> dict:

    vals = pd.to_numeric(
        g["IdeoP"],
        errors="coerce"
    ).to_numpy(
        dtype=float
    )

    vals = vals[
        np.isfinite(vals)
    ]

    total_n = len(vals)

    if total_n == 0:

        return {
            "n_observations": 0,
            "n_unique_users": 0,
            "zero_count": 0,
            "zero_pct_all": np.nan,
            "mean_all": np.nan,
            "median_all": np.nan,
            "nonzero_count": 0,
            "q1_nonzero": np.nan,
            "median_nonzero": np.nan,
            "q3_nonzero": np.nan,
            "iqr_width_nonzero": np.nan,
            "p90_nonzero": np.nan,
            "p95_nonzero": np.nan,
            "ge2_count_all": 0,
            "ge2_pct_all": np.nan,
        }

    zero_mask = np.isclose(
        vals,
        0.0,
        atol=ZERO_ATOL,
        rtol=0
    )

    nonzero = vals[
        (~zero_mask)
        & (vals > 0)
    ]

    if len(nonzero) > 0:

        q1, med, q3 = np.quantile(
            nonzero,
            [
                0.25,
                0.50,
                0.75,
            ]
        )

        p90 = np.quantile(
            nonzero,
            0.90
        )

        p95 = np.quantile(
            nonzero,
            0.95
        )

    else:

        q1 = med = q3 = (
            p90
        ) = p95 = np.nan

    return {
        "n_observations":
            total_n,

        "n_unique_users":
            int(
                g["user_id"]
                .nunique()
            ),

        "zero_count":
            int(
                zero_mask.sum()
            ),

        "zero_pct_all":
            float(
                zero_mask.mean()
                * 100
            ),

        "mean_all":
            float(
                np.mean(vals)
            ),

        "median_all":
            float(
                np.median(vals)
            ),

        "nonzero_count":
            int(
                len(nonzero)
            ),

        "q1_nonzero":
            float(q1)
            if pd.notna(q1)
            else np.nan,

        "median_nonzero":
            float(med)
            if pd.notna(med)
            else np.nan,

        "q3_nonzero":
            float(q3)
            if pd.notna(q3)
            else np.nan,

        "iqr_width_nonzero":
            float(q3 - q1)
            if (
                pd.notna(q1)
                and pd.notna(q3)
            )
            else np.nan,

        "p90_nonzero":
            float(p90)
            if pd.notna(p90)
            else np.nan,

        "p95_nonzero":
            float(p95)
            if pd.notna(p95)
            else np.nan,

        "ge2_count_all":
            int(
                (vals >= 2).sum()
            ),

        "ge2_pct_all":
            float(
                (vals >= 2).mean()
                * 100
            ),
    }


def summarize_regression_matched_transitions(
    df: pd.DataFrame = None
):

    if df is None:

        fp = os.path.join(
            OUT_DIR,
            "transition_7x7_regression_matched_user_level.csv"
        )

        df = pd.read_csv(
            fp,
            dtype={
                "user_id": str
            }
        )

    pooled_rows = []

    for origin in SHORT_ORDER:

        for target in SHORT_ORDER:

            g = df[
                (
                    df["origin_short"]
                    == origin
                )
                & (
                    df["target_short"]
                    == target
                )
            ]

            row = {
                "origin_short":
                    origin,

                "target_short":
                    target,

                "exact_transition":
                    f"{origin}→{target}",
            }

            row.update(
                summarize_ideop_group(g)
            )

            pooled_rows.append(
                row
            )

    pooled_df = pd.DataFrame(
        pooled_rows
    )

    pooled_path = os.path.join(
        OUT_DIR,
        "transition_7x7_regression_matched_stats_pooled.csv"
    )

    pooled_df.to_csv(
        pooled_path,
        index=False,
        encoding="utf-8-sig"
    )

    # by quarter pair
    pair_rows = []

    for q1, q2 in QUARTER_PAIRS:

        qp = (
            f"{q1}_to_{q2}"
        )

        qdf = df[
            df["quarter_pair"]
            == qp
        ]

        for origin in SHORT_ORDER:

            for target in SHORT_ORDER:

                g = qdf[
                    (
                        qdf["origin_short"]
                        == origin
                    )
                    & (
                        qdf["target_short"]
                        == target
                    )
                ]

                row = {
                    "quarter_pair":
                        qp,

                    "origin_short":
                        origin,

                    "target_short":
                        target,

                    "exact_transition":
                        f"{origin}→{target}",
                }

                row.update(
                    summarize_ideop_group(g)
                )

                pair_rows.append(
                    row
                )

    by_pair_df = pd.DataFrame(
        pair_rows
    )

    pair_path = os.path.join(
        OUT_DIR,
        "transition_7x7_regression_matched_stats_by_quarter_pair.csv"
    )

    by_pair_df.to_csv(
        pair_path,
        index=False,
        encoding="utf-8-sig"
    )

    print(
        "\n========== Regression-matched "
        "7×7 pooled statistics =========="
    )

    show_cols = [
        "exact_transition",
        "n_observations",
        "zero_pct_all",
        "median_nonzero",
        "q1_nonzero",
        "q3_nonzero",
        "iqr_width_nonzero",
        "p90_nonzero",
        "p95_nonzero",
        "ge2_pct_all",
    ]

    print(
        pooled_df[
            show_cols
        ].round(4).to_string(
            index=False
        )
    )

    print(
        f"\n[SAVE] pooled: "
        f"{pooled_path}"
    )

    print(
        f"[SAVE] by pair: "
        f"{pair_path}"
    )

    return (
        pooled_df,
        by_pair_df
    )


# ============================================================
# 8. 7 origin panels × 7 target violins
#    using FINAL Fig.2c sample
# ============================================================

def plot_regression_matched_transition_distributions(
    df: pd.DataFrame = None
):

    if df is None:

        fp = os.path.join(
            OUT_DIR,
            "transition_7x7_regression_matched_user_level.csv"
        )

        df = pd.read_csv(
            fp,
            dtype={
                "user_id": str
            }
        )

    rng = np.random.default_rng(
        RANDOM_SEED
    )

    fig, axes = plt.subplots(
        2,
        4,
        figsize=(22, 11),
        sharey=True
    )

    axes = axes.flatten()

    for panel_idx, origin in enumerate(
        SHORT_ORDER
    ):

        ax = axes[
            panel_idx
        ]

        positions = np.arange(
            1,
            8
        )

        tick_labels = []

        for pos, target in zip(
            positions,
            SHORT_ORDER
        ):

            sub = df[
                (
                    df["origin_short"]
                    == origin
                )
                & (
                    df["target_short"]
                    == target
                )
            ].copy()

            vals_all = pd.to_numeric(
                sub["IdeoP"],
                errors="coerce"
            ).dropna().to_numpy(
                dtype=float
            )

            zero_mask = np.isclose(
                vals_all,
                0.0,
                atol=ZERO_ATOL,
                rtol=0
            )

            vals_nonzero = vals_all[
                (~zero_mask)
                & (vals_all > 0)
            ]

            if (
                len(vals_nonzero)
                > MAX_PLOT_POINTS_PER_CELL
            ):

                plot_vals = rng.choice(
                    vals_nonzero,
                    size=MAX_PLOT_POINTS_PER_CELL,
                    replace=False,
                )

            else:

                plot_vals = (
                    vals_nonzero
                )

            if len(plot_vals) >= 2:

                parts = ax.violinplot(
                    [plot_vals],
                    positions=[pos],
                    widths=0.75,
                    showmeans=False,
                    showmedians=False,
                    showextrema=False,
                )

                for body in parts[
                    "bodies"
                ]:

                    body.set_alpha(
                        0.65
                    )

                # full nonzero distribution, not sampled
                q1, med, q3 = np.quantile(
                    vals_nonzero,
                    [
                        0.25,
                        0.50,
                        0.75,
                    ]
                )

                ax.vlines(
                    pos,
                    q1,
                    q3,
                    linewidth=4,
                    color="black",
                    alpha=0.75
                )

                ax.scatter(
                    [pos],
                    [med],
                    s=22,
                    color="white",
                    edgecolor="black",
                    zorder=5
                )

            elif len(
                plot_vals
            ) == 1:

                ax.scatter(
                    [pos],
                    plot_vals,
                    s=25,
                    color="black"
                )

            if len(
                vals_all
            ) == 0:

                tick_labels.append(
                    f"{target}\n"
                    f"n=0"
                )

            else:

                tick_labels.append(
                    f"{target}\n"
                    f"n={len(vals_all):,}"
                )

        ax.set_title(
            f"{origin} origin",
            fontsize=13,
            fontweight="bold"
        )

        ax.set_xticks(
            positions
        )

        ax.set_xticklabels(
            tick_labels,
            fontsize=7.5
        )

        ax.set_ylim(
            PLOT_YLIM
        )

        ax.grid(
            axis="y",
            linestyle="--",
            alpha=0.25
        )

        ax.set_xlabel(
            "Target ideological category",
            fontsize=9
        )

        if (
            panel_idx
            % 4
            == 0
        ):

            ax.set_ylabel(
                "Ideological Permeability "
                "(IdeoP > 0)",
                fontsize=10
            )

    axes[-1].axis(
        "off"
    )

    fig.suptitle(
        "Ideological Permeability Across "
        "7×7 Ideological Transitions "
        "in the Exact Fig.2c Regression Sample",
        fontsize=16,
        fontweight="bold",
        y=0.995,
    )

    fig.tight_layout(
        rect=[
            0,
            0,
            1,
            0.97
        ]
    )

    out_png = os.path.join(
        OUT_DIR,
        "transition_7x7_regression_matched_violin.png"
    )

    plt.savefig(
        out_png,
        dpi=600,
        bbox_inches="tight"
    )

    plt.close()

    print(
        f"[SAVE] violin: "
        f"{out_png}"
    )

    return out_png


# ============================================================
# 9. Simple heatmaps
# ============================================================

def _annotated_heatmap(
    matrix: pd.DataFrame,
    title: str,
    cbar_label: str,
    out_png: str,
    fmt: str = ".2f"
):

    arr = matrix.to_numpy(
        dtype=float
    )

    fig, ax = plt.subplots(
        figsize=(9, 7.5)
    )

    im = ax.imshow(
        arr,
        aspect="auto"
    )

    cbar = fig.colorbar(
        im,
        ax=ax
    )

    cbar.set_label(
        cbar_label
    )

    ax.set_xticks(
        np.arange(
            len(SHORT_ORDER)
        )
    )

    ax.set_yticks(
        np.arange(
            len(SHORT_ORDER)
        )
    )

    ax.set_xticklabels(
        SHORT_ORDER
    )

    ax.set_yticklabels(
        SHORT_ORDER
    )

    ax.set_xlabel(
        "Target category"
    )

    ax.set_ylabel(
        "Origin category"
    )

    ax.set_title(
        title,
        fontweight="bold"
    )

    finite = arr[
        np.isfinite(arr)
    ]

    if finite.size > 0:

        vmin = np.nanmin(
            finite
        )

        vmax = np.nanmax(
            finite
        )

    else:

        vmin = 0.0
        vmax = 1.0

    span = (
        vmax - vmin
        if vmax > vmin
        else 1.0
    )

    for i in range(
        arr.shape[0]
    ):

        for j in range(
            arr.shape[1]
        ):

            value = arr[
                i,
                j
            ]

            if np.isfinite(
                value
            ):

                norm = (
                    value - vmin
                ) / span

                text_color = (
                    "white"
                    if (
                        norm < 0.20
                        or norm > 0.75
                    )
                    else "black"
                )

                ax.text(
                    j,
                    i,
                    format(
                        value,
                        fmt
                    ),
                    ha="center",
                    va="center",
                    fontsize=8,
                    color=text_color,
                )

            else:

                ax.text(
                    j,
                    i,
                    "NA",
                    ha="center",
                    va="center",
                    fontsize=8
                )

    fig.tight_layout()

    plt.savefig(
        out_png,
        dpi=600,
        bbox_inches="tight"
    )

    plt.close()


def plot_regression_matched_transition_heatmaps(
    pooled_df: pd.DataFrame = None
):

    if pooled_df is None:

        fp = os.path.join(
            OUT_DIR,
            "transition_7x7_regression_matched_stats_pooled.csv"
        )

        pooled_df = pd.read_csv(
            fp
        )

    specs = [
        (
            "median_nonzero",
            "Median Ideological Permeability",
            "Median IdeoP",
            ".2f",
        ),
        (
            "iqr_width_nonzero",
            "IQR Width of Ideological Permeability",
            "IQR width",
            ".2f",
        ),
        (
            "p90_nonzero",
            "90th Percentile of Ideological Permeability",
            "P90 IdeoP",
            ".2f",
        ),
        (
            "p95_nonzero",
            "95th Percentile of Ideological Permeability",
            "P95 IdeoP",
            ".2f",
        ),
        (
            "ge2_pct_all",
            "Share of High-Permeability Observations "
            "(IdeoP ≥ 2)",
            "Percent",
            ".1f",
        ),
    ]

    for (
        metric,
        title,
        cbar_label,
        fmt
    ) in specs:

        matrix = pooled_df.pivot(
            index="origin_short",
            columns="target_short",
            values=metric,
        ).reindex(
            index=SHORT_ORDER,
            columns=SHORT_ORDER
        )

        out_png = os.path.join(
            OUT_DIR,
            f"transition_7x7_regression_matched_heatmap_{metric}.png"
        )

        _annotated_heatmap(
            matrix,
            title,
            cbar_label,
            out_png,
            fmt=fmt
        )

        print(
            f"[SAVE] heatmap "
            f"{metric}: {out_png}"
        )


# ============================================================
# 10. One-click
# ============================================================

def run_regression_matched_bridge_analysis():

    # Step 0: verify that the current Fig. 2c audit and regression outputs agree.
    # Stop when the reference files are inconsistent.
    validate_current_fig2c_reference_files()

    df = (
        build_regression_matched_transition_sample()
    )

    pooled_df, by_pair_df = (
        summarize_regression_matched_transitions(
            df
        )
    )

    plot_regression_matched_transition_distributions(
        df
    )

    plot_regression_matched_transition_heatmaps(
        pooled_df
    )

    print(
        "\nFig.1c × Fig.2c "
        "regression-matched bridge experiment completed."
    )

    return (
        df,
        pooled_df,
        by_pair_df
    )



import os
import numpy as np
import pandas as pd


def audit_origin_category_mismatches():

    ROOT_DIR = (
        project_path('data', 'intermediate/Openmindness/media/连续的/total/transition_openmindness_analysis/regression_matched_7x7_transition')
    )

    input_csv = os.path.join(
        ROOT_DIR,
        "origin_category_score_vs_regression_bias_mismatch.csv"
    )

    out_summary = os.path.join(
        ROOT_DIR,
        "origin_category_mismatch_summary.csv"
    )

    out_boundary = os.path.join(
        ROOT_DIR,
        "origin_category_mismatch_boundary_check.csv"
    )

    print(f"[READ] {input_csv}")

    df = pd.read_csv(
        input_csv,
        dtype={"user_id": str},
        encoding="utf-8-sig"
    )

    df.columns = df.columns.str.strip()

    required_cols = [
        "user_id",
        "quarter1",
        "date1_average",
        "political_bias",
        "origin_short_regression",
        "origin_short_from_score"
    ]

    missing = [
        c for c in required_cols
        if c not in df.columns
    ]

    if missing:
        raise ValueError(
            f"缺少列：{missing}\n"
            f"当前列：{list(df.columns)}"
        )

    df["date1_average"] = pd.to_numeric(
        df["date1_average"],
        errors="coerce"
    )

    print("\n" + "=" * 80)
    print("1. mismatch 总数")
    print("=" * 80)

    print(
        f"mismatch observations = {len(df):,}"
    )

    print(
        f"unique users = {df['user_id'].nunique():,}"
    )

    # ============================================================
    # 1. Summarize which origin-category pairs disagree.
    # ============================================================

    pair_summary = (
        df.groupby(
            [
                "origin_short_regression",
                "origin_short_from_score"
            ]
        )
        .agg(
            n_observations=("user_id", "size"),
            n_users=("user_id", "nunique"),
            min_score=("date1_average", "min"),
            q1_score=("date1_average", lambda x: x.quantile(0.25)),
            median_score=("date1_average", "median"),
            q3_score=("date1_average", lambda x: x.quantile(0.75)),
            max_score=("date1_average", "max")
        )
        .reset_index()
        .sort_values(
            "n_observations",
            ascending=False
        )
    )

    pair_summary["pct_of_all_mismatch"] = (
        pair_summary["n_observations"]
        / len(df)
        * 100
    )

    print("\n" + "=" * 80)
    print("2. mismatch 类型")
    print("=" * 80)

    print(
        pair_summary.round(6).to_string(
            index=False
        )
    )

    pair_summary.to_csv(
        out_summary,
        index=False,
        encoding="utf-8-sig"
    )

    # ============================================================
    # 2. Check whether mismatches occur exactly at seven-category boundaries.
    # ============================================================

    boundaries = np.array(
        [
            -2.5,
            -1.5,
            -0.5,
            0.5,
            1.5,
            2.5
        ],
        dtype=float
    )

    def nearest_boundary(x):

        if pd.isna(x):
            return pd.Series(
                [np.nan, np.nan]
            )

        distances = np.abs(
            boundaries - x
        )

        idx = np.argmin(
            distances
        )

        return pd.Series(
            [
                boundaries[idx],
                distances[idx]
            ]
        )

    df[
        [
            "nearest_boundary",
            "distance_to_boundary"
        ]
    ] = df[
        "date1_average"
    ].apply(
        nearest_boundary
    )

    # Treat distances within the stated tolerance as boundary matches.
    df["is_exact_boundary"] = (
        df["distance_to_boundary"]
        <= 1e-10
    )

    print("\n" + "=" * 80)
    print("3. 是否由分类边界造成")
    print("=" * 80)

    exact_n = int(
        df["is_exact_boundary"].sum()
    )

    print(
        f"exact boundary mismatch = "
        f"{exact_n:,} / {len(df):,} "
        f"({exact_n / len(df) * 100:.2f}%)"
    )

    boundary_counts = (
        df[
            df["is_exact_boundary"]
        ]
        .groupby(
            [
                "nearest_boundary",
                "origin_short_regression",
                "origin_short_from_score"
            ]
        )
        .size()
        .reset_index(
            name="n_observations"
        )
        .sort_values(
            "n_observations",
            ascending=False
        )
    )

    print(
        "\nExact boundary mismatch："
    )

    print(
        boundary_counts.to_string(
            index=False
        )
    )

    # ============================================================
    # 3. Inspect mismatches away from the boundaries.
    # ============================================================

    non_boundary = df[
        ~df["is_exact_boundary"]
    ].copy()

    print("\n" + "=" * 80)
    print("4. 非边界 mismatch")
    print("=" * 80)

    print(
        f"non-boundary mismatch = "
        f"{len(non_boundary):,}"
    )

    if not non_boundary.empty:

        non_boundary_summary = (
            non_boundary.groupby(
                [
                    "origin_short_regression",
                    "origin_short_from_score"
                ]
            )
            .agg(
                n=("user_id", "size"),
                min_score=("date1_average", "min"),
                median_score=("date1_average", "median"),
                max_score=("date1_average", "max"),
                median_distance_to_boundary=(
                    "distance_to_boundary",
                    "median"
                )
            )
            .reset_index()
            .sort_values(
                "n",
                ascending=False
            )
        )

        print(
            non_boundary_summary
            .round(8)
            .to_string(index=False)
        )

    # ============================================================
    # 4. Summarize mismatches by research window.
    # ============================================================

    quarter_summary = (
        df.groupby(
            [
                "quarter1",
                "origin_short_regression",
                "origin_short_from_score"
            ]
        )
        .size()
        .reset_index(
            name="n_observations"
        )
        .sort_values(
            [
                "quarter1",
                "n_observations"
            ],
            ascending=[
                True,
                False
            ]
        )
    )

    print("\n" + "=" * 80)
    print("5. 按季度 mismatch")
    print("=" * 80)

    print(
        quarter_summary.to_string(
            index=False
        )
    )

    df.to_csv(
        out_boundary,
        index=False,
        encoding="utf-8-sig"
    )

    print(
        f"\n[SAVE] summary: {out_summary}"
    )

    print(
        f"[SAVE] boundary detail: {out_boundary}"
    )




if __name__ == "__main__":
    run_regression_matched_bridge_analysis()
    audit_origin_category_mismatches()
