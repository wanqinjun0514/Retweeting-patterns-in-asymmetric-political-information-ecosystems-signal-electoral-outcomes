from pathlib import Path as _ReleasePath
import sys as _release_sys
_release_root = next(_p for _p in _ReleasePath(__file__).resolve().parents if (_p / 'runtime_config.py').is_file())
_release_sys.path.insert(0, str(_release_root))
from runtime_config import project_path

import os
import time

import numpy as np
import pandas as pd
import plotly.io as pio
import plotly.express as px

from sklearn.metrics import (
    roc_curve,
    roc_auc_score,
    accuracy_score,
    balanced_accuracy_score,
    confusion_matrix,
)

try:
    from tqdm.auto import tqdm
except ImportError:
    tqdm = None

# Replace the historical fixed 0.3 cutoff with a ROC/Youden-J threshold.
# J=Sensitivity+Specificity−1
# Choose the finite normalized-score threshold maximizing J to separate predicted red and blue states.


# Compare the state social-media indicator with 2020 presidential-election outcomes.
def evaluate_state_scores_and_plot_map():
    """Evaluate state social-media ideology indicators and plot the Figure 5a map.
    
    Read each state's '归一化比例' and actual 2020 presidential vote percentages.
    Assign actual Blue/Red outcomes from Biden/Trump percentages. Select the
    finite ROC threshold maximizing Youden's J and classify the state scores.
    Report agreement, balanced accuracy and ROC AUC; also perform
    leave-one-state-out threshold evaluation. Draw the map using the selected
    threshold and preserve the existing input/output schemas.
    """

    # ============================================================
    # 0. Configure paths.
    # ============================================================

    score_path = (
        project_path('outputs', 'analyses/Geographic Results/图5a_20260813/all time every state user bias proportion_删除三个州.csv')
    )

    vote_path = (
        project_path('outputs', 'analyses/Geographic Results/图5a_20260813/2020_presidential_vote_results.csv')
    )

    save_pdf_path = (
        project_path('outputs', 'analyses/Geographic Results/图5a_20260813/图4a_美国地图.pdf')
    )

    save_compare_path = (
        project_path('outputs', 'analyses/Geographic Results/图5a_20260813/图5a_州级指标与2020真实选举结果对比.csv')
    )

    # ============================================================
    # 1. Initialize progress reporting and timing.
    # ============================================================

    t_all = time.perf_counter()

    pbar = (
        tqdm(
            total=6,
            desc="图5a 美国地图",
            unit="步",
            dynamic_ncols=True
        )
        if tqdm else None
    )

    if pbar is None:
        print("[图5a] 未安装 tqdm，仅打印各步耗时。")

    t_step = time.perf_counter()

    def _end_step(label):
        nonlocal t_step

        dt = time.perf_counter() - t_step

        if pbar is not None:
            pbar.update(1)
            pbar.set_postfix_str(f"{label} {dt:.2f}s")
        else:
            print(
                f"[图5a] {label}: "
                f"本步 {dt:.2f}s | "
                f"累计 {time.perf_counter() - t_all:.2f}s"
            )

        t_step = time.perf_counter()

    # ============================================================
    # 2. Read CSVs using encoding fallbacks.
    # ============================================================

    def _read_csv_auto(path):

        encodings = [
            "utf-8-sig",
            "utf-8",
            "gb18030",
            "gbk"
        ]

        last_error = None

        for encoding in encodings:

            try:
                return pd.read_csv(
                    path,
                    encoding=encoding
                )

            except UnicodeDecodeError as e:
                last_error = e

        raise last_error

    # ============================================================
    # 3. Read state-level social-media indicators.
    # ============================================================

    df_scores = _read_csv_auto(score_path)

    df_scores["归一化比例"] = pd.to_numeric(
        df_scores["归一化比例"],
        errors="coerce"
    )

    df_scores["州全称"] = (
        df_scores["州全称"]
        .astype(str)
        .str.strip()
    )

    # The original District of Columbia abbreviation is missing.
    # Fill it with DC for Plotly state-map matching.
    df_scores.loc[
        df_scores["州全称"] == "District of Columbia",
        "州"
    ] = "DC"

    _end_step("读取州级政治倾向数据")

    # ============================================================
    # 4. Read the actual 2020 presidential-election results.
    # ============================================================

    df_vote = _read_csv_auto(vote_path)

    df_vote["State"] = (
        df_vote["State"]
        .astype(str)
        .str.strip()
    )

    df_vote["Biden Percentage"] = pd.to_numeric(
        df_vote["Biden Percentage"],
        errors="coerce"
    )

    df_vote["Trump Percentage"] = pd.to_numeric(
        df_vote["Trump Percentage"],
        errors="coerce"
    )

    # Assign red/blue outcomes from the recorded vote percentages.
    # Biden > Trump → Blue
    # Trump > Biden → Red
    df_vote["真实结果"] = np.where(
        df_vote["Biden Percentage"]
        >
        df_vote["Trump Percentage"],
        "Blue",
        "Red"
    )

    df_vote["actual_blue"] = np.where(
        df_vote["真实结果"] == "Blue",
        1,
        0
    )

    _end_step("读取真实选举结果")

    # ============================================================
    # 5. Join social-media indicators to election results.
    # ============================================================

    df_eval = pd.merge(
        df_scores,
        df_vote,
        left_on="州全称",
        right_on="State",
        how="inner"
    )

    df_eval = df_eval[
        df_eval["归一化比例"].notna()
        &
        df_eval["actual_blue"].notna()
    ].copy()

    print("\n" + "=" * 60)
    print("州级数据匹配情况")
    print("=" * 60)

    print(
        f"社交媒体数据地区数: {len(df_scores)}"
    )

    print(
        f"真实选举数据地区数: {len(df_vote)}"
    )

    print(
        f"最终成功匹配地区数: {len(df_eval)}"
    )

    unmatched_states = (
        set(df_scores["州全称"])
        -
        set(df_vote["State"])
    )

    if unmatched_states:
        print(
            "未进入选举比较的地区:",
            sorted(unmatched_states)
        )

    # ============================================================
    # 6. Select a ROC/Youden-J threshold.
    # ============================================================

    def _find_youden_threshold(y_true, scores):

        fpr, tpr, thresholds = roc_curve(
            y_true,
            scores
        )

        youden_j = tpr - fpr

        # The first roc_curve threshold may be infinite.
        # Maximize J over finite thresholds only.
        finite_mask = np.isfinite(thresholds)

        finite_indices = np.where(
            finite_mask
        )[0]

        best_index = finite_indices[
            np.argmax(
                youden_j[finite_indices]
            )
        ]

        return (
            float(thresholds[best_index]),
            float(youden_j[best_index]),
            float(tpr[best_index]),
            float(fpr[best_index]),
        )

    y_true = (
        df_eval["actual_blue"]
        .astype(int)
        .to_numpy()
    )

    scores = (
        df_eval["归一化比例"]
        .astype(float)
        .to_numpy()
    )

    (
        optimal_threshold,
        best_youden_j,
        sensitivity,
        fpr_value
    ) = _find_youden_threshold(
        y_true,
        scores
    )

    specificity = 1 - fpr_value

    # ============================================================
    # Predict red/blue outcomes using the selected threshold.
    # ============================================================

    df_eval["预测结果"] = np.where(
        df_eval["归一化比例"]
        >= optimal_threshold,
        "Blue",
        "Red"
    )

    y_pred = np.where(
        df_eval["预测结果"] == "Blue",
        1,
        0
    )

    # ============================================================
    # Calculate evaluation measures.
    # ============================================================

    accuracy = accuracy_score(
        y_true,
        y_pred
    )

    balanced_accuracy = balanced_accuracy_score(
        y_true,
        y_pred
    )

    auc = roc_auc_score(
        y_true,
        scores
    )

    tn, fp, fn, tp = confusion_matrix(
        y_true,
        y_pred,
        labels=[0, 1]
    ).ravel()

    df_eval["是否一致"] = np.where(
        df_eval["预测结果"]
        ==
        df_eval["真实结果"],
        "Yes",
        "No"
    )

    # ============================================================
    # If the normalized indicator is the min-max transform of the raw left/right ratio,
    # also report the corresponding raw-ratio threshold.
    # ============================================================

    ratio_threshold = np.nan

    if "左派比上右派" in df_scores.columns:

        df_scores["左派比上右派"] = pd.to_numeric(
            df_scores["左派比上右派"],
            errors="coerce"
        )

        ratio_min = (
            df_scores["左派比上右派"]
            .min()
        )

        ratio_max = (
            df_scores["左派比上右派"]
            .max()
        )

        ratio_threshold = (
            ratio_min
            +
            optimal_threshold
            *
            (ratio_max - ratio_min)
        )

    # ============================================================
    # 7. Leave-one-state-out cross-validation.
    #
    # For each held-out state:
    # Select a Youden threshold using the other states.
    # Predict the held-out state.
    #
    # Report this separately from same-sample threshold selection and evaluation.
    # ============================================================

    cv_predictions = []

    for i in range(len(df_eval)):

        train_mask = (
            np.arange(len(df_eval))
            != i
        )

        cv_threshold, _, _, _ = (
            _find_youden_threshold(
                y_true[train_mask],
                scores[train_mask]
            )
        )

        pred_i = int(
            scores[i]
            >= cv_threshold
        )

        cv_predictions.append(
            pred_i
        )

    cv_predictions = np.array(
        cv_predictions
    )

    cv_accuracy = accuracy_score(
        y_true,
        cv_predictions
    )

    cv_balanced_accuracy = (
        balanced_accuracy_score(
            y_true,
            cv_predictions
        )
    )

    # ============================================================
    # Print the results.
    # ============================================================

    print("\n" + "=" * 60)
    print("ROC + Youden J 自动阈值结果")
    print("=" * 60)

    print(
        f"最优归一化阈值: "
        f"{optimal_threshold:.6f}"
    )

    if pd.notna(ratio_threshold):

        print(
            f"对应原始 左派/右派 比值: "
            f"{ratio_threshold:.6f}"
        )

    print(
        f"Youden's J: "
        f"{best_youden_j:.4f}"
    )

    print(
        f"Sensitivity (Blue): "
        f"{sensitivity:.4f}"
    )

    print(
        f"Specificity (Red): "
        f"{specificity:.4f}"
    )

    print(
        f"ROC AUC: "
        f"{auc:.4f}"
    )

    print("\n" + "=" * 60)
    print("州级红蓝结果一致性")
    print("=" * 60)

    print(
        f"正确州数: "
        f"{tp + tn}/{len(df_eval)}"
    )

    print(
        f"同样本 Agreement: "
        f"{accuracy:.2%}"
    )

    print(
        f"Balanced Accuracy: "
        f"{balanced_accuracy:.2%}"
    )

    print(
        f"Leave-one-state-out Accuracy: "
        f"{cv_accuracy:.2%}"
    )

    print(
        f"Leave-one-state-out Balanced Accuracy: "
        f"{cv_balanced_accuracy:.2%}"
    )

    print(
        "\n混淆矩阵:"
    )

    print(
        f"真实Red → 预测Red: {tn}"
    )

    print(
        f"真实Red → 预测Blue: {fp}"
    )

    print(
        f"真实Blue → 预测Red: {fn}"
    )

    print(
        f"真实Blue → 预测Blue: {tp}"
    )

    # Report misclassified states.
    misclassified = df_eval[
        df_eval["是否一致"] == "No"
    ][
        [
            "州全称",
            "归一化比例",
            "Biden Percentage",
            "Trump Percentage",
            "真实结果",
            "预测结果",
        ]
    ]

    if not misclassified.empty:

        print("\n错分地区：")

        print(
            misclassified.to_string(
                index=False
            )
        )

    # Save the state-level comparison table.
    df_eval.to_csv(
        save_compare_path,
        index=False,
        encoding="utf-8-sig"
    )

    print(
        f"\n州级对比结果已保存："
        f"{save_compare_path}"
    )

    _end_step("自动寻找阈值并评价")

    # ============================================================
    # 8. Build a color scale around the selected threshold.
    #
    # Preserve the original palette.
    # Dark red, red, light red; light blue, blue, dark blue.
    #
    # Threshold-placement difference:
    # The historical palette changed camps at 0.3.
    # This version changes camps at optimal_threshold.
    # ============================================================

    threshold_for_color = float(
        np.clip(
            optimal_threshold,
            0.001,
            0.999
        )
    )

    # Preserve approximate relative positions of the other color stops.
    red_middle = (
        threshold_for_color
        *
        (2 / 3)
    )

    blue_middle = (
        threshold_for_color
        +
        (1 - threshold_for_color)
        *
        (5 / 7)
    )

    color_scale = [

        [
            0,
            "rgb(139, 26, 26)"
        ],

        [
            red_middle,
            "rgb(204, 102, 102)"
        ],

        [
            threshold_for_color,
            "rgb(255, 153, 153)"
        ],

        # Switch directly from red to blue at the threshold.
        [
            threshold_for_color,
            "rgb(181, 216, 243)"
        ],

        [
            blue_middle,
            "rgb(51, 102, 153)"
        ],

        [
            1,
            "rgb(0, 51, 102)"
        ],
    ]

    # ============================================================
    # 9. Draw the map.
    # ============================================================

    min_value = 0.0
    max_value = 1.0

    # Omit regions without a USA state abbreviation.
    # For example, Puerto Rico and the US Virgin Islands.
    df_plot = df_scores[
        df_scores["州"].notna()
    ].copy()

    fig = px.choropleth(

        df_plot,

        locations="州",

        locationmode="USA-states",

        color="归一化比例",

        color_continuous_scale=color_scale,

        range_color=[
            min_value,
            max_value
        ],

        labels={
            "归一化比例":
            "State Score"
        },

        title=(
            "USA States Map with Custom Coloring"
        ),
    )

    fig.update_geos(

        projection_type="albers usa",

        visible=False,

        scope="usa",
    )

    _end_step("构建 choropleth")

    # ============================================================
    # 10. Save the PDF.
    # ============================================================

    pio.write_image(

        fig,

        save_pdf_path,

        format="pdf",

        width=5000,

        height=7000,
    )

    _end_step("导出 PDF")

    # ============================================================
    # 11. Display the figure.
    # ============================================================

    fig.show()

    _end_step("fig.show()")

    if pbar is not None:
        pbar.close()

    print(
        f"\n[图5a] 全部完成，"
        f"总耗时 "
        f"{time.perf_counter() - t_all:.2f}s"
    )



# Historical run output:

# Historical progress sample: step 2 of 6, reading election results.
# ============================================================
# State-level input matching summary.
# ============================================================
# Social-media input regions: 50.
# Election input regions: 50.
# Successfully matched regions: 50.

# ============================================================
# ROC/Youden-J threshold summary.
# ============================================================
# Historical normalized threshold: 0.314311.
# Historical raw left/right ratio threshold: 2.881367.
# Youden's J: 0.8400
# Sensitivity (Blue): 0.8400
# Specificity (Red): 1.0000
# ROC AUC: 0.9616

# ============================================================
# State-level red/blue agreement.
# ============================================================
# Historical correct predictions: 46/50.
# Historical same-sample agreement: 92.00%.
# Balanced Accuracy: 92.00%
# Leave-one-state-out Accuracy: 90.00%
# Leave-one-state-out Balanced Accuracy: 90.00%

# Historical confusion matrix:
# Actual Red, predicted Red: 25.
# Actual Red, predicted Blue: 0.
# Actual Blue, predicted Red: 4.
# Actual Blue, predicted Blue: 21.

# Misclassified regions:
# Historical table: state name, normalized score, Biden/Trump percentages, actual outcome and predicted outcome.
#        Nevada 0.198975             50.06             47.67 Blue  Red
#       Arizona 0.199190             49.36             49.06 Blue  Red
#       Georgia 0.278378             49.47             49.24 Blue  Red
# New Hampshire 0.292334             52.71             45.36 Blue  Red



# Historical progress sample: all six steps completed.

# Historical total runtime: 5.74 seconds.
if __name__ == '__main__':
    evaluate_state_scores_and_plot_map()
