from pathlib import Path as _ReleasePath
import sys as _release_sys
_release_root = next(_p for _p in _ReleasePath(__file__).resolve().parents if (_p / 'runtime_config.py').is_file())
_release_sys.path.insert(0, str(_release_root))
from runtime_config import project_path

# Figure 2c.
    
    
    
    

    # Bias-change and open-mindedness regression workflow, documented on 2026-08-09:
    # Methods stage and corresponding implementation.
    # | --------------------------------------- | -------------------------------------------- |
    # Per-period overall MediaScore: load_total_bias_quarter_from_folders().
    # MediaScore tables for six periods: build_total_bias_by_quarter().
    # Require scores in q and q+1: the inner join in build_bias_change_for_total().
    # | (\Delta MediaScore=Score_{q+1}-Score_q) | `build_bias_change_for_total()`              |
    # Read IdeoP at q: read_openmindness_for_total().
    # Require at least two consumption records in the main analysis.
    # Join starting-period IdeoP to q-to-q+1 changes in run_regression_total().
    # Remove missing and non-finite values in run_regression_total().
    # Apply full-sample IQR filtering to IdeoP first.
    # Apply IQR filtering to Delta MediaScore second.
    # Fit five window pairs by seven starting categories: 35 groups.
    # Require MIN_N_PER_GROUP = 10.
    # | Robust regression                       | `sm.RLM(y,X).fit()`                          |
    # Extract beta_1 from model.params['average_info_openmindness'].
    # Audit processing-stage sample counts with export_total_regression_audit_report().
    # Plot Fig. 2c with plot_regression_slope_bubbles().


# Final total-source regression implementation.

# Analysis logic:
# Relate a user's starting-window open-mindedness to the continuous ideology change from q1 to q2.
# bias_change = intercept + slope × average_info_openmindness + error
# bias_change = average_bias_points at q2 minus average_bias_points at q1.


# Use current-period total open-mindedness as the explanatory variable and adjacent-period ideology change as the response, fitting robust regressions by window pair and starting category.
# Filter low-count, missing and outlying records and audit retained samples. Historical sensitivity analyses considered count thresholds, IQR filtering and OLS/RLM alternatives.

# 1. Number of records read.
# 2. Number retained after merging.
# 3. Number retained after IQR filtering.
# 4. n_obs in each regression group.
# Use these counts to audit sample inclusion across processing stages.
# bias_quarter: total-source user records read for each window.


# Historical audit summary:
# Window, total-bias records and unique-user count.
# 2019_12_2020_01_2020_02      	718,832
# 2020_03_2020_04_2020_05	      818,547
# 2020_06_2020_07_2020_08      	1,200,010
# 2020_09_2020_10      	1,961,638
# 2020_11_2020_12	      1,868,681
# 2021_01_2021_02      	2,188,294

# bias_change: users with scores in both adjacent windows.
# Compute:
# bias_change = average_bias_points at q2 minus average_bias_points at q1.
# A change is defined only when the same user is present in both adjacent windows.
# Historical result summary:
# Window pair and number of users with a defined bias_change.
# Q1 → Q2     	346,977
# Q2 → Q3	     	429,306
# Q3 → Q4	     	701,679
# Q4 → Q5	     	924,026
# Q5 → Q6	     	984,513

# The intersection can be smaller than either single-window user set.
# Historical example: Q1 had 718,832 users and Q2 had 818,547; their intersection contained 346,977 users.
# Historical inspection retained this stage.

# openmindness_after_threshold: observations passing the consumption-count threshold.

# total_appear_count >= 2
# The historical audit contained 42 category/window summary rows:
# Six windows times seven categories equals 42.
# Inspect coverage of all six windows and seven configured categories.
# Open-mindedness records retained per window:
# Window and thresholded open-mindedness sample size.
# 2019_12_2020_01_2020_02    		381,510
# 2020_03_2020_04_2020_05    		577,206
# 2020_06_2020_07_2020_08    		602,003
# 2020_09_2020_10	    	    	1,059,172
# 2020_11_2020_12	    	    	1,006,527
# 2021_01_2021_02	    	    	1,201,381
# This sample requires open-mindedness and total_appear_count >= 2, so it can be smaller than bias_quarter.


# merged_before_cleaning: joined candidate observations for regression.
# Inspect the merged-sample count.
# stage    	    			n_rows	n_users
# merged_before_cleaning	2,838,737	1,003,381
# Across adjacent window pairs, require both:
# Ideology scores at q1 and q2.
# Open-mindedness at q1.
# total_appear_count >= 2
# Historical merged sample: 2,838,737 user-window-pair observations.
# Historical number of unique users: 1,003,381.
# n_rows may exceed n_users because a user can contribute to several adjacent window pairs.

# after_dropna_inf: retained sample after removing missing and infinite values.
# stage	n_rows	n_users
# merged_before_cleaning	2,838,737	1,003,381
# after_dropna_inf	2,838,737	1,003,381
# Interpretation:
# The historical merged sample lost no rows for missing/non-finite bias_change or average_info_openmindness.
# This describes the historical cleaning audit, not a guarantee for new inputs.


# after_iqr: candidate sample after IQR filtering.
# stage	n_rows	n_users
# after_dropna_inf	2,838,737	1,003,381
# after_iqr	2,534,669	906,804
# Historical number of records removed by IQR filtering:
# 2,838,737 - 2,534,669 = 304,068 records.
# Approximately 10.7%.
# The historical filtering removed tail observations in open-mindedness or bias change.



# Directory layout relative to the configured root:
# 1) bias
#    bias/<source>/user_bias_scores_by_quarter/quarterly_user_bias_scores_<quarter>.csv
# Example header:
#    user_id,total_score,appearance_count,average_bias_points

# 2) openmindness（TOTAL）
#    total/<political_bias>/<quarter>_...openmindness_score.csv
# Columns: user_id, total_info_score, total_appear_count, average_score.

# Regression structure:
# Each individual source has five pairs by seven categories: 35 groups.
#   bias_change = (q2 average_bias_points) - (q1 average_bias_points)
# Use q1 average_info_openmindness after the consumption-count filter.
# TOTAL also has five pairs by seven categories: 35 groups.
# Pooled quarterly ideology is sum(total_score) / sum(appearance_count) after aggregation by user_id.
# Then compute adjacent-window bias_change.
# Read total_appear_count and average_score from the total-source open-mindedness table.

# Outputs:
# regression_outputs/
#   regression_results_total.csv


import os
import glob
import numpy as np
import pandas as pd
import statsmodels.api as sm


# ======================
# Analysis parameters.
# ======================
SOURCES = ["external", "twitter", "without"]

QUARTERS = [
    "2019_12_2020_01_2020_02",
    "2020_03_2020_04_2020_05",
    "2020_06_2020_07_2020_08",
    "2020_09_2020_10",
    "2020_11_2020_12",
    "2021_01_2021_02"
]

POLITICAL_BIAS_FOLDERS = [
    "extreme_left",
    "left",
    "left_leaning",
    "center",
    "right_leaning",
    "right",
    "extreme_right"
]

# Open-mindedness inclusion threshold: count >= this value.
APPEAR_COUNT_THRESHOLD = 3

# Use one suffix consistently for this analysis profile's outputs.
OUTPUT_SUFFIX = f"appear_ge_{APPEAR_COUNT_THRESHOLD}"

# Skip regression fits below this group size, while retaining a result row.
MIN_N_PER_GROUP = 10

# Enable the existing IQR outlier filter.
USE_IQR_OUTLIER_FILTER = True

# Debug-output settings.
DEBUG_PRINT_HEAD_ROWS = 5
DEBUG_PRINT_XY_EXAMPLES = True
DEBUG_MAX_GROUP_EXAMPLES = 8


# ======================
# Configure paths.
# ======================
# multiplication_parameter = r"参数1点5"
ROOT_DIR = project_path('data', 'intermediate/Openmindness/media/连续的/total')   # Directory for total-source regression outputs.


OUT_DIR = os.path.join(ROOT_DIR, "regression_outputs")
os.makedirs(OUT_DIR, exist_ok=True)

# ======================
# Run total-source regressions only.
# ======================

# Total-source continuous quarterly user-ideology data.
TOTAL_BIAS_ROOT = project_path('outputs', 'analyses/Average_Bias_Rating/media_average_rating/total_url-rating/user_bias_scores_by_quarter')

# Total-source open-mindedness data.
TOTAL_OPENMINDNESS_ROOT = project_path('data', 'intermediate/Openmindness/media/连续的/total')   # Read total-source ideological-permeability values here.

# ======================
# Helper functions.
# ======================
def remove_outliers_iqr(df: pd.DataFrame, column: str) -> pd.DataFrame:
    if df.empty:
        return df
    Q1 = df[column].quantile(0.25)
    Q3 = df[column].quantile(0.75)
    IQR = Q3 - Q1
    if pd.isna(IQR) or IQR == 0:
        return df
    lower = Q1 - 1.5 * IQR
    upper = Q3 + 1.5 * IQR
    return df[(df[column] >= lower) & (df[column] <= upper)]




def find_total_bias_file(quarter: str, political_bias: str) -> str:
    'Find a total-source quarterly user-score file in a category directory.\n    \n    Expected root:\n    <configured external path>\n    \n    Category folders: extreme_left, left, left_leaning, center, right_leaning,\n    right and extreme_right.\n    '

    folder_path = os.path.join(TOTAL_BIAS_ROOT, political_bias)

    if not os.path.isdir(folder_path):
        print(f"[WARN-total-bias] 缺少 total bias 文件夹: {folder_path}")
        return ""

    # Prefer the exact expected file-name format.
    exact = os.path.join(folder_path, f"{quarter}_{political_bias}_user.csv")

    if os.path.exists(exact):
        return exact

    # Fallback: choose a CSV whose name begins with the window identifier.
    cand = glob.glob(os.path.join(folder_path, f"{quarter}*.csv"))

    return cand[0] if cand else ""


def load_total_bias_quarter_from_folders(quarter: str) -> pd.DataFrame:
    """Read and combine continuous total-source scores from seven category folders.
    
    Return user_id and average_bias_points for the requested research window.
    """

    parts = []

    for political_bias in POLITICAL_BIAS_FOLDERS:
        fp = find_total_bias_file(quarter, political_bias)

        if not fp:
            print(f"[WARN-total-bias] 找不到 total | {political_bias} | {quarter} 的 bias 文件")
            continue

        print(f"[READ-total-bias] {quarter} | {political_bias} -> {os.path.basename(fp)}")

        try:
            df = pd.read_csv(fp)
        except Exception as e:
            print(f"[WARN-total-bias] 读取失败: {fp} | {e}")
            continue

        if df.empty:
            continue

        if "user_id" not in df.columns:
            print(f"[WARN-total-bias] 文件缺少 user_id: {fp}")
            continue

        if "average_bias_points" not in df.columns:
            print(f"[WARN-total-bias] 文件缺少 average_bias_points: {fp}")
            continue

        out = df[["user_id", "average_bias_points"]].copy()
        out["user_id"] = out["user_id"].astype(str)
        out["average_bias_points"] = pd.to_numeric(
            out["average_bias_points"],
            errors="coerce"
        )

        out = out.dropna(subset=["average_bias_points"])

        if not out.empty:
            parts.append(out)

    if not parts:
        return pd.DataFrame(columns=["user_id", "average_bias_points"])

    result = pd.concat(parts, ignore_index=True)

    # Each user should belong to only one total-source category folder per window.
    dup_n = result.duplicated(subset=["user_id"]).sum()

    if dup_n > 0:
        print(f"[WARN-total-bias] {quarter} 存在重复 user_id = {dup_n:,}，将保留第一条")
        result = result.drop_duplicates(subset=["user_id"], keep="first")

    print(f"[OK-total-bias] {quarter} total 用户数: {len(result):,}")

    return result

def build_total_bias_by_quarter() -> dict:
    """Load existing total_url-rating quarterly scores.
    
    Do not rebuild pooled External/Twitter/Without scores in this function.
    """

    quarter_to_df = {}

    for q in QUARTERS:
        quarter_df = load_total_bias_quarter_from_folders(q)

        if quarter_df.empty:
            print(f"[WARN-total-bias] {q} total 季度政治倾向数据为空")
            quarter_to_df[q] = pd.DataFrame(columns=["user_id", "average_bias_points"])
            continue

        quarter_to_df[q] = quarter_df

    return quarter_to_df

# build_bias_change_for_total constructs the regression response.
# Require valid MediaScore values at both q and q+1.
def build_bias_change_for_total() -> pd.DataFrame:
    quarter_to_df = build_total_bias_by_quarter()
    pairs = [(QUARTERS[i], QUARTERS[i + 1]) for i in range(len(QUARTERS) - 1)]
    all_rows = []

    for q1, q2 in pairs:
        d1 = quarter_to_df.get(q1, pd.DataFrame())
        d2 = quarter_to_df.get(q2, pd.DataFrame())

        if d1.empty or d2.empty:
            print(f"[SKIP-total-bias] {q1}_to_{q2} pooled季度为空，跳过")
            continue

        merged = pd.merge(d1, d2, on="user_id", how="inner", suffixes=("_q1", "_q2"))
        if merged.empty:
            print(f"[SKIP-total-bias] {q1}_to_{q2} pooled无共同用户")
            continue

        merged["bias_change"] = merged["average_bias_points_q2"] - merged["average_bias_points_q1"]
        merged["quarter1"] = q1
        merged["quarter2"] = q2
        merged["quarter_pair"] = f"{q1}_to_{q2}"

        out = merged[["user_id", "quarter1", "quarter2", "quarter_pair", "bias_change"]].copy()
        all_rows.append(out)
        print(f"[OK-total-bias] {q1}_to_{q2} pooled common_users={len(out):,}")

    if not all_rows:
        return pd.DataFrame(columns=["user_id", "quarter1", "quarter2", "quarter_pair", "bias_change"])

    bias_df = pd.concat(all_rows, ignore_index=True)
    bias_df["user_id"] = bias_df["user_id"].astype(str)
    bias_df["bias_change"] = pd.to_numeric(bias_df["bias_change"], errors="coerce")
    bias_df = bias_df.dropna(subset=["user_id", "quarter1", "quarter_pair", "bias_change"])
    return bias_df



def read_openmindness_for_total() -> pd.DataFrame:
    "Read combined user-quarter IdeoP with total-media quarterly categories.\n    \n    Input:\n    <configured external path>\n    \n    Input columns: quarter, user_id, bias, total_info_score, total_appear_count,\n    average_score. Output columns: user_id, average_info_openmindness,\n    political_bias, quarter.\n    \n    average_info_openmindness represents IdeoP(u,q); political_bias is the user's\n    total-media category at q. APPEAR_COUNT_THRESHOLD filters consumption at q.\n    "

    file_path = os.path.join(
        TOTAL_OPENMINDNESS_ROOT,
        'plots_ridgeline_correct_total/plot_data_total_correct.csv'
    )

    if not os.path.exists(file_path):
        raise FileNotFoundError(
            f"找不到正确的 total 观念开放程度文件：{file_path}"
        )

    print(f"[READ-open-total] 读取：{file_path}")

    # Read only regression-required columns to reduce memory use.
    data = pd.read_csv(
        file_path,
        usecols=[
            "quarter",
            "user_id",
            "bias",
            "total_info_score",
            "total_appear_count",
            "average_score"
        ],
        dtype={
            "quarter": str,
            "user_id": str,
            "bias": str
        }
    )

    data.columns = data.columns.str.strip()

    print(
        f"[CHECK-open-total] 原始总行数：{len(data):,}，"
        f"不同用户数：{data['user_id'].nunique():,}"
    )

    # =========================
    # 1. Clean string fields.
    # =========================
    data["quarter"] = data["quarter"].str.strip()
    data["user_id"] = data["user_id"].str.strip()
    data["bias"] = data["bias"].str.strip()

    # =========================
    # 2. Convert numeric fields.
    # =========================
    data["total_info_score"] = pd.to_numeric(
        data["total_info_score"],
        errors="coerce"
    )

    data["total_appear_count"] = pd.to_numeric(
        data["total_appear_count"],
        errors="coerce"
    )

    data["average_score"] = pd.to_numeric(
        data["average_score"],
        errors="coerce"
    )

    # =========================
    # 3. Drop records missing required fields.
    # =========================
    before_dropna = len(data)

    data = data.dropna(
        subset=[
            "quarter",
            "user_id",
            "bias",
            "total_info_score",
            "total_appear_count",
            "average_score"
        ]
    ).copy()

    # Remove empty strings.
    data = data[
        (data["quarter"] != "")
        & (data["user_id"] != "")
        & (data["bias"] != "")
        & (data["user_id"].str.lower() != "nan")
        & (data["bias"].str.lower() != "nan")
    ].copy()

    print(
        f"[CHECK-open-total] 删除缺失值："
        f"{before_dropna:,} -> {len(data):,}"
    )

    # =========================
    # 4. Keep configured windows and seven political categories.
    # =========================
    invalid_quarter_mask = ~data["quarter"].isin(QUARTERS)
    invalid_quarter_count = int(invalid_quarter_mask.sum())

    if invalid_quarter_count > 0:
        print(
            f"[WARN-open-total] 存在 {invalid_quarter_count:,} 条"
            "未识别季度记录，将删除。"
        )

    invalid_bias_mask = ~data["bias"].isin(
        POLITICAL_BIAS_FOLDERS
    )
    invalid_bias_count = int(invalid_bias_mask.sum())

    if invalid_bias_count > 0:
        print(
            f"[WARN-open-total] 存在 {invalid_bias_count:,} 条"
            "未识别政治倾向记录，将删除："
        )

        print(
            data.loc[invalid_bias_mask, "bias"]
            .value_counts(dropna=False)
        )

    data = data[
        data["quarter"].isin(QUARTERS)
        & data["bias"].isin(POLITICAL_BIAS_FOLDERS)
    ].copy()

    # =========================
    # 5. Validate user-quarter uniqueness.
    # =========================
    # In the total-source open-mindedness table,
    # each user must have one record per window.
    duplicate_mask = data.duplicated(
        subset=["user_id", "quarter"],
        keep=False
    )

    duplicate_count = int(duplicate_mask.sum())

    if duplicate_count > 0:
        duplicate_path = os.path.join(
            OUT_DIR,
            "duplicate_total_openmindness_user_quarter.csv"
        )

        duplicate_df = (
            data.loc[duplicate_mask]
            .sort_values(
                ["quarter", "user_id", "bias"]
            )
        )

        duplicate_df.to_csv(
            duplicate_path,
            index=False,
            encoding="utf-8-sig"
        )

        raise ValueError(
            f"发现 {duplicate_count:,} 条重复的用户—季度记录。"
            "正确的 total 数据中，每个用户每季度只能出现一次。"
            f"重复明细已保存至：{duplicate_path}"
        )

    print(
        "[CHECK-open-total] 用户—季度唯一性检查通过，"
        "没有重复记录。"
    )

    # =========================
    # 6. Validate the average_score calculation.
    # =========================
    calculated_average = (
        data["total_info_score"]
        / data["total_appear_count"]
    )

    valid_denominator_mask = (
        data["total_appear_count"] > 0
    )

    inconsistent_mask = (
        valid_denominator_mask
        & ~np.isclose(
            data["average_score"],
            calculated_average,
            rtol=1e-10,
            atol=1e-12,
            equal_nan=False
        )
    )

    inconsistent_count = int(inconsistent_mask.sum())

    if inconsistent_count > 0:
        inconsistent_path = os.path.join(
            OUT_DIR,
            "inconsistent_total_openmindness_average.csv"
        )

        inconsistent_df = data.loc[
            inconsistent_mask
        ].copy()

        inconsistent_df["calculated_average_score"] = (
            calculated_average.loc[inconsistent_mask]
        )

        inconsistent_df.to_csv(
            inconsistent_path,
            index=False,
            encoding="utf-8-sig"
        )

        print(
            f"[WARN-open-total] 发现 {inconsistent_count:,} 条 "
            "average_score 与 total_info_score / "
            "total_appear_count 不一致的记录。"
        )

        print(
            "[WARN-open-total] 将使用 total_info_score / "
            "total_appear_count 重新计算。"
        )

        data.loc[
            valid_denominator_mask,
            "average_score"
        ] = calculated_average.loc[
            valid_denominator_mask
        ]

    # =========================
    # 7. Remove invalid counts and non-finite values.
    # =========================
    invalid_numeric_mask = (
        (data["total_appear_count"] <= 0)
        | ~np.isfinite(data["total_info_score"])
        | ~np.isfinite(data["total_appear_count"])
        | ~np.isfinite(data["average_score"])
    )

    invalid_numeric_count = int(
        invalid_numeric_mask.sum()
    )

    if invalid_numeric_count > 0:
        print(
            f"[WARN-open-total] 删除 {invalid_numeric_count:,} 条"
            "次数非正或数值非有限的记录。"
        )

    data = data.loc[
        ~invalid_numeric_mask
    ].copy()

    # =========================
    # 8. Apply the main consumption-count threshold.
    # =========================
    before_threshold = len(data)

    data = data[
        data["total_appear_count"]
        >= APPEAR_COUNT_THRESHOLD
    ].copy()

    print(
        f"[CHECK-open-total] total_appear_count >= "
        f"{APPEAR_COUNT_THRESHOLD}："
        f"{before_threshold:,} -> {len(data):,}"
    )

    print(
        "[CHECK-open-total] 阈值筛选后的消费次数总和："
        f"{data['total_appear_count'].sum():,.0f}"
    )

    # =========================
    # 9. Report retained sample counts by window.
    # =========================
    quarter_stats = (
        data.groupby("quarter")
        .agg(
            n_rows=("user_id", "size"),
            n_users=("user_id", "nunique"),
            total_appear_count=(
                "total_appear_count",
                "sum"
            )
        )
        .reindex(QUARTERS)
    )

    print(
        "\n[CHECK-open-total] "
        "各季度阈值筛选后样本数："
    )
    print(quarter_stats.to_string())

    # =========================
    # 10. Rename columns to the regression interface.
    # =========================
    out = data[
        [
            "user_id",
            "average_score",
            "bias",
            "quarter"
        ]
    ].copy()

    out.columns = [
        "user_id",
        "average_info_openmindness",
        "political_bias",
        "quarter"
    ]

    # Confirm uniqueness of the final output once more.
    final_duplicate_count = int(
        out.duplicated(
            subset=["user_id", "quarter"]
        ).sum()
    )

    if final_duplicate_count > 0:
        raise ValueError(
            "[ERROR-open-total] 输出数据仍存在重复的"
            " user_id + quarter。"
        )

    print(
        f"\n[OK-open-total] 最终读取完成："
        f"{len(out):,} 条用户—季度记录。"
    )

    return out




def export_total_regression_audit_report():
    """Export sample-count audits for the total-source regression.
    
    Report quarterly total-bias counts, window/category IdeoP counts, bias-change
    counts, joined counts, counts before/after IQR filtering, and final counts
    for each quarter_pair/political_bias group.
    """

    audit_rows = []

    # 1. Read total-source bias for each window.
    quarter_to_bias = build_total_bias_by_quarter()

    for q, df_q in quarter_to_bias.items():
        audit_rows.append({
            "stage": "bias_quarter",
            "quarter": q,
            "quarter_pair": "",
            "political_bias": "",
            "n_rows": len(df_q),
            "n_users": df_q["user_id"].nunique() if not df_q.empty else 0
        })

    # 2. Construct bias_change.
    bias_df = build_bias_change_for_total()

    if not bias_df.empty:
        tmp = (
            bias_df.groupby("quarter_pair")
            .agg(n_rows=("user_id", "size"), n_users=("user_id", "nunique"))
            .reset_index()
        )

        for _, row in tmp.iterrows():
            audit_rows.append({
                "stage": "bias_change",
                "quarter": "",
                "quarter_pair": row["quarter_pair"],
                "political_bias": "",
                "n_rows": row["n_rows"],
                "n_users": row["n_users"]
            })

    # 3. Read open-mindedness.
    open_df = read_openmindness_for_total()

    if not open_df.empty:
        tmp = (
            open_df.groupby(["quarter", "political_bias"])
            .agg(n_rows=("user_id", "size"), n_users=("user_id", "nunique"))
            .reset_index()
        )

        for _, row in tmp.iterrows():
            audit_rows.append({
                "stage": "openmindness_after_threshold",
                "quarter": row["quarter"],
                "quarter_pair": "",
                "political_bias": row["political_bias"],
                "n_rows": row["n_rows"],
                "n_users": row["n_users"]
            })

    # 4. Join bias_change to q1 open-mindedness.
    merged_df = pd.merge(
        bias_df,
        open_df,
        left_on=["user_id", "quarter1"],
        right_on=["user_id", "quarter"],
        how="inner"
    ).drop(columns=["quarter"])

    audit_rows.append({
        "stage": "merged_before_cleaning",
        "quarter": "",
        "quarter_pair": "ALL",
        "political_bias": "ALL",
        "n_rows": len(merged_df),
        "n_users": merged_df["user_id"].nunique() if not merged_df.empty else 0
    })

    if not merged_df.empty:
        # 5. Count records before cleaning.
        merged_df["average_info_openmindness"] = pd.to_numeric(
            merged_df["average_info_openmindness"],
            errors="coerce"
        )
        merged_df["bias_change"] = pd.to_numeric(
            merged_df["bias_change"],
            errors="coerce"
        )

        before_dropna = len(merged_df)

        cleaned_df = merged_df.dropna(
            subset=[
                "bias_change",
                "average_info_openmindness",
                "political_bias",
                "quarter_pair"
            ]
        )

        cleaned_df = cleaned_df[
            ~cleaned_df.isin([np.inf, -np.inf]).any(axis=1)
        ]

        audit_rows.append({
            "stage": "after_dropna_inf",
            "quarter": "",
            "quarter_pair": "ALL",
            "political_bias": "ALL",
            "n_rows": len(cleaned_df),
            "n_users": cleaned_df["user_id"].nunique() if not cleaned_df.empty else 0
        })

        # 6. Count each group before IQR filtering.
        tmp = (
            cleaned_df.groupby(["quarter_pair", "political_bias"])
            .agg(n_rows=("user_id", "size"), n_users=("user_id", "nunique"))
            .reset_index()
        )

        for _, row in tmp.iterrows():
            audit_rows.append({
                "stage": "group_before_iqr",
                "quarter": "",
                "quarter_pair": row["quarter_pair"],
                "political_bias": row["political_bias"],
                "n_rows": row["n_rows"],
                "n_users": row["n_users"]
            })

        # 7. Count records after IQR filtering.
        if USE_IQR_OUTLIER_FILTER:
            iqr_df = remove_outliers_iqr(cleaned_df, "average_info_openmindness")
            iqr_df = remove_outliers_iqr(iqr_df, "bias_change")
        else:
            iqr_df = cleaned_df.copy()

        audit_rows.append({
            "stage": "after_iqr",
            "quarter": "",
            "quarter_pair": "ALL",
            "political_bias": "ALL",
            "n_rows": len(iqr_df),
            "n_users": iqr_df["user_id"].nunique() if not iqr_df.empty else 0
        })

        tmp = (
            iqr_df.groupby(["quarter_pair", "political_bias"])
            .agg(n_rows=("user_id", "size"), n_users=("user_id", "nunique"))
            .reset_index()
        )

        for _, row in tmp.iterrows():
            audit_rows.append({
                "stage": "group_after_iqr_final_regression_sample",
                "quarter": "",
                "quarter_pair": row["quarter_pair"],
                "political_bias": row["political_bias"],
                "n_rows": row["n_rows"],
                "n_users": row["n_users"]
            })

    audit_df = pd.DataFrame(audit_rows)

    audit_path = os.path.join(
        OUT_DIR,
        f"regression_total_data_audit_report_{OUTPUT_SUFFIX}.csv"
    )

    audit_df.to_csv(audit_path, index=False, encoding="utf-8-sig")

    print(f"[AUDIT DONE] 已保存数据审计报告：{audit_path}")




# ======================
# Total-source regression: run_regression_total produces the paper's regression results.
# ======================
def run_regression_total() -> pd.DataFrame:
    print(f"\n==============================")
    print(f"开始处理：TOTAL（pooled bias + total openmindness）")
    print(f"==============================")

    bias_df = build_bias_change_for_total()
    print(f"[CHECK] total bias_change 总行数: {len(bias_df):,}")
    print(f"[CHECK] total bias_change 不同用户数（仅统计）: {bias_df['user_id'].nunique():,}")
    if not bias_df.empty:
        print("[CHECK] total bias_change head：")
        print(bias_df.head(DEBUG_PRINT_HEAD_ROWS).to_string(index=False))
    if bias_df.empty:
        return pd.DataFrame()

    open_df = read_openmindness_for_total()
    print(f"[CHECK] total openmindness 总行数: {len(open_df):,}")
    print(f"[CHECK] total openmindness 不同用户数（仅统计）: {open_df['user_id'].nunique():,}")
    if not open_df.empty:
        print("[CHECK] total openmindness head：")
        print(open_df.head(DEBUG_PRINT_HEAD_ROWS).to_string(index=False))
    if open_df.empty:
        return pd.DataFrame()

    merged_df = pd.merge(
        bias_df,
        open_df,
        left_on=["user_id", "quarter1"],
        right_on=["user_id", "quarter"],
        how="inner"
    ).drop(columns=["quarter"])

    print(f"[CHECK] total merge 后样本行数: {len(merged_df):,}")
    print(f"[CHECK] total merge 后不同用户数（仅统计）: {merged_df['user_id'].nunique():,}")
    if merged_df.empty:
        return pd.DataFrame()

    merged_df["average_info_openmindness"] = pd.to_numeric(merged_df["average_info_openmindness"], errors="coerce")
    merged_df["bias_change"] = pd.to_numeric(merged_df["bias_change"], errors="coerce")
    merged_df = merged_df.dropna(subset=["bias_change", "average_info_openmindness", "political_bias", "quarter_pair"])
    merged_df = merged_df[~merged_df.isin([np.inf, -np.inf]).any(axis=1)]

    if USE_IQR_OUTLIER_FILTER:
        before = len(merged_df)
        merged_df = remove_outliers_iqr(merged_df, "average_info_openmindness")
        merged_df = remove_outliers_iqr(merged_df, "bias_change")
        after = len(merged_df)
        print(f"[CHECK] total IQR：{before:,} -> {after:,}")

    fixed_quarter_pairs = [f"{QUARTERS[i]}_to_{QUARTERS[i+1]}" for i in range(len(QUARTERS) - 1)]
    fixed_biases = POLITICAL_BIAS_FOLDERS

    results = []
    printed = 0

    for qp in fixed_quarter_pairs:
        for pb in fixed_biases:
            sub = merged_df[(merged_df["quarter_pair"] == qp) & (merged_df["political_bias"] == pb)]
            n = len(sub)

            if DEBUG_PRINT_XY_EXAMPLES and n > 0 and printed < DEBUG_MAX_GROUP_EXAMPLES:
                print(f"\n[EXAMPLE] total | {qp} | {pb} | n={n:,}")
                print(sub[["user_id", "average_info_openmindness", "bias_change"]]
                      .head(DEBUG_PRINT_HEAD_ROWS).to_string(index=False))
                printed += 1

            if n < MIN_N_PER_GROUP:
                results.append({
                    "source": "total", "quarter_pair": qp, "political_bias": pb,
                    "intercept": np.nan, "slope": np.nan, "p_value": np.nan,
                    "n_obs": n, "rsquared": np.nan, "status": "skipped_n_too_small"
                })
                continue

            X = sm.add_constant(sub[["average_info_openmindness"]])
            y = sub["bias_change"]

            try:
                model = sm.RLM(y, X).fit()
                denom = ((y - y.mean()) ** 2).sum()
                rsq = np.nan if denom == 0 else 1 - (model.resid ** 2).sum() / denom

                results.append({
                    "source": "total", "quarter_pair": qp, "political_bias": pb,
                    "intercept": model.params.get("const", np.nan),
                    "slope": model.params.get("average_info_openmindness", np.nan),
                    "p_value": model.pvalues.get("average_info_openmindness", np.nan),
                    "n_obs": n, "rsquared": rsq, "status": "ok"
                })
                print(f"[OK] total {qp} {pb} n={n:,} slope={model.params.get('average_info_openmindness', np.nan):.6f}")

            except Exception as e:
                results.append({
                    "source": "total", "quarter_pair": qp, "political_bias": pb,
                    "intercept": np.nan, "slope": np.nan, "p_value": np.nan,
                    "n_obs": n, "rsquared": np.nan, "status": f"failed: {e}"
                })
                print(f"[FAIL] total {qp} {pb}: {e}")

    res = pd.DataFrame(results)
    out_path = os.path.join(
        OUT_DIR,
        f"regression_results_total_{OUTPUT_SUFFIX}.csv"
    )
    res.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"[DONE] 保存：{out_path}  行数={len(res)}（应为35）")
    return res


def main():
    export_total_regression_audit_report() # Audit the data used for the results.
    run_regression_total() # Run the core regression calculation.
    print("\nTOTAL 回归和数据审计完成。")



import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import seaborn as sns
from matplotlib import rcParams
# Historical figure reference for this plotting block.
def plot_regression_slope_bubbles():
    # 1. Configure the base plot styling.
    try:
        plt.style.use('seaborn-v0_8')
    except:
        plt.style.use('ggplot')

    rcParams.update({
        'font.sans-serif': ['SimHei', 'Arial Unicode MS', 'DejaVu Sans'],
        'axes.unicode_minus': False,
        'font.size': 10,
        'axes.labelsize': 11,
        'xtick.labelsize': 9,
        'ytick.labelsize': 10
    })

    def to_plt_color(rgb_str):
        colors = [int(x) / 255.0 for x in rgb_str.replace('rgb(', '').replace(')', '').split(',')]
        return tuple(colors)

    node_color_config = {
        'left': 'rgb(51, 102, 153)',
        'left_leaning': 'rgb(181, 216, 243)',
        'center': 'rgb(240, 230, 140)',
        'right_leaning': 'rgb(255, 153, 153)',
        'right': 'rgb(204, 102, 102)',
        'extreme_right': 'rgb(139, 26, 26)',
    }
    plt_color_map = {k: to_plt_color(v) for k, v in node_color_config.items()}

    # 2. Read the regression output.
    file_path = os.path.join(
        OUT_DIR,
        f"regression_results_total_{OUTPUT_SUFFIX}.csv"
    )    # Directory containing regression results for plotting.
    

    try:
        # Specify the encoding and strip column-name whitespace.
        df = pd.read_csv(file_path, encoding='utf-8-sig')
        df.columns = df.columns.str.strip() 
    except Exception as e:
        print(f"❌ 读取文件失败: {e}")
        return

    # Strip cell whitespace so category matching is consistent.
    for col in ['political_bias', 'quarter_pair']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    # Convert plot variables to numeric; unparseable values become NaN.
    for col in ['slope', 'p_value', 'n_obs']:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # Convert slopes to the displayed scale.
    # Multiply raw decimal slopes, such as 0.02, by 1000 for this display scale.
    # Do not apply this display conversion again to data already expressed in the displayed units.
    df['slope'] = df['slope'] * 1000 

    # Filter the plotting data.
    df = df[df['political_bias'] != 'extreme_left'].copy()
    df = df.dropna(subset=['political_bias', 'slope']) # Remove observations that could not be read as numeric.

    quarter_order = [
        '2019_12_2020_01_2020_02_to_2020_03_2020_04_2020_05',
        '2020_03_2020_04_2020_05_to_2020_06_2020_07_2020_08',
        '2020_06_2020_07_2020_08_to_2020_09_2020_10',
        '2020_09_2020_10_to_2020_11_2020_12',
        '2020_11_2020_12_to_2021_01_2021_02'
    ]
    quarter_labels = ['Q1→Q2', 'Q2→Q3', 'Q3→Q4', 'Q4→Q5', 'Q5→Q6']
    bias_order = ['left', 'left_leaning', 'center', 'right_leaning', 'right', 'extreme_right']

    # Compute x-axis positions.
    # Handle unmatched quarter_pair identifiers.
    def get_x_pos(row):
        try:
            b_idx = bias_order.index(row['political_bias'])
            q_idx = quarter_order.index(row['quarter_pair'])
            return b_idx + (q_idx - len(quarter_order) / 2 + 0.5) * 0.15
        except:
            return np.nan

    df['x_pos'] = df.apply(get_x_pos, axis=1)
    df = df.dropna(subset=['x_pos']) # Drop rows whose window-pair identifiers do not match the configured list.

    if df.empty:
        print("⚠️ 警告：过滤后数据为空！请检查 quarter_pair 的字符串内容是否与代码中定义的完全一致。")
        return

    # 3. Plot the figure.
    fig, ax = plt.subplots(figsize=(14, 8))

    MIN_BUBBLE_SIZE = 100 
    MAX_BUBBLE_SIZE = 800
    n_min, n_max = df['n_obs'].min(), df['n_obs'].max()

    for i, bias in enumerate(bias_order):
        ax.axvspan(i - 0.5, i + 0.5, facecolor=plt_color_map[bias], alpha=0.18, zorder=0)
        # Position the annotation at 0.95 of the axes height.
        # ax.text(i, 0.95, bias.replace('_', ' ').title(), ha='center', va='center', 
        #         color=plt_color_map[bias], fontweight='bold', fontsize=12,
        #         transform=ax.get_xaxis_transform())

        subset = df[df['political_bias'] == bias]
        if subset.empty: continue
        
        current_bubble_sizes = np.interp(subset['n_obs'], [n_min, n_max], [MIN_BUBBLE_SIZE, MAX_BUBBLE_SIZE])
        
        ax.scatter(
            subset['x_pos'], subset['slope'],
            s=current_bubble_sizes,
            c=[plt_color_map[bias]],
            alpha=0.9,
            edgecolors='white',
            linewidth=1.0,
            zorder=3
        )

        for _, row in subset.iterrows():
            sig = '*' if row['p_value'] < 0.05 else 'NS'
            ax.text(row['x_pos'], row['slope'], sig,
                    ha='center', va='center', fontsize=8, color='black', fontweight='bold', zorder=4)

    # 4. Refine plot details.
    # Use a light-red dashed reference line.
    ax.axhline(0, color='#FF9999', linestyle='--', alpha=0.8, linewidth=1.5, zorder=2)
    
    # Set the y-axis range dynamically.
    y_max = max(df['slope'].abs().max() * 1.2, 50) 
    ax.set_ylim(-y_max, y_max)
    ax.set_xlim(-0.5, len(bias_order) - 0.5)
    
    ax.grid(axis='y', color='white', linestyle='--', alpha=0.6, zorder=1)
    ax.set_facecolor('#F8F9FA') 
    for spine in ['top', 'right', 'bottom', 'left']:
        ax.spines[spine].set_visible(False)

    # Generate x-axis ticks.
    all_x_ticks = []
    all_x_labels = []
    for i, _ in enumerate(bias_order):
        for q_idx, q_label in enumerate(quarter_labels):
            pos = i + (q_idx - len(quarter_order) / 2 + 0.5) * 0.15
            all_x_ticks.append(pos)
            all_x_labels.append(q_label)
    
    ax.set_xticks(all_x_ticks)
    ax.set_xticklabels(all_x_labels, rotation=90, fontsize=8)

    ax.set_ylabel('回归斜率 (Slope × 1000)', labelpad=15, fontweight='bold')
    # ax.set_title('Open-mindedness and bias change (Updated Data)', pad=40)

    plt.tight_layout()
    
    output_dir = os.path.dirname(file_path)
    save_path = os.path.join(
        output_dir,
        f"slope_bubble_final_{OUTPUT_SUFFIX}.png"
    )
    plt.savefig(save_path, format='png', dpi=1200, bbox_inches='tight')
    
    print(f"✅ 绘图完成。有效数据点数量: {len(df)}")
    print(f"✅ 高清图片已保存至: {save_path}")
    plt.show()



if __name__ == "__main__":
    # Historical note: the Figure 2c workflow was rerun on 2026-08-10.
    main()  # Regression stage.
    plot_regression_slope_bubbles()
    