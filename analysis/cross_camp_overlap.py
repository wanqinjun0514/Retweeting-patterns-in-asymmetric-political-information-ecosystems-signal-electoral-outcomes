# -*- coding: utf-8 -*-
"""
Figure 3 follow-up experiment
Final network filtered version

This version uses only the final Fig. 3a media nodes from the GEXF file,
loads each media outlet's user set from category folders, recalculates
pairwise overlaps, and aggregates only the 9 left-camp x right-camp groups.
"""
from pathlib import Path as _ReleasePath
import sys as _release_sys
_release_root = next(_p for _p in _ReleasePath(__file__).resolve().parents if (_p / 'runtime_config.py').is_file())
_release_sys.path.insert(0, str(_release_root))
from runtime_config import project_path


import glob
import os
import re

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
from matplotlib.ticker import PercentFormatter


GEXF_PATH = (
    project_path('outputs', 'coexposure/media_network_CatTop25_EdgeTop10.gexf')
)

MEDIA_ROOT = (
    project_path('data', 'audiences/media')
)

BIAS_ROOT = (
    project_path('outputs', 'analyses/Average_Bias_Rating/media_average_rating/total_url-rating/user_bias_scores_by_quarter')
)

OUTPUT_ROOT = os.environ.get(
    "FIG3_OUTPUT_ROOT",
    os.path.join(MEDIA_ROOT, "Final_network_filtered_followup"),
)

QUARTERS = [
    "2019_12_2020_01_2020_02",
    "2020_03_2020_04_2020_05",
    "2020_06_2020_07_2020_08",
    "2020_09_2020_10",
    "2020_11_2020_12",
    "2021_01_2021_02",
]

BIAS_ORDER = [
    "Left",
    "Left Leaning",
    "Center",
    "Right Leaning",
    "Right",
]

LEFT_CAMP = [
    "Left",
    "Left Leaning",
]

RIGHT_CAMP = [
    "Right Leaning",
    "Right",
]

CROSS_CAMP_GROUPS = [
    (left, right)
    for left in LEFT_CAMP
    for right in RIGHT_CAMP
]

os.makedirs(OUTPUT_ROOT, exist_ok=True)


def normalize_media_name(name):
    name = str(name).strip().lower()
    name = re.sub(r"\.csv$", "", name)
    name = name.replace("&", "and")
    name = re.sub(r"[^a-z0-9]+", " ", name)
    name = re.sub(r"\s+", " ", name)
    return name.strip()


def read_gexf_nodes():
    G = nx.read_gexf(GEXF_PATH)

    rows = []
    for node, attr in G.nodes(data=True):
        rows.append({
            "media": node,
            "category": attr.get("political_bias"),
            "gexf_user_count": attr.get("user_count"),
        })

    df = pd.DataFrame(rows).dropna(subset=["media", "category"])
    df = df[df["category"] != "Fake News"].copy()

    print("\nFinal GEXF media:", len(df))
    print(df["category"].value_counts())

    df.to_csv(
        os.path.join(OUTPUT_ROOT, "final_gexf_media_nodes.csv"),
        index=False,
        encoding="utf-8-sig",
    )
    return df


def read_user_set(path):
    df = pd.read_csv(path, dtype=str)

    if "user_id" in df.columns:
        user_col = "user_id"
    else:
        df = pd.read_csv(path, dtype=str, header=None)
        user_col = df.columns[0]

    users = df[user_col].dropna().astype(str).str.strip()
    users = users[users != ""]
    return set(users)


def load_media_users():
    media_users = {}
    media_index = {}
    file_rows = []

    for folder in BIAS_ORDER:
        path = os.path.join(MEDIA_ROOT, folder)

        if not os.path.exists(path):
            print(f"{folder} 0 (missing folder: {path})")
            continue

        files = glob.glob(os.path.join(path, "*.csv"))
        print(folder, len(files))

        for f in files:
            media = os.path.basename(f).replace(".csv", "")
            users = read_user_set(f)

            if len(users) == 0:
                continue

            media_users[media] = users
            media_index[normalize_media_name(media)] = media
            file_rows.append({
                "media_file_name": media,
                "folder_category": folder,
                "user_count": len(users),
                "path": f,
            })

    print("Loaded media:", len(media_users))

    pd.DataFrame(file_rows).to_csv(
        os.path.join(OUTPUT_ROOT, "loaded_media_user_files.csv"),
        index=False,
        encoding="utf-8-sig",
    )
    return media_users, media_index


def keep_final_media(media_nodes, media_users, media_index):
    final = {}
    audit_rows = []

    for _, row in media_nodes.iterrows():
        media = row["media"]
        matched_media = None
        match_type = "not_matched"

        if media in media_users:
            matched_media = media
            match_type = "exact"
        else:
            key = normalize_media_name(media)
            if key in media_index:
                matched_media = media_index[key]
                match_type = "normalized"

        if matched_media is not None:
            final[media] = media_users[matched_media]

        audit_rows.append({
            "gexf_media": media,
            "gexf_category": row["category"],
            "matched_media_file": matched_media,
            "match_type": match_type,
            "user_count": len(final.get(media, set())),
        })

    print("Matched final media:", len(final))

    audit = pd.DataFrame(audit_rows)
    audit.to_csv(
        os.path.join(OUTPUT_ROOT, "final_gexf_media_match_audit.csv"),
        index=False,
        encoding="utf-8-sig",
    )

    missing = audit[audit["match_type"] == "not_matched"]
    if len(missing) > 0:
        print("\nUnmatched final media:")
        print(missing[["gexf_category", "gexf_media"]].to_string(index=False))

    return final


def calculate_overlap(final_users, media_nodes):
    category = dict(zip(media_nodes["media"], media_nodes["category"]))
    result = {f"{left}+{right}": set() for left, right in CROSS_CAMP_GROUPS}
    pair_rows = []
    medias = list(final_users.keys())

    for i in range(len(medias)):
        for j in range(i + 1, len(medias)):
            m1 = medias[i]
            m2 = medias[j]
            c1 = category[m1]
            c2 = category[m2]

            if c1 in LEFT_CAMP and c2 in RIGHT_CAMP:
                key = f"{c1}+{c2}"
            elif c2 in LEFT_CAMP and c1 in RIGHT_CAMP:
                key = f"{c2}+{c1}"
            else:
                continue

            users = final_users[m1] & final_users[m2]
            result[key].update(users)
            pair_rows.append({
                "media_1": m1,
                "category_1": c1,
                "media_2": m2,
                "category_2": c2,
                "group": key,
                "shared_user_count": len(users),
            })

    print("\nCross camp groups:")
    for k, v in result.items():
        print(k, len(v))

    pd.DataFrame(pair_rows).to_csv(
        os.path.join(OUTPUT_ROOT, "cross_camp_media_pair_overlap_audit.csv"),
        index=False,
        encoding="utf-8-sig",
    )
    return result


def bias_category(x):
    try:
        x = float(x)
    except (TypeError, ValueError):
        return None

    if not np.isfinite(x) or not -3 <= x <= 3:
        return None
    if x < -2.5:
        return "Extreme Left"
    if x < -1.5:
        return "Left"
    if x < -0.5:
        return "Left Leaning"
    if x < 0.5:
        return "Center"
    if x < 1.5:
        return "Right Leaning"
    if x < 2.5:
        return "Right"
    return "Extreme Right"


def load_bias():
    data = {}

    for q in QUARTERS:
        f = os.path.join(
            BIAS_ROOT,
            f"quarterly_user_bias_scores_{q}.csv",
        )

        df = pd.read_csv(f, dtype={"user_id": str})
        df = df.dropna(subset=["user_id", "average_bias_points"])
        df["category"] = df["average_bias_points"].apply(bias_category)
        df["category"] = df["category"].replace({
            "Extreme Bias Left": "Extreme Left",
            "Left-Leaning": "Left Leaning",
            "Extreme Bias Right": "Extreme Right"
        })
        df = df.drop_duplicates("user_id")
        data[q] = df

    return data


def normalized_rate(users, df):
    den = df.groupby("category").size().to_dict()
    sub = df[df["user_id"].isin(users)]
    num = sub.groupby("category").size().to_dict()

    rows = []
    for c in BIAS_ORDER:
        denominator = den.get(c, 0)
        count = num.get(c, 0)
        rows.append({
            "category": c,
            "count": count,
            "denominator": denominator,
            "rate": count / denominator if denominator > 0 else 0,
        })

    return pd.DataFrame(rows)


def plot(results):

    out = os.path.join(OUTPUT_ROOT, "Plots")
    os.makedirs(out, exist_ok=True)

    fig, axes = plt.subplots(
    2, 2,
    figsize=(12, 8),
    dpi=300
    )

    axes = axes.flatten()

    # User-ideology colors.
    color_map = {
        "Extreme Left": "#355C8A",
        "Left": "#5B8CC0",
        "Left Leaning": "#A9CBE8",
        "Center": "#E6D86A",
        "Right Leaning": "#F28E8E",
        "Right": "#C65C60",
        "Extreme Right": "#8B0000",
    }

    title_map = {
    "Left+Right Leaning": "Co-exposure to Left and Right-Leaning Media",
    "Left+Right": "Co-exposure to Left and Right Media",
    "Left Leaning+Right Leaning": "Co-exposure to Left-Leaning and Right-Leaning Media",
    "Left Leaning+Right": "Co-exposure to Left-Leaning and Right Media",
    }
    for ax, (name, df) in zip(axes, results.items()):

        colors = [
            color_map.get(c, "gray")
            for c in df["category"]
        ]

        ax.bar(
            df["category"],
            df["rate"],
            color=colors
        )

        ax.set_title(title_map.get(name, name), fontsize=12)

        ax.yaxis.set_major_formatter(
            PercentFormatter(1)
        )

        ax.tick_params(
            axis="x",
            rotation=45
        )

        ax.set_ylim(0, 1)


    # fig.text(
    #     0.04,
    #     0.5,
    #     "Normalized Co-exposure Rate",
    #     va="center",
    #     rotation="vertical",
    #     fontsize=14
    # )

    plt.tight_layout()

    plt.savefig(
        os.path.join(
            out,
            "all_4_media_pairs_grouped_bar_panel.png"
        ),
        dpi=300,
        bbox_inches="tight"
    )

    plt.close()


def main():
    media_nodes = read_gexf_nodes()
    media_users, media_index = load_media_users()
    final_users = keep_final_media(media_nodes, media_users, media_index)
    shared_groups = calculate_overlap(final_users, media_nodes)
    bias = load_bias()
    results = {}

    for group, users in shared_groups.items():
        qs = []

        for q, df in bias.items():
            temp = normalized_rate(users, df)
            temp["quarter"] = q
            qs.append(temp)

        merged = pd.concat(qs)
        merged = (
            merged.groupby("category")
            .agg({
                "count": "sum",
                "denominator": "sum",
            })
            .reset_index()
        )
        merged["rate"] = merged["count"] / merged["denominator"]
        merged["category"] = pd.Categorical(
            merged["category"],
            categories=BIAS_ORDER,
            ordered=True,
        )
        merged = merged.sort_values("category")
        results[group] = merged

        merged.to_csv(
            os.path.join(OUTPUT_ROOT, group + "_summary.csv"),
            index=False,
            encoding="utf-8-sig",
        )

    plot(results)
    print("\nFinished!")


if __name__ == "__main__":
    main()
