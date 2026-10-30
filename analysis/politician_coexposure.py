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









# Configuration.
DATA_DIR = project_path('data', f'audiences/politicians')
RESULT_DIR = project_path('outputs', 'coexposure')

# Step 1: select nodes.
# Keep the configured fraction of politicians with the largest audiences.
NODE_TOP_PERCENTILE = 0.8

# Step 2: select edges.
# Keep each politician's ten strongest links.
TOP_K_EDGES = 10

# Category color mapping.
COLOR_MAP = {
    "Left": {'r': 51, 'g': 102, 'b': 153, 'a': 1.0},
    "Center": {'r': 240, 'g': 230, 'b': 140, 'a': 1.0},
    "Right": {'r': 204, 'g': 102, 'b': 102, 'a': 1.0},
    "Unknown": {'r': 128, 'g': 128, 'b': 128, 'a': 1.0}
}


# ===========================================

def load_data(root_dir):
    print("Step 1: Loading data from 'influenced_user_sets'...")
    pol_users = {}
    pol_bias = {}

    if not os.path.exists(root_dir):
        print(f"Error: Directory '{root_dir}' does not exist.")
        return {}, {}

    csv_files = glob.glob(os.path.join(root_dir, '**/*.csv'), recursive=True)
    csv_files = [f for f in csv_files if not os.path.basename(f).startswith('._')]

    print(f"Found {len(csv_files)} files.")

    for file_path in csv_files:
        filename = os.path.basename(file_path)
        try:
            parts = filename.split('_')
            if len(parts) < 2:
                continue

            bias = parts[0]
            pol_id = parts[1]

            if bias not in ["Left", "Right", "Center"]:
                pass

            df = pd.read_csv(file_path, header=None, dtype=str)
            users = set(df.iloc[:, 0].dropna().unique())

            if len(users) > 0:
                pol_users[pol_id] = users
                pol_bias[pol_id] = bias
        except Exception as e:
            print(f"  Error reading {filename}: {e}")

    print(f"Loaded {len(pol_users)} politicians (Nodes).")
    return pol_users, pol_bias


def build_network_top_k(pol_users, pol_bias, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 1. Select network nodes.
    print(f"\nStep 2: Filtering Top {NODE_TOP_PERCENTILE * 100}% Politicians by Audience Size...")

    # Count unique users for each politician.
    user_counts = {pid: len(u) for pid, u in pol_users.items()}
    # Sort by audience size.
    sorted_pids = sorted(user_counts.keys(), key=lambda x: user_counts[x], reverse=True)

    # Retain the configured leading fraction of nodes.
    num_nodes_keep = int(len(sorted_pids) * NODE_TOP_PERCENTILE)
    num_nodes_keep = max(1, num_nodes_keep)

    top_nodes_set = set(sorted_pids[:num_nodes_keep])
    print(f"  Retained {len(top_nodes_set)} nodes out of {len(pol_users)}.")

    # 2. Load or calculate pairwise edges.
    csv_path = os.path.join(output_dir, 'all_politician_jaccard_values.csv')
    df_edges = pd.DataFrame()

    # Read and filter an existing edge file, or compute edges only between retained nodes.
    if os.path.exists(csv_path):
        print(f"\nStep 3: Found existing edge file. Loading...")
        df_edges = pd.read_csv(csv_path, dtype={'source': str, 'target': str, 'weight': float})
        print(f"  Loaded {len(df_edges)} total edges.")

        # Convert ID columns to strings and strip whitespace.
        df_edges['source'] = df_edges['source'].astype(str).str.strip()
        df_edges['target'] = df_edges['target'].astype(str).str.strip()

        # Keep edges whose endpoints both belong to top_nodes_set.
        mask_nodes = df_edges['source'].isin(top_nodes_set) & df_edges['target'].isin(top_nodes_set)
        df_edges = df_edges[mask_nodes].copy()
        print(f"  Filtered to {len(df_edges)} edges within the top {NODE_TOP_PERCENTILE * 100}% nodes.")

    else:
        print(f"\nStep 3: Calculating Jaccard Similarities for Top Politicians...")
        pol_list = list(top_nodes_set)
        all_edges = []

        # Calculate edges only between retained nodes.
        total_pairs = len(list(combinations(pol_list, 2)))
        print(f"  Processing {total_pairs} pairs...")

        for id_i, id_j in combinations(pol_list, 2):
            users_i = pol_users[id_i]
            users_j = pol_users[id_j]
            union = len(users_i.union(users_j))
            if union > 0:
                intersection = len(users_i.intersection(users_j))
                if intersection > 0:
                    jaccard = intersection / union
                    all_edges.append({
                        'source': str(id_i),
                        'target': str(id_j),
                        'weight': jaccard,
                        'raw_intersection': intersection
                    })
        df_edges = pd.DataFrame(all_edges)
        # The calculated subset may be saved separately if required.
        # This branch keeps the subset in memory without overwriting the full cache.

    if df_edges.empty:
        print("No edges available after filtering.")
        return

    # 3. Select each politician's Top 10 edges.
    print(f"\nStep 4: Keeping top {TOP_K_EDGES} strongest edges for each politician...")

    # Take the union of the strongest incident-edge sets selected by each node.
    # Keep A-B when it is selected among either A's or B's strongest neighbors.

    kept_indices = set()

    # Group by node to retrieve incident edges efficiently.
    # Index both orientations of each undirected pair.

    # Concatenate original and reversed endpoint columns for grouping.
    # Original orientations: [A, B, w], [C, D, w].
    # Reversed orientations: [B, A, w], [D, C, w].
    # Group the combined table by source to collect each node's incident edges.

    df_forward = df_edges.copy()
    df_backward = df_edges.rename(columns={'source': 'target', 'target': 'source'})

    # Use indices to select rows from the original df_edges table.
    df_forward['original_index'] = df_edges.index
    df_backward['original_index'] = df_edges.index

    df_combined = pd.concat([df_forward, df_backward])

    # Within each source group, sort weight descending and retain Top K original_index values.
    top_k_indices = df_combined.groupby('source', group_keys=False) \
        .apply(lambda x: x.sort_values('weight', ascending=False).head(TOP_K_EDGES))

    kept_indices = set(top_k_indices['original_index'].values)

    final_edges_df = df_edges.loc[list(kept_indices)].copy()

    print(f"  Selected {len(final_edges_df)} unique edges based on Top-{TOP_K_EDGES} per node logic.")

    # 4. Construct and optionally save the graph.
    print(f"\nStep 5: Generating Graph...")

    G_final = nx.Graph()

    # Add nodes.
    for pol_id in top_nodes_set:
        user_count = user_counts.get(pol_id, 0)
        bias = pol_bias.get(pol_id, "Unknown")
        color = COLOR_MAP.get(bias, COLOR_MAP["Unknown"])

        G_final.add_node(
            str(pol_id),
            label=str(pol_id),
            political_bias=bias,
            user_count=user_count,
            viz={'color': color}
        )

    # Add edges.
    for _, row in final_edges_df.iterrows():
        G_final.add_edge(
            row['source'],
            row['target'],
            weight=float(row['weight']),
            raw_intersection=int(row['raw_intersection']) if 'raw_intersection' in row else 0
        )

    # Remove isolated nodes.
    G_final.remove_nodes_from(list(nx.isolates(G_final)))

    # Optionally retain the largest connected component.
    if len(G_final) > 0:
        largest_cc = max(nx.connected_components(G_final), key=len)
        G_output = G_final.subgraph(largest_cc).copy()
        print(f"  Extracted Giant Component: {G_output.number_of_nodes()} nodes.")
    else:
        G_output = G_final

    # Save the output.
    output_filename = f'politician_network_NodesTop{int(NODE_TOP_PERCENTILE * 100)}_EdgesTop{TOP_K_EDGES}.gexf'
    output_path = os.path.join(output_dir, output_filename)
    nx.write_gexf(G_output, output_path)
    print(f"Graph saved to: {output_path}")


def main():
    pol_users, pol_bias = load_data(DATA_DIR)
    if not pol_users:
        return
    build_network_top_k(pol_users, pol_bias, RESULT_DIR)


if __name__ == "__main__":
    main()