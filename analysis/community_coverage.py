# -*- coding: utf-8 -*-
"""Summarize community sizes, media-score coverage and Top3 ideology categories.

Process the six research windows and write three CSVs:
1. 每季度社群总览.csv: user/community counts and Top3 community IDs and sizes.
2. 全部社群规模与媒体评分覆盖率.csv: one row per community/window, including
   valid-media-score counts and coverage.
3. 前三大社群政治倾向分类数量.csv: one row per Top3 community/window with
   counts for each '政客政治倾向分类' and '媒体政治倾向分类' label. Missing or
   blank labels retain the output category '未分类/缺失'.

Each input row represents one node; reject duplicate user_id values.
A valid '媒体bias' is a nonmissing value convertible to a finite number.
Rank communities by descending user count.
"""
from pathlib import Path as _ReleasePath
import sys as _release_sys
_release_root = next(_p for _p in _ReleasePath(__file__).resolve().parents if (_p / 'runtime_config.py').is_file())
_release_sys.path.insert(0, str(_release_root))
from runtime_config import project_path


from pathlib import Path
from typing import Optional
import re

import numpy as np
import pandas as pd


# 1. Configure paths.

ROOT = Path(
    project_path('outputs', 'analyses/转发网络/季度合并_Top1Percent度数网络提取/季度社团Hub分析')
)

PERIOD_FOLDERS = [
    "2019_12_2020_01_2020_02",
    "2020_03_2020_04_2020_05",
    "2020_06_2020_07_2020_08",
    "2020_09_2020_10",
    "2020_11_2020_12",
    "2021_01_2021_02",
]

OUTPUT_OVERVIEW = ROOT / "每季度社群总览.csv"
OUTPUT_ALL_COMMUNITIES = ROOT / "全部社群规模与媒体评分覆盖率.csv"
OUTPUT_TOP3_DISTRIBUTION = ROOT / "前三大社群政治倾向分类数量.csv"

REQUIRED_COLUMNS = [
    "user_id",
    "community_id",
    "媒体bias",
    "政客政治倾向分类",
    "媒体政治倾向分类",
]


# 2. Read CSVs and locate period-specific files.

def read_csv_with_fallback(file_path: Path) -> pd.DataFrame:
    """Try the supported CSV encodings in order."""
    encodings = ["utf-8-sig", "utf-8", "gbk", "gb18030"]
    last_error = None

    for encoding in encodings:
        try:
            df = pd.read_csv(file_path, encoding=encoding)
            # Strip accidental whitespace from column names.
            df.columns = [str(c).strip() for c in df.columns]
            return df
        except UnicodeDecodeError as exc:
            last_error = exc

    raise RuntimeError(
        "无法读取文件编码。已尝试 {}。文件：{}；最后错误：{}".format(
            encodings, file_path, last_error
        )
    )


def locate_period_csv(period_folder: Path, period_name: str) -> Optional[Path]:
    """Prefer the expected file name; otherwise require one uniquely matching CSV."""
    expected = period_folder / (
        "{}_top1pct_社团划分结果_完成分类.csv".format(period_name)
    )
    if expected.exists():
        return expected

    candidates = list(
        period_folder.glob("*_top1pct_社团划分结果_完成分类.csv")
    )

    if len(candidates) == 1:
        print(
            "[提示] {} 使用文件夹内唯一匹配文件：{}".format(
                period_name, candidates[0].name
            )
        )
        return candidates[0]

    if len(candidates) == 0:
        print(
            "[缺失] 文件夹 {} 中未找到 "
            "*_top1pct_社团划分结果_完成分类.csv".format(period_folder)
        )
        return None

    names = "\n".join("  - {}".format(p.name) for p in candidates)
    raise RuntimeError(
        "{} 文件夹中找到多个候选 CSV，无法自动判断应使用哪一个：\n{}\n"
        "请检查文件后，在 locate_period_csv() 中指定正确文件。".format(
            period_name, names
        )
    )


# 3. Normalize category fields.

MISSING_LABELS = {"", "nan", "none", "null", "na", "n/a", "<na>"}


def normalize_category(series: pd.Series) -> pd.Series:
    """Normalize political-category whitespace while retaining original labels.
    
    Map missing values, empty strings and configured missing-value text to the
    unchanged category '未分类/缺失'. Preserve all other category names.
    """
    text = series.astype("string").str.strip()
    missing_mask = text.isna() | text.str.lower().isin(MISSING_LABELS)
    text = text.mask(missing_mask, "未分类/缺失")
    return text.astype(str)


def valid_numeric_score(series: pd.Series) -> pd.Series:
    """Return a mask indicating scores convertible to finite numeric values."""
    numeric = pd.to_numeric(series, errors="coerce")
    return numeric.notna() & np.isfinite(numeric)


def safe_column_suffix(value: str) -> str:
    """Clean category-derived column suffixes so embedded line breaks do not alter headers."""
    value = re.sub(r"[\r\n\t]+", " ", str(value)).strip()
    return value or "未分类/缺失"


# 4. Calculate statistics for one research window.

def analyze_one_period(period_name: str):
    period_folder = ROOT / period_name
    if not period_folder.exists():
        print("[缺失] 季度文件夹不存在：{}".format(period_folder))
        return None

    csv_path = locate_period_csv(period_folder, period_name)
    if csv_path is None:
        return None

    df = read_csv_with_fallback(csv_path)

    missing_columns = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_columns:
        raise ValueError(
            "\n文件缺少必要列：{}\n文件：{}\n实际列名：{}".format(
                missing_columns, csv_path, df.columns.tolist()
            )
        )

    # Drop rows without an identifiable user or community.
    original_rows = len(df)
    df = df.dropna(subset=["user_id", "community_id"]).copy()
    dropped_rows = original_rows - len(df)
    if dropped_rows:
        print(
            "[提示] {} 删除了 {} 行缺少 user_id/community_id 的记录。".format(
                period_name, dropped_rows
            )
        )

    # Each user_id should appear once in this node table.
    duplicate_mask = df["user_id"].duplicated(keep=False)
    if duplicate_mask.any():
        examples = (
            df.loc[duplicate_mask, "user_id"]
            .astype(str)
            .unique()[:10]
            .tolist()
        )
        raise ValueError(
            "\n{} 中发现重复 user_id，示例：{}\n"
            "请先检查节点表，避免社群人数及覆盖率重复计数。\n文件：{}".format(
                period_name, examples, csv_path
            )
        )

    df["_valid_media_bias"] = valid_numeric_score(df["媒体bias"])
    df["_politician_category"] = normalize_category(df["政客政治倾向分类"])
    df["_media_category"] = normalize_category(df["媒体政治倾向分类"])

    total_users = int(df["user_id"].nunique())

    # Community size is the number of users in each community_id.
    community_sizes = (
        df.groupby("community_id")["user_id"]
        .nunique()
        .rename("community_total_users")
        .reset_index()
    )
    community_sizes = community_sizes.sort_values(
        by=["community_total_users", "community_id"],
        ascending=[False, True],
        kind="mergesort",
    ).reset_index(drop=True)
    community_sizes["community_rank_by_size"] = np.arange(
        1, len(community_sizes) + 1
    )

    number_of_communities = int(df["community_id"].nunique())

    # Window-level overview.
    overview = {
        "period": period_name,
        "file_name": csv_path.name,
        "total_users_in_network": total_users,
        "number_of_communities": number_of_communities,
    }
    for rank in range(1, 4):
        if len(community_sizes) >= rank:
            row = community_sizes.iloc[rank - 1]
            overview["top{}_community_id".format(rank)] = row["community_id"]
            overview["top{}_community_users".format(rank)] = int(
                row["community_total_users"]
            )
        else:
            overview["top{}_community_id".format(rank)] = ""
            overview["top{}_community_users".format(rank)] = 0

    # Community sizes and media-score coverage for all communities.
    all_community_records = []
    for _, community_row in community_sizes.iterrows():
        community_id = community_row["community_id"]
        community_df = df[df["community_id"] == community_id]

        community_user_count = int(community_df["user_id"].nunique())
        users_with_media_bias = int(community_df["_valid_media_bias"].sum())

        all_community_records.append({
            "period": period_name,
            "file_name": csv_path.name,
            "number_of_communities_in_period": number_of_communities,
            "community_rank_by_size": int(
                community_row["community_rank_by_size"]
            ),
            "community_id": community_id,
            "community_total_users": community_user_count,
            "users_with_valid_media_bias": users_with_media_bias,
            "users_without_valid_media_bias": (
                community_user_count - users_with_media_bias
            ),
            "media_bias_coverage_pct": round(
                users_with_media_bias / community_user_count * 100, 2
            ) if community_user_count else np.nan,
            "is_top3_community": (
                int(community_row["community_rank_by_size"]) <= 3
            ),
        })

    # Count politician-based and media-based categories within the three largest communities only.
    top3_records = []
    for _, community_row in community_sizes.head(3).iterrows():
        community_id = community_row["community_id"]
        community_df = df[df["community_id"] == community_id]

        community_user_count = int(community_df["user_id"].nunique())
        users_with_media_bias = int(community_df["_valid_media_bias"].sum())

        politician_counts = (
            community_df["_politician_category"].value_counts(dropna=False).to_dict()
        )
        media_counts = (
            community_df["_media_category"].value_counts(dropna=False).to_dict()
        )

        top3_records.append({
            "period": period_name,
            "file_name": csv_path.name,
            "community_rank_by_size": int(
                community_row["community_rank_by_size"]
            ),
            "community_id": community_id,
            "community_total_users": community_user_count,
            "users_with_valid_media_bias": users_with_media_bias,
            "media_bias_coverage_pct": round(
                users_with_media_bias / community_user_count * 100, 2
            ) if community_user_count else np.nan,
            "_politician_counts": politician_counts,
            "_media_counts": media_counts,
        })

    print(
        "[完成] {}：用户 {:,} 人；社群 {} 个；前三大社群人数为 {}。".format(
            period_name,
            total_users,
            number_of_communities,
            [
                int(x) for x in community_sizes.head(3)[
                    "community_total_users"
                ].tolist()
            ],
        )
    )

    return overview, all_community_records, top3_records


# 5. Combine and export the six research windows.

def main():
    if not ROOT.exists():
        raise FileNotFoundError(
            "找不到根目录：{}\n请确认本地 G: 盘路径及“季度社团Hub分析”文件夹名称。".format(
                ROOT
            )
        )

    overview_records = []
    all_community_records = []
    top3_records = []
    missing_periods = []

    for period in PERIOD_FOLDERS:
        result = analyze_one_period(period)
        if result is None:
            missing_periods.append(period)
            continue

        overview, all_communities, top3 = result
        overview_records.append(overview)
        all_community_records.extend(all_communities)
        top3_records.extend(top3)

    if not overview_records:
        raise RuntimeError(
            "没有成功统计任何季度。请检查根目录、六个文件夹名称及 CSV 文件名。"
        )

    # File 1: overview for each window.
    overview_df = pd.DataFrame(overview_records)
    overview_df.to_csv(OUTPUT_OVERVIEW, index=False, encoding="utf-8-sig")

    # File 2: sizes and media-score coverage for all communities.
    all_communities_df = pd.DataFrame(all_community_records)
    all_communities_df.to_csv(
        OUTPUT_ALL_COMMUNITIES, index=False, encoding="utf-8-sig"
    )

    # File 3: wide-format category counts for the three largest communities, suitable for spreadsheet inspection.
    politician_categories = sorted({
        str(category)
        for record in top3_records
        for category in record["_politician_counts"].keys()
    })
    media_categories = sorted({
        str(category)
        for record in top3_records
        for category in record["_media_counts"].keys()
    })

    top3_output_records = []
    for record in top3_records:
        row = {
            "period": record["period"],
            "file_name": record["file_name"],
            "community_rank_by_size": record["community_rank_by_size"],
            "community_id": record["community_id"],
            "community_total_users": record["community_total_users"],
            "users_with_valid_media_bias": record["users_with_valid_media_bias"],
            "media_bias_coverage_pct": record["media_bias_coverage_pct"],
        }

        for category in politician_categories:
            column = "政客分类人数_{}".format(safe_column_suffix(category))
            row[column] = int(record["_politician_counts"].get(category, 0))

        for category in media_categories:
            column = "媒体分类人数_{}".format(safe_column_suffix(category))
            row[column] = int(record["_media_counts"].get(category, 0))

        top3_output_records.append(row)

    top3_df = pd.DataFrame(top3_output_records)
    top3_df.to_csv(
        OUTPUT_TOP3_DISTRIBUTION, index=False, encoding="utf-8-sig"
    )

    print("\n================ 统计完成 ================")
    print("1. 每季度社群总览：{}".format(OUTPUT_OVERVIEW))
    print("2. 全部社群规模与媒体评分覆盖率：{}".format(OUTPUT_ALL_COMMUNITIES))
    print("3. 前三大社群政治倾向分类数量：{}".format(OUTPUT_TOP3_DISTRIBUTION))
    print("\n已统计季度数：{}".format(len(overview_df)))
    print("全部社群记录数：{}".format(len(all_communities_df)))
    print("前三大社群记录数：{}".format(len(top3_df)))

    if missing_periods:
        print("\n[警告] 以下季度未成功统计，请检查终端中的提示：")
        for period in missing_periods:
            print("  - {}".format(period))

    print("\n每季度社群总览预览：")
    print(overview_df.to_string(index=False))

    print("\n前三大社群媒体评分覆盖率预览：")
    print(top3_df[[
        "period",
        "community_rank_by_size",
        "community_id",
        "community_total_users",
        "users_with_valid_media_bias",
        "media_bias_coverage_pct",
    ]].to_string(index=False))


if __name__ == "__main__":
    main()
