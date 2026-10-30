from pathlib import Path as _ReleasePath
import sys as _release_sys
_release_root = next(_p for _p in _ReleasePath(__file__).resolve().parents if (_p / 'runtime_config.py').is_file())
_release_sys.path.insert(0, str(_release_root))
from runtime_config import project_path

import os
import glob
import pandas as pd
import networkx as nx
from itertools import combinations








# 1. Load user sets and category metadata.
# Read media files from the configured political-category folders.

# Treat each media CSV's first column as its unique audience-user set.

# Store the media name, audience set and category in lookup dictionaries.

# 2. Select network nodes.
# Retain the configured leading media outlets to construct the displayed network.

# Count each outlet's unique audience users.

# Keep the 25 outlets with the largest audiences in each category, using TOP_N_PER_CATEGORY.

# 3. Compute Jaccard edge weights.
# An edge measures overlap between two media audience sets using Jaccard similarity.

# Jaccard = unique shared users / unique users in the union.

# Reuse all_media_jaccard_values.csv when present; otherwise compute pairwise overlaps for retained media.

# 4. Select network edges.
# Retain the configured strongest audience-overlap links.

# For each outlet, keep TOP_K_EDGES = 10 neighbors with the highest Jaccard weights.

# Combine per-node strongest-neighbor links into the displayed sparse network.

# 5. Construct the graph and configure export.
# Attach political category, audience size and configured visualization colors to each node.

# Remove isolated nodes.

# Keep the largest connected component.

# The commented export block writes media_network_CatTop25_EdgeTop10.gexf with node attributes and graph structure.
# Configuration.
DATA_ROOT_DIR = project_path('data', f'audiences/media')  # Input data root.
RESULT_DIR = project_path('outputs', f'coexposure')  # Results directory.

# Strategy 1: select nodes.
# Top media outlets per category, ranked by unique-user count.
TOP_N_PER_CATEGORY = 25

# Strategy 2: select edges.
# Retain each node's K strongest neighbors.
TOP_K_EDGES = 10

# Specify the category directories to load.
TARGET_CATEGORIES = [
    "Center", "Extreme Bias Left", "Extreme Bias Right", 
    "Left", "Left Leaning", "Right", "Right Leaning"
]

COLOR_MAP = {
    'Extreme Bias Left': {'r': 0, 'g': 51, 'b': 102, 'a': 1.0},
    'Left': {'r': 51, 'g': 102, 'b': 153, 'a': 1.0},
    'Left Leaning': {'r': 181, 'g': 216, 'b': 243, 'a': 1.0},
    'Center': {'r': 240, 'g': 230, 'b': 140, 'a': 1.0},
    'Right Leaning': {'r': 255, 'g': 153, 'b': 153, 'a': 1.0},
    'Right': {'r': 204, 'g': 102, 'b': 102, 'a': 1.0},
    'Extreme Bias Right': {'r': 139, 'g': 26, 'b': 26, 'a': 1.0},
    'Unknown': {'r': 128, 'g': 128, 'b': 128, 'a': 1.0}
}


# ===========================================

def load_data(root_dir):
    print("Step 1: Loading data...")
    media_users = {}
    media_bias = {}

    if not os.path.exists(root_dir):
        print(f"Error: Path '{root_dir}' does not exist.")
        return {}, {}

    for category in TARGET_CATEGORIES:
        cat_path = os.path.join(root_dir, category)
        if not os.path.isdir(cat_path):
            continue

        csv_files = glob.glob(os.path.join(cat_path, '*.csv'))
        # print(f"  - Reading {category}: {len(csv_files)} files.")

        for file_path in csv_files:
            media_name = os.path.splitext(os.path.basename(file_path))[0]
            try:
                # Read user IDs from the first column.
                df = pd.read_csv(file_path, header=None, usecols=[0], dtype=str)
                users = set(df.iloc[:, 0].dropna().unique())
                if len(users) > 0:
                    media_users[media_name] = users
                    media_bias[media_name] = category
            except Exception as e:
                print(f"    Error reading {file_path}: {e}")

    print(f"Loaded {len(media_users)} media outlets in total.")
    return media_users, media_bias


def build_network_top_k(media_users, media_bias, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 1. Select Top 25 nodes within each category.
    print(f"\nStep 2: Filtering Top {TOP_N_PER_CATEGORY} Media per Category...")

    # Count users for each media outlet.
    media_counts = []
    for m, users in media_users.items():
        media_counts.append({
            'name': m,
            'bias': media_bias[m],
            'count': len(users)
        })
    df_counts = pd.DataFrame(media_counts)

    # Select Top N within each category.
    # Use group_keys=False to avoid an extra index level.
    top_media_df = df_counts.groupby('bias', group_keys=False).apply(
        lambda x: x.sort_values('count', ascending=False).head(TOP_N_PER_CATEGORY)
    )

    valid_media_set = set(top_media_df['name'].values)

    print(f"  Total nodes retained: {len(valid_media_set)}")
    print(f"  Breakdown by category:")
    print(top_media_df['bias'].value_counts())

    # 2. Load or compute edges between retained nodes.
    csv_path = os.path.join(output_dir, 'all_media_jaccard_values.csv')
    df_edges = pd.DataFrame()

    if os.path.exists(csv_path):
        print(f"\nStep 3: Found existing edge file. Loading...")
        df_full = pd.read_csv(csv_path, dtype={'source': str, 'target': str, 'weight': float})

        # Keep edges whose source and target both belong to valid_media_set.
        mask = df_full['source'].isin(valid_media_set) & df_full['target'].isin(valid_media_set)
        df_edges = df_full[mask].copy()
        print(f"  Filtered to {len(df_edges)} edges among top media.")

    else:
        print(f"\nStep 3: Calculating Jaccard Similarities for Top Media...")
        media_list = list(valid_media_set)
        all_edges = []

        total_pairs = len(list(combinations(media_list, 2)))
        print(f"  Processing {total_pairs} pairs...")

        for name_i, name_j in combinations(media_list, 2):
            users_i = media_users[name_i]
            users_j = media_users[name_j]

            union = len(users_i.union(users_j))
            if union > 0:
                intersection = len(users_i.intersection(users_j))
                if intersection > 0:
                    jaccard = intersection / union
                    all_edges.append({
                        'source': name_i,
                        'target': name_j,
                        'weight': jaccard,
                        'raw_intersection': intersection
                    })

        df_edges = pd.DataFrame(all_edges)
        # Optionally save the calculated Jaccard edges.
        if not df_edges.empty:
            print(f"  Saving calculated Jaccard values to {csv_path}...")
            df_edges.to_csv(csv_path, index=False, encoding='utf-8-sig')
            print("  Save complete.")
        # ------------------------------------------
        # Do not overwrite a global cache with a locally filtered result in this branch.
        # Alternatively, save the filtered result under a different file name.

    if df_edges.empty:
        print("No edges found between selected media.")
        return

    # 3. Select the configured Top K edges per node.
    print(f"\nStep 4: Keeping Top {TOP_K_EDGES} strongest edges for each media...")

    # Represent each undirected pair in both directions for grouping.
    # Grouping by source then exposes all neighbors of each node.
    df_forward = df_edges[['source', 'target', 'weight', 'raw_intersection']].copy()
    df_backward = df_edges[['target', 'source', 'weight', 'raw_intersection']].copy()
    df_backward.columns = ['source', 'target', 'weight', 'raw_intersection']

    df_combined = pd.concat([df_forward, df_backward])

    # Select Top K edges in each source group.
    df_top_k = df_combined.groupby('source', group_keys=False).apply(
        lambda x: x.sort_values('weight', ascending=False).head(TOP_K_EDGES)
    )

    print(f"  Edges retained (directional count): {len(df_top_k)}")

    # 4. Construct and optionally save the graph.
    print(f"\nStep 5: Generating Graph...")
    G = nx.Graph()

    # Add nodes.
    for media_name in valid_media_set:
        user_count = len(media_users[media_name])
        bias = media_bias[media_name]
        color = COLOR_MAP.get(bias, COLOR_MAP["Unknown"])

        G.add_node(
            media_name,
            political_bias=bias,
            user_count=user_count,
            viz={'color': color}
        )

    # Add edges.
    # NetworkX treats the two orientations of an undirected pair as the same edge.
    # For duplicate orientations, the last assignment replaces attributes with the same values.
    for _, row in df_top_k.iterrows():
        G.add_edge(
            row['source'],
            row['target'],
            weight=float(row['weight']),
            raw_intersection=int(row['raw_intersection'])
        )

    print(f"Network constructed: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges.")

    # Remove isolated nodes.
    G.remove_nodes_from(list(nx.isolates(G)))
    print(f"After removing isolates: {G.number_of_nodes()} nodes.")

    # Optionally retain the largest connected component.
    if len(G) > 0:
        largest_cc = max(nx.connected_components(G), key=len)
        G_final = G.subgraph(largest_cc).copy()
        print(f"Extracted Largest Connected Component: {G_final.number_of_nodes()} nodes.")
    else:
        G_final = G

    # Save the output.
    # output_filename = f'media_network_CatTop{TOP_N_PER_CATEGORY}_EdgeTop{TOP_K_EDGES}.gexf'
    # output_path = os.path.join(output_dir, output_filename)
    # nx.write_gexf(G_final, output_path)
    # print(f"Graph saved to: {output_path}")


def main():
    media_users, media_bias = load_data(DATA_ROOT_DIR)
    if not media_users:
        return
    build_network_top_k(media_users, media_bias, RESULT_DIR)


if __name__ == "__main__":
    main()