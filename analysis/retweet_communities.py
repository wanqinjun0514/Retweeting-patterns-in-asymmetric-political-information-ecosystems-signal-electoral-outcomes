from pathlib import Path as _ReleasePath
import sys as _release_sys
_release_root = next(_p for _p in _ReleasePath(__file__).resolve().parents if (_p / 'runtime_config.py').is_file())
_release_sys.path.insert(0, str(_release_root))
from runtime_config import project_path

import pandas as pd
import networkx as nx
import community.community_louvain as community_louvain
import os
import numpy as np
import traceback
import gc
import re
# Original Twitter records.
#        ↓
# Result:
# twitter_url/output_month
# without_url/output_month
# external_url/output_month
# Source datasets to be supplied with the research data.

# Pool External URL, Twitter URL and Without URL retweet records within each analysis period.
# Define an undirected user pair from retweeted_user_id and retweet_origin_user_id.
# Aggregate repeated user pairs into interaction-count edge weights and remove self-loops.
# Take the largest connected component, compute its 99th degree percentile and retain the induced subgraph of nodes at or above that threshold.
# Run Louvain community detection, hub identification and community-structure analysis on this core graph.
# Existing files for each research window:
# {period}_top1pct_edges.csv
# {period}_top1pct_nodes.csv
#         ↓
# Build the NetworkX graph.
#         ↓
# Run Louvain community detection.
#         ↓
# Analyze community structure.
#         ↓
# Attach ideology scores.
#         ↓
# Plot community bias distributions and radar charts.




# % ============================================================
# Quarterly core-retweet network and community-ideology workflow.
# % ============================================================
# %
# Stages:
# 1. Extract the quarterly Top1% degree-based core network.
# 2. Run Louvain and calculate hub and community-structure measures.
# 3. Attach quarterly continuous media-based and politician-based ideology scores to nodes.
# 4. Classify nodes using their continuous ideology scores.
# 5. Export ideology attributes to GEXF for Gephi visualization.
# %
# Original Twitter records and the three processed sources are intended to accompany the data release.
# This analysis starts from prepared monthly Twitter URL, Without URL and External URL records.

# % ============================================================
# Stage 1: extract quarterly Top1% degree-based core networks.
# % ============================================================
# %
# Historical network-extraction implementation:

# Reference file: 合并三部分数据的Kcore网络并逐步增加K值_20260518_手动精简了代码.py
# %
# Function used:
# def extract_top_degree_retweet_subgraphs()
# %
# Network input data:

# % 1. single_url\twitter_url\output_{month}
# % 2. without_url\output_{month}
# % 3. single_url\external_url\output_{month}
# %
# Required record fields:
# % retweeted_user_id
# % retweet_origin_user_id
# %
# Network-extraction procedure:
# 1. Pool the months in each of the paper's six analysis periods.
# 2. Pool retweet records from Twitter URL, Without URL and External URL within each period.
# 3. Define retweet endpoints using retweeted_user_id and retweet_origin_user_id.
# 4. Build an undirected igraph multigraph with initial edge weight one.
# 5. Sum repeated user-pair interactions into edge weights.
# 6. Remove self-loops to obtain a simplified weighted undirected graph.
# 7. Extract the largest connected component for this period.
# 8. Compute unweighted degree for every node in the full LCC.
# 9. Retain nodes with degree at or above the 99th percentile.
# Ties at the threshold can retain slightly more than 1% of nodes.
# 10. Extract the subgraph induced by the retained high-degree nodes.
# 11. Save node and weighted-edge tables for Louvain analysis.
# %
# Top1% selection criterion:
# Select by unweighted degree in the full LCC.
# Do not select by weighted degree or degree measured inside the extracted subgraph.
# %
# Network-extraction output directory:

# %
# Directory read by the downstream analysis:

# %
# Outputs for each analysis period:
# % {period}_top1pct_nodes.csv
# Principal fields:
# %   user_id
# %   degree
# %
# % {period}_top1pct_edges.csv
# Principal fields:
# %   source
# %   target
# %   weight
# %
# weight counts repeated retweet interactions between the two users in this period.

# % ============================================================
# Stage 2: Louvain communities, hub identification and community-structure measures.
# % ============================================================
# %
# Community-analysis function:
# def analyze_quarterly_top_degree_communities()
# %
# Inputs produced by stage 1:

# % {period}_top1pct_edges.csv
# %

# % {period}_top1pct_nodes.csv
# %
# Analysis-results directory:

# Reference directory component: 季度社团Hub分析{period}
# %
# Community-analysis procedure:
# 1. Reconstruct the core network from the Top1% node and edge tables.
# 2. Convert the network to undirected form for Louvain community detection.
# 3. Fixed Louvain parameters:
# %    resolution = 1.0
# %    random_seed = 42
# 4. Rank communities by node count.
# 5. Define Top1, Top2 and Top3 as the three largest communities in the current period.
# 6. Compute weighted degree and PageRank.
# 7. Select each community's ten highest-ranked nodes for weighted degree and PageRank separately.
# These rankings identify hub or core accounts.
# 8. Extract internal subgraphs of the three largest communities and calculate:
# %    node_count
# %    edge_count
# %    density
# %    avg_degree
# %    assortativity
# %    clustering_coefficient
# 9. Save the partition, hub tables, community metrics and GEXF network.
# %
# Principal outputs:
# %
# % {period}_res1.0_seed42.gexf
# The GEXF contains graph topology, Louvain community, weighted degree and PageRank attributes.
# Use it for Gephi visualization and subsequent ideology-attribute attachment.
# %
# % {period}_res1.0_seed42_top10_nodes.csv
# Highest-ranked weighted-degree and PageRank nodes within each community.
# %
# % {period}_res1.0_seed42_top3_community_metrics.csv
# Structural measures for the three largest communities.
# %
# Reference file: {period}_top1pct_社团划分结果.csv
# Save all Top1% network nodes and their Louvain community_id.
# Use this node table to attach ideology scores.

# % ============================================================
# Stage 3: attach quarterly continuous ideology scores to community nodes.
# % ============================================================
# %
# Function used:
# def attach_quarterly_bias_to_community_nodes()
# %
# Network-node input:

# Reference directory component: 季度社团Hub分析{period}
# Reference file: {period}_top1pct_社团划分结果.csv
# %
# When the node CSV is absent, recover nodes from:
# % {period}_res1.0_seed42.gexf
# Recover node IDs and Louvain community attributes from that GEXF.
# %
# Directory containing politician-based continuous ideology scores:

# % politician_average_rating\total_url-rating\user_bias_scores_by_quarter
# %
# Directory containing media-based continuous ideology scores:

# % media_average_rating\total_url-rating\user_bias_scores_by_quarter
# %
# Processing procedure:
# 1. Read all Top1% network nodes and community IDs for the analysis period.
# 2. Read politician-based user ideology for the same period.
# 3. Read media-based user ideology for the same period.
# 4. Match both continuous score types to nodes by user_id.
# 5. Retain unmatched nodes with missing ideology attributes.
# %
# Output file:

# Reference directory component: 季度社团Hub分析{period}
# Reference file: {period}_top1pct_社团划分结果_补充bias.csv
# %
# Principal added fields:
# CSV field: 政客bias
# CSV field: 媒体bias

# % ============================================================
# Stage 4: classify continuous ideology scores.
# % ============================================================
# %
# Function used:
# def classify_community_node_ideology()
# %
# Input file:
# Reference file: {period}_top1pct_社团划分结果_补充bias.csv
# %
# Processing procedure:
# 1. Classify valid politician-based scores into three categories.
# %    Left
# %    Center
# %    Right
# %
# 2. Classify valid media-based scores into seven categories.
# %    Extreme Left
# %    Left
# %    Left-Leaning
# %    Center
# %    Right-Leaning
# %    Right
# %    Extreme Right
# %
# 3. Politician-based scores have range [-1, 1].
# 4. Media-based scores have range [-3, 3].
# 5. Retain both continuous scores and category labels.
# %
# Output file:

# Reference directory component: 季度社团Hub分析{period}
# Reference file: {period}_top1pct_社团划分结果_完成分类.csv
# %
# Principal added fields:
# CSV field: 政客政治倾向分类
# CSV field: 媒体政治倾向分类

# % ============================================================
# Stage 5: export ideology attributes to a new GEXF.
# % ============================================================
# %
# Function used:
# def export_gexf_with_ideology_attributes()
# %
# Inputs:
# %
# 1. Original Louvain network file.
# % {period}_res1.0_seed42.gexf
# %
# 2. Node table with completed ideology classification.
# Reference file: {period}_top1pct_社团划分结果_完成分类.csv
# %
# Processing procedure:
# 1. Read the GEXF containing the Louvain partition.
# 2. Match classified ideology attributes to network nodes by user_id.
# 3. Attach the following node attributes:
# CSV field: 政客bias
# CSV field: 媒体bias
# CSV field: 政客政治倾向分类
# CSV field: 媒体政治倾向分类
# 4. Preserve the original topology and Louvain community assignments.
# 5. Save a new GEXF with ideology attributes without replacing the original graph file.
# %
# Final GEXF output:

# Reference directory component: 季度社团Hub分析{period}
# % {period}_res1.0_seed42_with_political_attributes.gexf
# %
# Use this file for Gephi visualization and community-ideology analysis.
# Use this network file for Top1/Top2 media-ideology comparisons and community-structure analysis.

# % ============================================================
# Subsequent analyses.
# % ============================================================
# %
# After the five stages above:
# %
# 1. Analyze ideology distributions in each period's Top1, Top2 and Top3 communities.
# 2. Compare Top1 and Top2 media-ideology distributions within each period.
# 3. Extract PageRank and weighted-degree core nodes from the three largest communities.
# 4. Calculate mean media bias for Top1 and Top2.
# 5. Compare node_count, edge_count, avg_degree, assortativity,
# clustering coefficient and mean media bias with radar charts.






# This version selects by degree percentile rather than a k-core threshold.
# Stage 1: extract the network.
def extract_top_degree_retweet_subgraphs():
    import igraph as ig

    # Configuration.
    # List the research windows; no K parameter is used in this version.
    QUARTERS = [
        "2019_12_2020_01_2020_02",
        "2020_03_2020_04_2020_05",
        "2020_06_2020_07_2020_08",
        "2020_09_2020_10",
        "2020_11_2020_12",
        "2021_01_2021_02"
    ]
    
    # Existing input directories.
    BASE_INPUT_DIRS = [
        project_path('data', 'sources/single_url/twitter_url/output_{}'),
        project_path('data', 'sources/without_url/output_{}'),
        project_path('data', 'sources/single_url/external_url/output_{}'),
    ]
    
    # Output directory for this network variant.
    RESULT_DIR = project_path('outputs', 'analyses/转发网络/季度合并_Top1Percent度数网络提取')
    if not os.path.exists(RESULT_DIR):
        os.makedirs(RESULT_DIR)
        
    # Fraction of high-degree nodes retained: 1%.
    TOP_PERCENT = 0.01 
    # ===========================================

    for period_name in QUARTERS:
        print(f"\n{'='*30}")
        print(f"正在处理: {period_name}")
        print(f"目标: 提取度数排名前 {int(TOP_PERCENT*100)}% 的节点")
        print(f"{'='*30}")

        # 1. Parse the months in this period.
        sub_months = re.findall(r'\d{4}_\d{2}', period_name)
        print(f" -> 包含月份: {sub_months}")

        # 2. Read records and construct the edge list.
        all_edges = []
        for month in sub_months:
            for base_dir_template in BASE_INPUT_DIRS:
                data_dir = base_dir_template.format(month)
                if not os.path.exists(data_dir):
                    continue
                
                # Process each file.
                for file in os.listdir(data_dir):
                    if file.endswith('.csv'):
                        file_path = os.path.join(data_dir, file)
                        try:
                            # Read only the two endpoint columns as strings to preserve ID precision.
                            df = pd.read_csv(file_path, usecols=['retweeted_user_id', 'retweet_origin_user_id'], dtype=str)
                            df.dropna(inplace=True)
                            # Convert rows to endpoint tuples.
                            edges = list(df.itertuples(index=False, name=None))
                            all_edges.extend(edges)
                        except Exception as e:
                            print(f"    [Warning] 读取出错 {file}: {e}")
        
        print(f" -> 数据读取完毕，原始互动记录数: {len(all_edges)}")

        # 3. Construct the igraph network.
        print(" -> 正在构建图并计算权重...")
        # TupleList constructs a multigraph from repeated pairs.
        g = ig.Graph.TupleList(all_edges, directed=False)
        del all_edges
        gc.collect() 
        
        # Initialize each interaction edge with weight one.
        g.es['weight'] = 1

        print(f"    [原始多重图] 节点: {g.vcount()}, 边(互动次数): {g.ecount()}")

        # 4. Aggregate parallel edges, remove loops and extract the LCC.
        print(" -> 正在聚合权重并简化图...")
        
        # Sum weights of repeated edges when simplifying.
        g.simplify(multiple=True, loops=True, combine_edges={'weight': 'sum'})
        
        print(f"    [简化后加权图] 节点: {g.vcount()}, 边(唯一关系对): {g.ecount()}")
        
        print(" -> 正在提取最大连通子图 (LCC)...")
        components = g.components()
        largest = components.giant()
        
        del g, components
        gc.collect()
        
        print(f"    [LCC] 节点: {largest.vcount()}, 边: {largest.ecount()}")

        # =======================================================
        # 5. Compute degrees and retain the configured top percentile.
        # =======================================================
        print(f" -> 正在计算度数并筛选 Top {int(TOP_PERCENT*100)}%...")
        
        # Compute unweighted node degrees.
        degrees = largest.degree()
        
        # Compute the percentile threshold corresponding to TOP_PERCENT.
        # Nodes at or above that threshold are eligible for retention.
        degree_threshold = np.percentile(degrees, (1.0 - TOP_PERCENT) * 100)
        
        print(f"    [阈值计算] 度数前 1% 的门槛值为: {degree_threshold}")
        
        # Keep nodes with degree >= the threshold.
        # Ties at the threshold can retain more than the nominal fraction.
        nodes_to_keep = [v.index for v, d in zip(largest.vs, degrees) if d >= degree_threshold]
        
        # Extract the induced subgraph.
        top_degree_subgraph = largest.subgraph(nodes_to_keep)
        
        del largest, degrees
        gc.collect()
        
        print(f"    [最终 Top 1% 子图] 节点: {top_degree_subgraph.vcount()}, 边: {top_degree_subgraph.ecount()}")

        # 6. Save the weighted network tables.
        print(" -> 正在保存文件...")
        
        node_file = os.path.join(RESULT_DIR, f"{period_name}_top1pct_nodes.csv")
        edge_file = os.path.join(RESULT_DIR, f"{period_name}_top1pct_edges.csv")
        
        # 6.1. Save nodes.
        # Save subgraph degree as a node-size attribute for Gephi.
        sub_degrees = top_degree_subgraph.degree()
        nodes_df = pd.DataFrame({
            'user_id': top_degree_subgraph.vs['name'],
            'degree': sub_degrees # Also save the node degree.
        })
        nodes_df.to_csv(node_file, index=False)
        
        # 6.2. Save weighted edges.
        edges_indices = top_degree_subgraph.get_edgelist()
        edges_weights = top_degree_subgraph.es['weight']
        
        source_ids = [top_degree_subgraph.vs[u]['name'] for u, v in edges_indices]
        target_ids = [top_degree_subgraph.vs[v]['name'] for u, v in edges_indices]
        
        edges_df = pd.DataFrame({
            'source': source_ids,
            'target': target_ids,
            'weight': edges_weights
        })
        # Sort edges by descending weight.
        edges_df = edges_df.sort_values(by='weight', ascending=False)
        
        edges_df.to_csv(edge_file, index=False)
        
        print(f" -> 保存完成: \n    节点: {node_file}\n    边: {edge_file}")
        
        del top_degree_subgraph, nodes_df, edges_df
        gc.collect()




# Stage 2: reconstruct quarterly retweet networks, detect communities, rank hubs and calculate structural measures.

# Inputs:
# File-name format, directory and principal fields.
# Edge table: {Root}\{Period}\{Period}_top1pct_edges.csv; source, target and weight.
# Node attributes: user_id and community_id; retain the original completed-classification file name.
# Outputs:
# Output suffix res1.0_seed42 records the resolution and random seed.
# Output suffix, content and purpose.
# _top10_nodes.csv: each community's Top10 weighted-degree and Top10 PageRank nodes, with IDs and ranking attributes.
# _top3_community_metrics.csv: node_count, edge_count, density, avg_degree, assortativity and clustering_coefficient for the three largest communities.
# .gexf: graph topology and attributes for Gephi visualization.
def process_quarterly_analysis(period,base_root = project_path('outputs', f'analyses/转发网络/季度合并_Top2Percent度数网络提取/季度社团Hub分析'), resolution=1.0, random_seed=42):
    """Analyze one period's communities, hubs, Top3 structural measures and GEXF output."""
    # 1. Build the input paths and file names.
    edges_file = project_path('outputs', f'analyses/转发网络/季度合并_Top2Percent度数网络提取/{period}_top1pct_edges.csv')

    period_folder = os.path.join(base_root, period)
    nodes_file = f"{period}_top1pct_社团划分结果_完成分类.csv"

    # Build the full path.
    edges_path = os.path.join(period_folder, edges_file)
    nodes_path = os.path.join(period_folder, nodes_file)

    # Result-file parameter suffix.
    params_tag = f"res{resolution}_seed{random_seed}"
    output_gexf = os.path.join(period_folder, f"{period}_{params_tag}.gexf")
    output_top10 = os.path.join(period_folder, f"{period}_{params_tag}_top10_nodes.csv")
    # Output path for the Top3 community metrics.
    output_comm_metrics = os.path.join(period_folder, f"{period}_{params_tag}_top3_community_metrics.csv")

    print(f"\n" + "=" * 50)
    print(f"正在处理季度: {period}")
    print(f"读取路径: {period_folder}")

    if not os.path.exists(edges_path) or not os.path.exists(nodes_path):
        print(f"跳过：文件不存在。请检查路径: {edges_path}")
        return

    # 2. Load the data.
    df_edges = pd.read_csv(edges_path)
    df_nodes_attr = pd.read_csv(nodes_path)

    # Assign the expected names to the first three columns.
    df_edges.columns = ['source', 'target', 'weight'] + list(df_edges.columns[3:])

    # 3. Construct a weighted undirected graph and attach node attributes.
    G = nx.from_pandas_edgelist(df_edges, 'source', 'target', edge_attr='weight', create_using=nx.Graph())

    # Prepare node attributes.
    df_nodes_attr = df_nodes_attr.rename(columns={'community_id': 'original_community'})
    node_attr_dict = df_nodes_attr.set_index('user_id').to_dict('index')
    nx.set_node_attributes(G, node_attr_dict)

    # 4. Run Louvain community detection.
    print("运行 Louvain 算法...")
    G_undirected = G.to_undirected()
    partition = community_louvain.best_partition(
        G_undirected, weight='weight', resolution=resolution, random_state=random_seed
    )
    nx.set_node_attributes(G, partition, 'louvain_community')

    # 5. Summarize community sizes and proportions.
    total_nodes = len(G.nodes())
    counts = pd.Series(partition).value_counts()
    stats = pd.DataFrame({
        'louvain_community': counts.index,
        'node_count': counts.values,
        'percentage (%)': (counts.values / total_nodes * 100).round(2)
    }).sort_values('node_count', ascending=False)

    print("\n[社团划分占比 (Top 5)]:")
    print(stats.head(5).to_string(index=False))

    # 6. Compute weighted degree and PageRank.
    print("计算节点核心指标...")
    nx.set_node_attributes(G, dict(G.degree(weight='weight')), 'weighted_degree')
    nx.set_node_attributes(G, nx.pagerank(G, weight='weight'), 'pagerank')

    # 7. Select the Top10 nodes for each ranking.
    nodes_data = []
    for node, attrs in G.nodes(data=True):
        row = {'user_id': node}
        row.update(attrs)
        nodes_data.append(row)
    df_full_nodes = pd.DataFrame(nodes_data)

    top_list = []
    for comm_id in stats['louvain_community']:
        comm_df = df_full_nodes[df_full_nodes['louvain_community'] == comm_id]
        t1 = comm_df.nlargest(10, 'weighted_degree').copy()
        t1['ranking_type'] = 'weighted_degree'
        t2 = comm_df.nlargest(10, 'pagerank').copy()
        t2['ranking_type'] = 'pagerank'
        top_list.extend([t1, t2])

    # ==============================================================================
    # 7.5. Calculate structure measures for the three largest communities.
    # ==============================================================================
    print("计算 Top3 社团的网络结构指标...")
    top3_ids = stats['louvain_community'].head(3).tolist()
    comm_metrics_list = []

    for rank, comm_id in enumerate(top3_ids, 1):
        # 1. Extract the community subgraph.
        nodes_in_comm = [n for n, c in partition.items() if c == comm_id]
        # The extracted community subgraph is undirected.
        H = G.subgraph(nodes_in_comm).copy()
        # Use an undirected view for diameter and clustering calculations.
        H_und = H.to_undirected()

        # 2. Calculate the measures.

        # A. Paper-defined edge-to-node ratio D = E/N; keep the historical CSV key.
        # Count each undirected edge once; this is not the conventional mean degree 2E/N.
        avg_degree = len(H.edges()) / len(H.nodes()) if len(H.nodes()) > 0 else 0

        # B. Degree assortativity.
        try:
            # assortativity = nx.degree_assortativity_coefficient(H)
            assortativity = nx.degree_assortativity_coefficient(H_und) # Use the undirected view for the assortativity calculation.
        except Exception:
            assortativity = np.nan  # Degree assortativity may be undefined when degree variance is zero.

        # C. Average clustering coefficient.
        # Calculate clustering on the undirected view.
        clustering_coeff = nx.average_clustering(H_und)

        # D. Network diameter.
        # Diameter is the largest shortest-path distance in a connected graph.
        if nx.is_connected(H_und):
            diameter = nx.diameter(H_und)
            note = "Full Graph"
        else:
            # For a disconnected subgraph, calculate diameter on its LCC.
            if len(H_und) > 0:
                lcc = max(nx.connected_components(H_und), key=len)
                H_lcc = H_und.subgraph(lcc)
                diameter = nx.diameter(H_lcc)
                note = "LCC (Largest Component)"
            else:
                diameter = 0
                note = "Empty"

        comm_metrics_list.append({
            'period': period,
            'rank': rank,
            'community_id': comm_id,
            'node_count': len(H.nodes()),
            'edge_count': len(H.edges()),
            'avg_degree': round(avg_degree, 4),
            'assortativity': round(assortativity, 4) if pd.notna(assortativity) else None,
            'clustering_coefficient': round(clustering_coeff, 4),
            'diameter': diameter,
            'diameter_note': note  # Record whether the diameter uses the full subgraph or its LCC.
        })

    # Save community metrics.
    pd.DataFrame(comm_metrics_list).to_csv(output_comm_metrics, index=False, encoding='utf-8-sig')
    print(f"  -> Top3 社团指标已保存: {output_comm_metrics}")
    # ==============================================================================

    # 8. Save the remaining outputs.
    pd.concat(top_list).to_csv(output_top10, index=False, encoding='utf-8-sig')
    nx.write_gexf(G, output_gexf)
    print(f"处理成功！结果已存入该季度文件夹下。")

# Stage 3: community analysis.
# Community-analysis stage complete; this version omits diameter.
# Top1% degree-network variant introduced on 2026-04-08.
def analyze_quarterly_top_degree_communities(period, base_root=project_path('outputs', f'analyses/转发网络/季度合并_Top1Percent度数网络提取/季度社团Hub分析'), resolution=1.0, random_seed=42):
    """Analyze one Top1% network's communities, hubs and Top3 measures without diameter."""
    # 1. Build the input paths and file names.
    # Use raw strings and explicit path construction for Windows paths.
    # Avoid accidental numeric escape sequences when writing literal Windows paths.
    edges_base_dir = project_path('outputs', 'analyses/转发网络/季度合并_Top1Percent度数网络提取')
    edges_path = os.path.join(edges_base_dir, f"{period}_top1pct_edges.csv")

    # Create a separate output subdirectory for each research window.
    period_folder = os.path.join(base_root, period)
    os.makedirs(period_folder, exist_ok=True)

    # Read *_top1pct_nodes.csv from edges_base_dir with user_id and degree.
    nodes_path = os.path.join(edges_base_dir, f"{period}_top1pct_nodes.csv")

    # Result-file parameter suffix.
    params_tag = f"res{resolution}_seed{random_seed}"
    output_gexf = os.path.join(period_folder, f"{period}_{params_tag}.gexf")
    output_top10 = os.path.join(period_folder, f"{period}_{params_tag}_top10_nodes.csv")
    # Output path for the Top3 community metrics.
    output_comm_metrics = os.path.join(period_folder, f"{period}_{params_tag}_top3_community_metrics.csv")

    print(f"\n" + "=" * 50)
    print(f"正在处理季度: {period}")
    print(f"读取路径: {period_folder}")

    if not os.path.exists(edges_path) or not os.path.exists(nodes_path):
        if not os.path.exists(edges_path):
            print(f"跳过：边文件不存在。请检查路径: {edges_path}")
        if not os.path.exists(nodes_path):
            print(f"跳过：节点文件不存在。请检查路径: {nodes_path}")
        return

    # 2. Load the data.
    df_edges = pd.read_csv(edges_path)
    df_nodes_attr = pd.read_csv(nodes_path)

    # Assign the expected names to the first three columns.
    df_edges.columns = ['source', 'target', 'weight'] + list(df_edges.columns[3:])

    # 3. Construct a weighted undirected graph and attach node attributes.
    G = nx.from_pandas_edgelist(df_edges, 'source', 'target', edge_attr='weight', create_using=nx.Graph())

    # Prepare node attributes.
    df_nodes_attr = df_nodes_attr.rename(columns={'community_id': 'original_community'})
    node_attr_dict = df_nodes_attr.set_index('user_id').to_dict('index')
    nx.set_node_attributes(G, node_attr_dict)

    # 4. Run Louvain community detection.
    print("运行 Louvain 算法...")
    G_undirected = G.to_undirected()
    partition = community_louvain.best_partition(
        G_undirected, weight='weight', resolution=resolution, random_state=random_seed
    )
    nx.set_node_attributes(G, partition, 'louvain_community')

    # 5. Summarize community sizes and proportions.
    total_nodes = len(G.nodes())
    counts = pd.Series(partition).value_counts()
    stats = pd.DataFrame({
        'louvain_community': counts.index,
        'node_count': counts.values,
        'percentage (%)': (counts.values / total_nodes * 100).round(2)
    }).sort_values('node_count', ascending=False)

    print("\n[社团划分占比 (Top 5)]:")
    print(stats.head(5).to_string(index=False))

    # 6. Compute weighted degree and PageRank.
    print("计算节点核心指标...")
    nx.set_node_attributes(G, dict(G.degree(weight='weight')), 'weighted_degree')
    nx.set_node_attributes(G, nx.pagerank(G, weight='weight'), 'pagerank')

    # 7. Select the Top10 nodes for each ranking.
    nodes_data = []
    for node, attrs in G.nodes(data=True):
        row = {'user_id': node}
        row.update(attrs)
        nodes_data.append(row)
    df_full_nodes = pd.DataFrame(nodes_data)

    top_list = []
    for comm_id in stats['louvain_community']:
        comm_df = df_full_nodes[df_full_nodes['louvain_community'] == comm_id]
        t1 = comm_df.nlargest(10, 'weighted_degree').copy()
        t1['ranking_type'] = 'weighted_degree'
        t2 = comm_df.nlargest(10, 'pagerank').copy()
        t2['ranking_type'] = 'pagerank'
        top_list.extend([t1, t2])

    # ==============================================================================
    # 7.5. Calculate Top3 community measures without diameter.
    # ==============================================================================
    print("计算 Top3 社团的网络结构指标 (Exact metrics)...")
    top3_ids = stats['louvain_community'].head(3).tolist()
    comm_metrics_list = []

    for rank, comm_id in enumerate(top3_ids, 1):
        print(f"  -> 分析第 {rank} 大社团 (ID: {comm_id})...")

        # 1. Extract the community subgraph.
        nodes_in_comm = [n for n, c in partition.items() if c == comm_id]
        H = G.subgraph(nodes_in_comm).copy()  # Undirected community subgraph.
        H_und = H.to_undirected()  # Undirected view used for clustering.

        num_nodes = len(H.nodes())
        num_edges = len(H.edges())

        # A. Graph density.
        # Use the undirected density formula, counting each edge once.
        density = nx.density(H)

        # B. Paper-defined edge-to-node ratio D = E/N; keep the historical CSV key.
        avg_degree = num_edges / num_nodes if num_nodes > 0 else 0

        # C. Degree assortativity; requires processing edges.
        try:
            # assortativity = nx.degree_assortativity_coefficient(H)
            assortativity = nx.degree_assortativity_coefficient(H_und) # Use the undirected view for the assortativity calculation.
        except Exception:
            assortativity = np.nan

        # Without diameter, assortativity can be the most expensive measure in this stage.
        try:
            clustering_coeff = nx.average_clustering(H_und)
        except Exception:
            clustering_coeff = 0

        comm_metrics_list.append({
            'period': period,
            'rank': rank,
            'community_id': comm_id,
            'node_count': num_nodes,
            'edge_count': num_edges,
            'density': round(density, 8),  # Format the typically small density with eight decimal places.
            'avg_degree': round(avg_degree, 4),
            'assortativity': round(assortativity, 4) if pd.notna(assortativity) else None,
            'clustering_coefficient': round(clustering_coeff, 4)
        })

    # Save community metrics.
    pd.DataFrame(comm_metrics_list).to_csv(output_comm_metrics, index=False, encoding='utf-8-sig')
    print(f"  -> Top3 社团指标已保存: {output_comm_metrics}")
    # ==============================================================================

    # 8. Save the remaining outputs.
    pd.concat(top_list).to_csv(output_top10, index=False, encoding='utf-8-sig')

    # 8b. Export all node IDs and Louvain community_id values for ideology attachment.
    output_partition_csv = os.path.join(period_folder, f"{period}_top1pct_社团划分结果.csv")
    df_partition_export = df_full_nodes.rename(columns={"louvain_community": "community_id"})
    df_partition_export.to_csv(output_partition_csv, index=False, encoding="utf-8-sig")
    print(f"  -> 社团划分结果已保存: {output_partition_csv}")

    # Save the computed network as GEXF.
    print("正在保存 GEXF...")
    nx.write_gexf(G, output_gexf)
    print(f"处理成功！结果已存入该季度文件夹下。")




def _top1pct_default_quarters():
    return [
        "2019_12_2020_01_2020_02",
        "2020_03_2020_04_2020_05",
        "2020_06_2020_07_2020_08",
        "2020_09_2020_10",
        "2020_11_2020_12",
        "2021_01_2021_02",
    ]


def _nodes_dataframe_from_top1pct_gexf(gexf_path, community_attr_candidates=("louvain_community", "community_id")):
    """Recover the full node table and Louvain communities from an existing GEXF.
    
    Use graph node IDs as user_id and prefer the louvain_community attribute.
    This avoids rerunning community detection.
    """
    if not os.path.exists(gexf_path):
        raise FileNotFoundError(gexf_path)
    G = nx.read_gexf(gexf_path)
    rows = []
    for n, attrs in G.nodes(data=True):
        uid = str(n).strip()
        if not uid:
            continue
        attr = dict(attrs)
        comm = None
        for key in community_attr_candidates:
            if key in attr:
                comm = attr.pop(key)
                break
        row = {"user_id": uid, "community_id": comm}
        row.update(attr)
        rows.append(row)
    if not rows:
        raise ValueError(f"GEXF 中无节点: {gexf_path}")
    df = pd.DataFrame(rows)
    if "community_id" in df.columns:
        df["community_id"] = pd.to_numeric(df["community_id"], errors="coerce")
    df["user_id"] = df["user_id"].astype(str).str.strip()
    return df


def _bias_lookup_dict_from_table(df, id_col_candidates, score_col="average_bias_points"):
    """Build a string-user-ID lookup retaining the score table's original values."""
    if df is None or df.empty:
        return {}
    df = df.copy()
    df.columns = df.columns.str.strip()
    if score_col not in df.columns:
        return {}
    id_col = next((c for c in id_col_candidates if c in df.columns), None)
    if id_col is None:
        return {}
    out = {}
    for uid, val in zip(df[id_col], df[score_col]):
        if pd.isna(uid):
            continue
        key = str(uid).strip()
        if not key or key.lower() == "nan":
            continue
        out[key] = val
    return out

# Stage 4: attach quarterly continuous ideology scores to community nodes.
def attach_quarterly_bias_to_community_nodes(
    periods=None,
    node_base_dir=project_path('outputs', 'analyses/转发网络/季度合并_Top1Percent度数网络提取/季度社团Hub分析'),
    politician_dir=project_path('outputs', 'analyses/Average_Bias_Rating/politician_average_rating/total_url-rating/user_bias_scores_by_quarter'),
    media_dir=project_path('outputs', 'analyses/Average_Bias_Rating/media_average_rating/total_url-rating/user_bias_scores_by_quarter'),
    partition_csv_template="{quarter}_top1pct_社团划分结果.csv",
    bias_csv_template="quarterly_user_bias_scores_{quarter}.csv",
    partition_source="auto",
    gexf_params_tag="res1.0_seed42",
    gexf_filename_template="{quarter}_{params_tag}.gexf",
):
    """Attach politician and media scores by user_id and save the enriched node CSV.
    
    Output: {quarter}_top1pct_社团划分结果_补充bias.csv.
    partition_source='csv' reads partition_csv_template only; 'gexf' recovers
    nodes from the existing Louvain GEXF; 'auto' prefers CSV and falls back to GEXF.
    
    The GEXF must include louvain_community from analyze_quarterly_top_degree_communities.
    The default gexf_params_tag corresponds to resolution=1.0 and random_seed=42;
    use the tag of the actual input run.
    """
    if periods is None:
        periods = _top1pct_default_quarters()
    if partition_source not in ("csv", "gexf", "auto"):
        raise ValueError("partition_source 必须是 'csv'、'gexf' 或 'auto'")

    for quarter_name in periods:
        print(f"\n{'='*40}")
        print(f"正在处理: {quarter_name}")

        current_node_dir = os.path.join(node_base_dir, quarter_name)
        node_file_path = os.path.join(current_node_dir, partition_csv_template.format(quarter=quarter_name))
        gexf_path = os.path.join(
            current_node_dir,
            gexf_filename_template.format(quarter=quarter_name, params_tag=gexf_params_tag),
        )

        df_node = None
        try:
            if partition_source in ("csv", "auto") and os.path.exists(node_file_path):
                print(f"  -> 读取节点 CSV: {os.path.basename(node_file_path)}")
                df_node = pd.read_csv(node_file_path, encoding="utf-8-sig", dtype={"user_id": str})
                df_node.columns = df_node.columns.str.strip()
            elif partition_source == "csv":
                print(f"  [跳过] 指定 csv 但文件不存在: {node_file_path}")
                continue

            if df_node is None and partition_source in ("gexf", "auto"):
                if os.path.exists(gexf_path):
                    print(f"  -> 从 GEXF 恢复节点（无需重跑 Louvain）: {os.path.basename(gexf_path)}")
                    df_node = _nodes_dataframe_from_top1pct_gexf(gexf_path)
                elif partition_source == "gexf":
                    print(f"  [跳过] 指定 gexf 但文件不存在: {gexf_path}")
                    continue

            if df_node is None:
                print(
                    f"  [跳过] 未找到节点来源。CSV: {node_file_path}\n"
                    f"         GEXF: {gexf_path}\n"
                    f"         可将 partition_source='gexf' 并检查 gexf_params_tag 是否与当时一致。"
                )
                continue

            if "user_id" not in df_node.columns:
                raise ValueError(f"缺少列 user_id，现有列: {list(df_node.columns)}")

            df_node["user_id"] = df_node["user_id"].astype(str).str.strip()
            if "community_id" in df_node.columns:
                n_miss = int(df_node["community_id"].isna().sum())
                if n_miss:
                    print(f"  [警告] 有 {n_miss} 行缺少 community_id，请确认 GEXF/CSV 含 Louvain 社团字段")
            df_node["政客bias"] = np.nan
            df_node["媒体bias"] = np.nan

            pol_file_path = os.path.join(
                politician_dir, bias_csv_template.format(quarter=quarter_name)
            )
            pol_bias_dict = {}
            if os.path.exists(pol_file_path):
                print(f"  -> 读取政客Bias: {os.path.basename(pol_file_path)}")
                df_pol = pd.read_csv(pol_file_path, encoding="utf-8-sig", dtype=str)
                pol_bias_dict = _bias_lookup_dict_from_table(
                    df_pol, ("retweeted_user_id", "user_id")
                )
                if not pol_bias_dict:
                    print(f"  [错误] 政客表无法构建映射，列名: {list(df_pol.columns)}")
            else:
                print(f"  [警告] 政客文件缺失: {pol_file_path}")

            media_file_path = os.path.join(
                media_dir, bias_csv_template.format(quarter=quarter_name)
            )
            media_bias_dict = {}
            if os.path.exists(media_file_path):
                print(f"  -> 读取媒体Bias: {os.path.basename(media_file_path)}")
                df_media = pd.read_csv(media_file_path, encoding="utf-8-sig", dtype=str)
                media_bias_dict = _bias_lookup_dict_from_table(
                    df_media, ("user_id", "retweeted_user_id")
                )
                if not media_bias_dict:
                    print(f"  [错误] 媒体表无法构建映射，列名: {list(df_media.columns)}")
            else:
                print(f"  [警告] 媒体文件缺失: {media_file_path}")

            print("  -> 正在匹配并填充 Bias 分数...")
            if pol_bias_dict:
                df_node["政客bias"] = df_node["user_id"].map(pol_bias_dict)
            if media_bias_dict:
                df_node["媒体bias"] = df_node["user_id"].map(media_bias_dict)

            output_filename = f"{quarter_name}_top1pct_社团划分结果_补充bias.csv"
            output_path = os.path.join(current_node_dir, output_filename)
            df_node.to_csv(output_path, index=False, encoding="utf-8-sig")

            pol_count = int(df_node["政客bias"].notna().sum())
            media_count = int(df_node["媒体bias"].notna().sum())
            print(f"  -> 保存成功: {output_filename}")
            print(f"     成功匹配政客Bias节点数: {pol_count}")
            print(f"     成功匹配媒体Bias节点数: {media_count}")

        except Exception as e:
            print(f"  [异常中断] 处理 {quarter_name} 时发生错误: {e}")
            traceback.print_exc()

    print("\n全部处理完成。")

# Stage 5: classify the attached ideology scores.
def classify_community_node_ideology(
    periods=None,
    base_dir=project_path('outputs', 'analyses/转发网络/季度合并_Top1Percent度数网络提取/季度社团Hub分析'),
    input_csv_template="{quarter}_top1pct_社团划分结果_补充bias.csv",
    output_csv_template="{quarter}_top1pct_社团划分结果_完成分类.csv",
):
    """Classify politician and media node scores using the configured intervals.
    
    Read *_补充bias.csv and write *_完成分类.csv. Preserve continuous scores and
    the original CSV category-column names. Media labels match downstream
    COLOR_MAP_MEDIA keys such as Extreme bias Left and Left leaning.
    """

    def classify_politician(score):
        if pd.isna(score):
            return None
        try:
            s = float(score)
        except (TypeError, ValueError):
            return None
        th_n, th_p = -1 / 3, 1 / 3
        if -1 <= s < th_n:
            return "Left"
        if th_n <= s <= th_p:
            return "Center"
        if th_p < s <= 1:
            return "Right"
        return None

    def classify_media(score):
        """Use the configured media-score intervals and downstream media-legend labels."""
        if pd.isna(score):
            return None
        try:
            s = float(score)
        except (TypeError, ValueError):
            return None
        if -3 <= s < -2.5:
            return "Extreme bias Left"
        if -2.5 <= s < -1.5:
            return "Left"
        if -1.5 <= s < -0.5:
            return "Left leaning"
        if -0.5 <= s < 0.5:
            return "Center"
        if 0.5 <= s < 1.5:
            return "Right leaning"
        if 1.5 <= s < 2.5:
            return "Right"
        if 2.5 <= s <= 3:
            return "Extreme bias right"
        return None

    if periods is None:
        periods = _top1pct_default_quarters()

    for quarter_name in periods:
        print(f"\n{'='*40}")
        print(f"正在处理分类: {quarter_name}")

        current_dir = os.path.join(base_dir, quarter_name)
        input_filename = input_csv_template.format(quarter=quarter_name)
        input_path = os.path.join(current_dir, input_filename)

        if not os.path.exists(input_path):
            print(f"  [跳过] 找不到输入文件: {input_path}")
            print("  请先成功运行「补充 Bias」步骤。")
            continue

        try:
            print("  -> 读取文件...")
            df = pd.read_csv(input_path, encoding="utf-8-sig", dtype={"user_id": str})
            df.columns = df.columns.str.strip()

            if "政客bias" not in df.columns or "媒体bias" not in df.columns:
                raise ValueError(f"缺少 政客bias/媒体bias 列，现有: {list(df.columns)}")

            df["政客bias"] = pd.to_numeric(df["政客bias"], errors="coerce")
            df["媒体bias"] = pd.to_numeric(df["媒体bias"], errors="coerce")

            print("  -> 正在计算分类...")
            df["政客政治倾向分类"] = df["政客bias"].apply(classify_politician)
            df["媒体政治倾向分类"] = df["媒体bias"].apply(classify_media)

            print("     [统计预览]")
            print(f"     政客分类分布: {df['政客政治倾向分类'].value_counts(dropna=False).to_dict()}")
            print(f"     媒体分类分布: {df['媒体政治倾向分类'].value_counts(dropna=False).to_dict()}")

            output_filename = output_csv_template.format(quarter=quarter_name)
            output_path = os.path.join(current_dir, output_filename)
            df.to_csv(output_path, index=False, encoding="utf-8-sig")
            print(f"  -> 保存成功: {output_filename}")

        except Exception as e:
            print(f"  [错误] 处理失败: {e}")
            traceback.print_exc()

    print("\n所有季度分类处理完成。")


def _node_attr_value_for_gexf(val):
    """Convert a DataFrame cell to a NetworkX/GEXF scalar; return None for invalid values."""
    if val is None:
        return None
    if isinstance(val, float) and np.isnan(val):
        return None
    if pd.isna(val):
        return None
    if isinstance(val, (np.floating, float)):
        return float(val)
    if isinstance(val, (np.integer, int)):
        return int(val)
    s = str(val).strip()
    return s if s and s.lower() != "nan" else None


def export_gexf_with_ideology_attributes(
    periods=None,
    base_dir=project_path('outputs', 'analyses/转发网络/季度合并_Top1Percent度数网络提取/季度社团Hub分析'),
    gexf_params_tag="res1.0_seed42",
    gexf_filename_template="{quarter}_{params_tag}.gexf",
    output_suffix="_with_political_attributes",
    completed_csv_template="{quarter}_top1pct_社团划分结果_完成分类.csv",
    attr_columns=(
        "政客bias",
        "媒体bias",
        "政客政治倾向分类",
        "媒体政治倾向分类",
    ),
):
    """Export a new GEXF with continuous and categorical ideology attributes.
    
    Read the original Louvain GEXF and the classified node CSV, match by user_id
    and attach politician/media scores and categories without changing topology.
    Preserve the original GEXF and write a separate file in the same directory.
    
    Inputs: {quarter}_{params_tag}.gexf and
    {quarter}_top1pct_社团划分结果_完成分类.csv.
    Output: {quarter}_{params_tag}{output_suffix}.gexf.
    """
    if periods is None:
        periods = _top1pct_default_quarters()

    for quarter_name in periods:
        print(f"\n{'='*40}")
        print(f"GEXF 写入政治属性: {quarter_name}")

        current_dir = os.path.join(base_dir, quarter_name)
        gexf_in = os.path.join(
            current_dir,
            gexf_filename_template.format(quarter=quarter_name, params_tag=gexf_params_tag),
        )
        csv_path = os.path.join(
            current_dir,
            completed_csv_template.format(quarter=quarter_name),
        )
        base_name, ext = os.path.splitext(os.path.basename(gexf_in))
        if ext.lower() != ".gexf":
            base_name = os.path.basename(gexf_in)
            ext = ".gexf"
        gexf_out = os.path.join(current_dir, f"{base_name}{output_suffix}{ext}")

        if not os.path.exists(gexf_in):
            print(f"  [跳过] 原 GEXF 不存在: {gexf_in}")
            continue
        if not os.path.exists(csv_path):
            print(f"  [跳过] 完成分类 CSV 不存在: {csv_path}")
            print("  请先运行「补充 Bias」与「政治倾向类别划分」。")
            continue

        try:
            G = nx.read_gexf(gexf_in)
            df = pd.read_csv(csv_path, encoding="utf-8-sig", dtype={"user_id": str})
            df.columns = df.columns.str.strip()

            if "user_id" not in df.columns:
                raise ValueError(f"CSV 缺少 user_id，现有列: {list(df.columns)}")

            missing_cols = [c for c in attr_columns if c not in df.columns]
            if missing_cols:
                raise ValueError(f"CSV 缺少列: {missing_cols}")

            df["user_id"] = df["user_id"].astype(str).str.strip()
            df = df.drop_duplicates(subset=["user_id"], keep="first")
            lookup = df.set_index("user_id")

            n_matched = 0
            n_attrs_set = 0
            for node in G.nodes():
                uid = str(node).strip()
                if uid not in lookup.index:
                    continue
                row = lookup.loc[uid]
                if isinstance(row, pd.DataFrame):
                    row = row.iloc[0]
                n_matched += 1
                for col in attr_columns:
                    v = _node_attr_value_for_gexf(row[col])
                    if v is not None:
                        G.nodes[node][col] = v
                        n_attrs_set += 1

            nx.write_gexf(G, gexf_out, encoding="utf-8")
            print(f"  -> 已写入节点数（在 CSV 中有记录）: {n_matched}")
            print(f"  -> 已写入属性条数（非空）: {n_attrs_set}")
            print(f"  -> 保存: {gexf_out}")

        except Exception as e:
            print(f"  [错误] {quarter_name}: {e}")
            traceback.print_exc()

    print("\n全部 GEXF（含政治属性）导出完成。")




# Use Agg for file output without the Windows TkAgg foreground-window issue.
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import os

def rgb_to_hex(rgb_str):
    """Convert an rgb(r, g, b) string to a Matplotlib color tuple."""
    try:
        rgb_values = rgb_str.replace('rgb(', '').replace(')', '').split(',')
        return tuple(int(v.strip()) / 255.0 for v in rgb_values)
    except:
        return (0.5, 0.5, 0.5)


# Completed political-ideology distributions for each period's three largest communities.
# Top1% degree-network variant introduced on 2026-04-08.
def analyze_community_political_distribution_top1_percent(periods, base_root=project_path('outputs', f'analyses/转发网络/季度合并_Top1Percent度数网络提取/季度社团Hub分析')):
    # Color configuration.
    # Colors for seven media categories.
    COLOR_MAP_MEDIA = {
        'Extreme bias Left': rgb_to_hex('rgb(0, 51, 102)'),
        'Left': rgb_to_hex('rgb(51, 102, 153)'),
        'Left leaning': rgb_to_hex('rgb(181, 216, 243)'),
        'Center': rgb_to_hex('rgb(240, 230, 140)'),
        'Right leaning': rgb_to_hex('rgb(255, 153, 153)'),
        'Right': rgb_to_hex('rgb(204, 102, 102)'),
        'Extreme bias right': rgb_to_hex('rgb(139, 26, 26)'),
        'DEFAULT': rgb_to_hex('rgb(128, 128, 128)')
    }
    
    # Colors for three politician categories.
    COLOR_MAP_POLITICIAN = {
        'Left': rgb_to_hex('rgb(51, 102, 153)'),
        'Center': rgb_to_hex('rgb(240, 230, 140)'),
        'Right': rgb_to_hex('rgb(204, 102, 102)'),
        'DEFAULT': rgb_to_hex('rgb(128, 128, 128)')
    }

    # Prepare a lowercase color-key lookup to handle capitalization differences.
    COLOR_MAP_MEDIA_LOWER = {k.lower(): v for k, v in COLOR_MAP_MEDIA.items()}

    # Use shared histogram bins and the global peak of stacked category counts to set comparable y-axis limits.
    top_n = 3
    n_bins_pol, pol_range = 20, (-1, 1)
    n_bins_med, med_range = 30, (-3, 3)
    edges_pol = np.linspace(pol_range[0], pol_range[1], n_bins_pol + 1)
    edges_med = np.linspace(med_range[0], med_range[1], n_bins_med + 1)

    period_data = []  # (period, period_folder, df, top_comm_ids)
    max_pol_y = 0.0
    max_med_y = 0.0

    for period in periods:
        print(f"\n>>> 正在处理季度: {period}")
        period_folder = os.path.join(base_root, period)
        input_csv_path = os.path.join(period_folder, f"{period}_top1pct_社团划分结果_完成分类.csv")

        if not os.path.exists(input_csv_path):
            print(f"文件不存在: {input_csv_path}")
            continue

        df = pd.read_csv(input_csv_path, encoding='utf-8-sig')

        df['政客政治倾向分类'] = df['政客政治倾向分类'].astype(str).str.strip()
        df['媒体分类_match'] = df['媒体政治倾向分类'].astype(str).str.strip().str.lower()

        top_comm_ids = df['community_id'].value_counts().head(top_n).index.tolist()
        period_data.append((period, period_folder, df, top_comm_ids))

        for cid in top_comm_ids:
            sub_pol = df[(df['community_id'] == cid) & (df['政客bias'].notna())]
            total_pol = np.zeros(n_bins_pol, dtype=float)
            for label, color in COLOR_MAP_POLITICIAN.items():
                if label == 'DEFAULT':
                    continue
                cat_data = sub_pol[sub_pol['政客政治倾向分类'] == label]['政客bias']
                if cat_data.empty:
                    continue
                c, _ = np.histogram(cat_data, bins=edges_pol)
                total_pol += c
            max_pol_y = max(max_pol_y, float(total_pol.max()) if len(total_pol) else 0.0)

            sub_med = df[(df['community_id'] == cid) & (df['媒体bias'].notna())]
            total_med = np.zeros(n_bins_med, dtype=float)
            for label_name, color in COLOR_MAP_MEDIA.items():
                if label_name == 'DEFAULT':
                    continue
                label_lower = label_name.lower()
                cat_data = sub_med[sub_med['媒体分类_match'] == label_lower]['媒体bias']
                if cat_data.empty:
                    continue
                c, _ = np.histogram(cat_data, bins=edges_med)
                total_med += c
            max_med_y = max(max_med_y, float(total_med.max()) if len(total_med) else 0.0)

    y_lim_pol = max(max_pol_y * 1.05, 1.0)
    y_lim_med = max(max_med_y * 1.05, 1.0)
    print(f"\n[统一 Y 轴] 政客子图 ylim 上限: {y_lim_pol:.1f}；媒体子图 ylim 上限: {y_lim_med:.1f}")

    for period, period_folder, df, top_comm_ids in period_data:
        # Task 1: politician-based scores.
        fig1, axes1 = plt.subplots(1, top_n, figsize=(18, 5))
        fig1.suptitle(f'{period} - Politician Bias Distribution (Top 3 Communities)', fontsize=16, fontweight='bold')

        for i, cid in enumerate(top_comm_ids):
            ax = axes1[i]
            sub_df = df[(df['community_id'] == cid) & (df['政客bias'].notna())]

            for label, color in COLOR_MAP_POLITICIAN.items():
                if label == 'DEFAULT':
                    continue
                cat_data = sub_df[sub_df['政客政治倾向分类'] == label]['政客bias']
                if not cat_data.empty:
                    ax.hist(cat_data, bins=edges_pol, color=color, alpha=0.7, label=label)

            ax.set_title(f'Comm ID: {cid}\nNodes: {len(df[df["community_id"]==cid])}')
            ax.set_xlim(-1, 1)
            ax.set_ylim(0, y_lim_pol)
            ax.set_xlabel('Politician Bias')
            if i == 0:
                ax.set_ylabel('User Count')

        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        plt.savefig(os.path.join(period_folder, f"{period}_Politician_Bias_Top3.png"), dpi=300)
        plt.close()

        # Task 2: media-based scores.
        fig2, axes2 = plt.subplots(1, top_n, figsize=(18, 5))
        fig2.suptitle(f'{period} - Media Bias Distribution (Top 3 Communities)', fontsize=16, fontweight='bold')

        for i, cid in enumerate(top_comm_ids):
            ax = axes2[i]
            sub_df = df[(df['community_id'] == cid) & (df['媒体bias'].notna())]

            for label_name, color in COLOR_MAP_MEDIA.items():
                if label_name == 'DEFAULT':
                    continue
                label_lower = label_name.lower()
                cat_data = sub_df[sub_df['媒体分类_match'] == label_lower]['媒体bias']

                if not cat_data.empty:
                    ax.hist(cat_data, bins=edges_med, color=color, alpha=0.7, label=label_name)

            ax.set_title(f'Comm ID: {cid}\nNodes: {len(df[df["community_id"]==cid])}')
            ax.set_xlim(-3, 3)
            ax.set_ylim(0, y_lim_med)
            ax.set_xlabel('Media Bias')
            if i == 0:
                ax.set_ylabel('User Count')

        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        plt.savefig(os.path.join(period_folder, f"{period}_Media_Bias_Top3.png"), dpi=300)
        plt.close()

        print(f"   -> {period} 的图像已更新完成。")

    print("\n[完成] 所有图表已按要求重新生成。")



# Plot pooled distributions; the earlier variant plots each window separately.
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import os
# Pooled political-ideology distribution plot complete.
# Top1% degree-network variant introduced on 2026-04-08.
def plot_merged_bias_distribution_top1_percent(periods, base_root=project_path('outputs', f'analyses/转发网络/季度合并_Top1Percent度数网络提取/季度社团Hub分析')):
    # 1. Preserve the configured colors.
    def rgb_to_hex(rgb_str):
        try:
            rgb_values = rgb_str.replace('rgb(', '').replace(')', '').split(',')
            return tuple(int(v.strip()) / 255.0 for v in rgb_values)
        except: return (0.5, 0.5, 0.5)

    COLOR_MAP_MEDIA = {
        'Extreme bias Left': rgb_to_hex('rgb(0, 51, 102)'),
        'Left': rgb_to_hex('rgb(51, 102, 153)'),
        'Left leaning': rgb_to_hex('rgb(181, 216, 243)'),
        'Center': rgb_to_hex('rgb(240, 230, 140)'),
        'Right leaning': rgb_to_hex('rgb(255, 153, 153)'),
        'Right': rgb_to_hex('rgb(204, 102, 102)'),
        'Extreme bias right': rgb_to_hex('rgb(139, 26, 26)')
    }
    COLOR_MAP_POLITICIAN = {
        'Left': rgb_to_hex('rgb(51, 102, 153)'),
        'Center': rgb_to_hex('rgb(240, 230, 140)'),
        'Right': rgb_to_hex('rgb(204, 102, 102)')
    }

    # 2. Combine the period-specific records.
    merged_data = {0: [], 1: [], 2: []}
    periods_loaded = []
    for period in periods:
        input_csv_path = os.path.join(base_root, period, f"{period}_top1pct_社团划分结果_完成分类.csv")
        if not os.path.exists(input_csv_path):
            continue
        df = pd.read_csv(input_csv_path, encoding='utf-8-sig')
        df['政客分类'] = df['政客政治倾向分类'].astype(str).str.strip()
        df['媒体分类'] = df['媒体政治倾向分类'].astype(str).str.strip().str.lower()
        df.loc[df['媒体分类'].isin(['nan', 'none', 'nat', '']), '媒体分类'] = np.nan
        top_comm_ids = df['community_id'].value_counts().head(3).index.tolist()
        for rank, cid in enumerate(top_comm_ids):
            sub_df = df[df['community_id'] == cid].copy()
            merged_data[rank].append(sub_df)
        periods_loaded.append(period)

    # For an empty plot, inspect missing input files, missing bias values and category/color-key mismatches.
    diag_parts = [pd.concat(merged_data[r], ignore_index=True) for r in range(3) if merged_data[r]]
    if not diag_parts:
        q0 = periods[0] if periods else "季度名"
        print(
            "[诊断 Merged Top1%] 无任何合并数据：请确认 base_root 下各季度存在 "
            f"{q0}_top1pct_社团划分结果_完成分类.csv 等文件。"
        )
    else:
        diag_df = pd.concat(diag_parts, ignore_index=True)
        pol_n = int(diag_df["政客bias"].notna().sum()) if "政客bias" in diag_df.columns else 0
        med_n = int(diag_df["媒体bias"].notna().sum()) if "媒体bias" in diag_df.columns else 0
        print(
            f"[诊断 Merged Top1%] 读入季度数={len(periods_loaded)}/{len(periods)}, "
            f"合并行数={len(diag_df)}, 政客bias非空={pol_n}, 媒体bias非空={med_n}"
        )
        if "政客政治倾向分类" in diag_df.columns:
            pol_vc = diag_df["政客政治倾向分类"].dropna().astype(str).str.strip().value_counts().head(8)
            print(f"[诊断 Merged Top1%] 政客政治倾向分类(原始)出现次数 Top: {pol_vc.to_dict()}")
        if "媒体政治倾向分类" in diag_df.columns:
            med_vc = (
                diag_df["媒体政治倾向分类"].dropna().astype(str).str.strip().str.lower().value_counts().head(12)
            )
            print(f"[诊断 Merged Top1%] 媒体政治倾向分类(小写)出现次数 Top: {med_vc.to_dict()}")
        expected_med = {k.lower() for k in COLOR_MAP_MEDIA}
        if med_n > 0 and "媒体政治倾向分类" in diag_df.columns:
            raw_lower = diag_df["媒体政治倾向分类"].dropna().astype(str).str.strip().str.lower()
            unmatched = raw_lower[~raw_lower.isin(expected_med) & ~raw_lower.isin(["nan", "none", "nat", ""])]
            if len(unmatched):
                um = unmatched.value_counts().head(8)
                print(
                    "[诊断 Merged Top1%] 媒体分类与 COLOR_MAP 7 类不匹配（无法着色直方图）的取值: "
                    f"{um.to_dict()} —— 请统一 CSV 与 Extreme bias Left / Left / … 等英文标签。"
                )

    # Use the same bins as analyze_community_political_distribution_top1_percent for comparable counts.
    n_bins_pol, pol_range = 20, (-1, 1)
    n_bins_med, med_range = 30, (-3, 3)
    edges_pol = np.linspace(pol_range[0], pol_range[1], n_bins_pol + 1)
    edges_med = np.linspace(med_range[0], med_range[1], n_bins_med + 1)

    max_pol_y = 0.0
    max_med_y = 0.0
    for rank in range(3):
        all_rank_df = pd.concat(merged_data[rank]) if merged_data[rank] else pd.DataFrame()
        if all_rank_df.empty:
            continue
        pol_df = all_rank_df[all_rank_df['政客bias'].notna()]
        total_pol = np.zeros(n_bins_pol, dtype=float)
        for label, color in COLOR_MAP_POLITICIAN.items():
            cat_data = pol_df[pol_df['政客分类'].str.lower() == label.lower()]['政客bias']
            if cat_data.empty:
                continue
            c, _ = np.histogram(cat_data, bins=edges_pol)
            total_pol += c
        max_pol_y = max(max_pol_y, float(total_pol.max()) if len(total_pol) else 0.0)

        med_df = all_rank_df[all_rank_df['媒体bias'].notna()]
        total_med = np.zeros(n_bins_med, dtype=float)
        for label_orig, color in COLOR_MAP_MEDIA.items():
            label_lower = label_orig.lower()
            cat_data = med_df[med_df['媒体分类'] == label_lower]['媒体bias']
            if cat_data.empty:
                continue
            c, _ = np.histogram(cat_data, bins=edges_med)
            total_med += c
        max_med_y = max(max_med_y, float(total_med.max()) if len(total_med) else 0.0)

    y_lim_pol = max(max_pol_y * 1.05, 1.0)
    y_lim_med = max(max_med_y * 1.05, 1.0)
    print(f"\n[统一 Y 轴] 政客子图 ylim 上限: {y_lim_pol:.1f}；媒体子图 ylim 上限: {y_lim_med:.1f}")

    # 3. Configure the panel layout.
    # Adjust figure dimensions and resolution.
    fig, axes = plt.subplots(2, 3, figsize=(20, 12), dpi=150) 
    
    # Position the main title above the panels.
    fig.suptitle('Merged Political Bias Distribution (6 Quarters Aggregated)', 
                 fontsize=24, fontweight='bold', y=0.96)

    col_titles = ['Top 1 Community', 'Top 2 Community', 'Top 3 Community']

    for rank in range(3):
        all_rank_df = pd.concat(merged_data[rank]) if merged_data[rank] else pd.DataFrame()
        ax_pol = axes[0, rank]
        ax_med = axes[1, rank]
        ax_pol.set_title(col_titles[rank], fontsize=18, fontweight='bold', pad=20)
        ax_pol.set_xlim(-1, 1)
        ax_pol.set_ylim(0, y_lim_pol)
        ax_med.set_xlim(-3, 3)
        ax_med.set_ylim(0, y_lim_med)
        if all_rank_df.empty:
            continue

        # First row: politician-based scores.
        pol_df = all_rank_df[all_rank_df['政客bias'].notna()]
        for label, color in COLOR_MAP_POLITICIAN.items():
            cat_data = pol_df[pol_df['政客分类'].str.lower() == label.lower()]['政客bias']
            if not cat_data.empty:
                ax_pol.hist(cat_data, bins=edges_pol, color=color, alpha=0.7, label=label)
        
        if rank == 0: 
            ax_pol.set_ylabel('Politicians\n\nUser Count', fontsize=16, fontweight='bold')
        ax_pol.grid(axis='y', linestyle='--', alpha=0.3)

        # Second row: media-based scores.
        med_df = all_rank_df[all_rank_df['媒体bias'].notna()]
        for label_orig, color in COLOR_MAP_MEDIA.items():
            label_lower = label_orig.lower()
            cat_data = med_df[med_df['媒体分类'] == label_lower]['媒体bias']
            if not cat_data.empty:
                ax_med.hist(cat_data, bins=edges_med, color=color, alpha=0.7, label=label_orig)
        
        ax_med.set_xlabel('Bias Score', fontsize=14)
        if rank == 0: 
            ax_med.set_ylabel('Media\n\nUser Count', fontsize=16, fontweight='bold')
        ax_med.grid(axis='y', linestyle='--', alpha=0.3)

    # 4. Refine legend placement and panel spacing.
    # Place legends outside the data area or adjust their size.
    # axes[0, 2].legend(title="Politician Category", loc='upper right', fontsize=10, frameon=True)
    # axes[1, 2].legend(title="Media Category", loc='upper right', fontsize=10, frameon=True)

    # Use subplots_adjust to set panel spacing explicitly.
    # top reserves title space; hspace and wspace control panel gaps.
    plt.subplots_adjust(top=0.88, bottom=0.08, left=0.1, right=0.95, hspace=0.3, wspace=0.25)
    
    save_path = os.path.join(base_root, "Merged_Political_Media_Bias_Distribution_Clean.png")
    plt.savefig(save_path, bbox_inches='tight') # Use bbox_inches='tight' to retain labels in the saved image.
    print(f"清爽版合并图表已生成：{save_path}")
    plt.show()


# This version was used for Figure 4b.
# Plot media bias separately for each window; overlay Top1 and Top2, hatch Top1 and omit Top3.
def plot_quarterly_media_bias_distribution_top1_top2_top1_percent(
    periods,
    base_root=project_path('outputs', f'analyses/转发网络/季度合并_Top1Percent度数网络提取/季度社团Hub分析')
):
    """Plot each window's Top1 and Top2 media-bias distributions on a shared axis.
    
    Create one figure per window without pooling periods. Hatch the Top1 bars
    and leave Top2 unhatched. Use the pooled version's colors, input data and
    histogram bins. Do not plot politician scores or Top3 in this variant.
    """
    # 1. Preserve the configured colors.
    def rgb_to_hex(rgb_str):
        try:
            rgb_values = rgb_str.replace('rgb(', '').replace(')', '').split(',')
            return tuple(int(v.strip()) / 255.0 for v in rgb_values)
        except:
            return (0.5, 0.5, 0.5)

    COLOR_MAP_MEDIA = {
        'Extreme bias Left': rgb_to_hex('rgb(0, 51, 102)'),
        'Left': rgb_to_hex('rgb(51, 102, 153)'),
        'Left leaning': rgb_to_hex('rgb(181, 216, 243)'),
        'Center': rgb_to_hex('rgb(240, 230, 140)'),
        'Right leaning': rgb_to_hex('rgb(255, 153, 153)'),
        'Right': rgb_to_hex('rgb(204, 102, 102)'),
        'Extreme bias right': rgb_to_hex('rgb(139, 26, 26)')
    }

    # Use the same bins as analyze_community_political_distribution_top1_percent for comparable counts.
    n_bins_med, med_range = 30, (-3, 3)
    edges_med = np.linspace(med_range[0], med_range[1], n_bins_med + 1)

    # 2. First pass: compute a common y-axis limit across all windows.
    global_max_med_y = 0.0
    periods_loaded = 0
    for period in periods:
        input_csv_path = os.path.join(base_root, period, f"{period}_top1pct_社团划分结果_完成分类.csv")
        if not os.path.exists(input_csv_path):
            continue
        df = pd.read_csv(input_csv_path, encoding='utf-8-sig')
        if df.empty:
            continue

        df['媒体分类'] = df['媒体政治倾向分类'].astype(str).str.strip().str.lower()
        df.loc[df['媒体分类'].isin(['nan', 'none', 'nat', '']), '媒体分类'] = np.nan

        top_comm_ids = df['community_id'].value_counts().head(2).index.tolist()
        if len(top_comm_ids) < 2:
            continue

        cid_top1, cid_top2 = top_comm_ids[0], top_comm_ids[1]
        for cid in (cid_top1, cid_top2):
            sub_df = df[df['community_id'] == cid]
            med_df = sub_df[sub_df['媒体bias'].notna()]
            total_med = np.zeros(n_bins_med, dtype=float)
            for label_orig in COLOR_MAP_MEDIA.keys():
                label_lower = label_orig.lower()
                cat_data = med_df[med_df['媒体分类'] == label_lower]['媒体bias']
                if cat_data.empty:
                    continue
                c, _ = np.histogram(cat_data, bins=edges_med)
                total_med += c
            global_max_med_y = max(global_max_med_y, float(total_med.max()) if len(total_med) else 0.0)
        periods_loaded += 1

    y_lim_med_global = max(global_max_med_y * 1.05, 1.0)
    print(f"\n[统一 Y 轴] 媒体子图 ylim 上限(跨所有季度 Top1/Top2): {y_lim_med_global:.1f}（读入季度数={periods_loaded}/{len(periods)}）")

    for period in periods:
        input_csv_path = os.path.join(base_root, period, f"{period}_top1pct_社团划分结果_完成分类.csv")
        if not os.path.exists(input_csv_path):
            print(f"[跳过] 文件不存在: {input_csv_path}")
            continue

        df = pd.read_csv(input_csv_path, encoding='utf-8-sig')
        if df.empty:
            print(f"[跳过] 空文件: {input_csv_path}")
            continue

        # Use the same input cleaning as the pooled version.
        df['媒体分类'] = df['媒体政治倾向分类'].astype(str).str.strip().str.lower()
        df.loc[df['媒体分类'].isin(['nan', 'none', 'nat', '']), '媒体分类'] = np.nan

        top_comm_ids = df['community_id'].value_counts().head(2).index.tolist()
        if len(top_comm_ids) < 2:
            print(f"[跳过] {period} 社团数量不足以生成 Top1+Top2 图（仅有 {len(top_comm_ids)} 个）")
            continue

        cid_top1, cid_top2 = top_comm_ids[0], top_comm_ids[1]
        sub_top1 = df[df['community_id'] == cid_top1].copy()
        sub_top2 = df[df['community_id'] == cid_top2].copy()

        # Use approximately square panels for comparison and page layout.
        fig, ax = plt.subplots(1, 1, figsize=(10, 10), dpi=150)
        ax.set_title(
            f"Media Bias Distribution (Top1 overlaid on Top2)\n{period}",
            fontsize=18,
            fontweight='bold',
            pad=14,
        )
        ax.set_xlim(med_range[0], med_range[1])
        ax.set_ylim(0, y_lim_med_global)

        def _plot_one(ax_, sub_df, *, hatch=None, alpha=0.7):
            med_df = sub_df[sub_df['媒体bias'].notna()]
            for label_orig, color in COLOR_MAP_MEDIA.items():
                label_lower = label_orig.lower()
                cat_data = med_df[med_df['媒体分类'] == label_lower]['媒体bias']
                if cat_data.empty:
                    continue
                ax_.hist(
                    cat_data,
                    bins=edges_med,
                    color=color,
                    alpha=alpha,
                    hatch=hatch,
                    edgecolor='black' if hatch else None,
                    linewidth=0.25 if hatch else 0,
                )

        # Draw Top2 first, then overlay hatched Top1.
        _plot_one(ax, sub_top2, hatch=None, alpha=0.55)
        _plot_one(ax, sub_top1, hatch='///', alpha=0.55)

        ax.set_xlabel('Bias Score', fontsize=13)
        ax.set_ylabel('Media\n\nUser Count', fontsize=15, fontweight='bold')
        ax.grid(axis='y', linestyle='--', alpha=0.3)

        plt.subplots_adjust(top=0.88, bottom=0.10, left=0.10, right=0.98)

        save_path = os.path.join(base_root, period, f"{period}_Top1Top2_Media_Bias_Distribution_Clean.png")
        plt.savefig(save_path, bbox_inches='tight')
        print(f"按季度 Top1+Top2 媒体分布图已生成：{save_path}")
        plt.show()

# Figure 4b variant without coordinate text.
# Plot media bias separately for each window; overlay Top1 and Top2, hatch Top1 and omit Top3.
def plot_top_community_media_bias_without_axes(
    periods,
    base_root=project_path('outputs', f'analyses/转发网络/季度合并_Top1Percent度数网络提取/季度社团Hub分析')
):
    """Plot per-window Top1/Top2 media-bias distributions without coordinate text.
    
    Overlay Top1 and Top2 on the same axis, hatch Top1 and leave Top2 unhatched.
    Retain the original colors, source data and bins; do not pool periods or
    include politician scores or Top3.
    """
    # 1. Preserve the configured colors.
    def rgb_to_hex(rgb_str):
        try:
            rgb_values = rgb_str.replace('rgb(', '').replace(')', '').split(',')
            return tuple(int(v.strip()) / 255.0 for v in rgb_values)
        except:
            return (0.5, 0.5, 0.5)

    COLOR_MAP_MEDIA = {
        'Extreme bias Left': rgb_to_hex('rgb(0, 51, 102)'),
        'Left': rgb_to_hex('rgb(51, 102, 153)'),
        'Left leaning': rgb_to_hex('rgb(181, 216, 243)'),
        'Center': rgb_to_hex('rgb(240, 230, 140)'),
        'Right leaning': rgb_to_hex('rgb(255, 153, 153)'),
        'Right': rgb_to_hex('rgb(204, 102, 102)'),
        'Extreme bias right': rgb_to_hex('rgb(139, 26, 26)')
    }

    # Use the same bins as analyze_community_political_distribution_top1_percent for comparable counts.
    n_bins_med, med_range = 30, (-3, 3)
    edges_med = np.linspace(med_range[0], med_range[1], n_bins_med + 1)

    # 2. First pass: compute a common y-axis limit across all windows.
    global_max_med_y = 0.0
    periods_loaded = 0
    for period in periods:
        input_csv_path = os.path.join(base_root, period, f"{period}_top1pct_社团划分结果_完成分类.csv")
        if not os.path.exists(input_csv_path):
            continue
        df = pd.read_csv(input_csv_path, encoding='utf-8-sig')
        if df.empty:
            continue

        df['媒体分类'] = df['媒体政治倾向分类'].astype(str).str.strip().str.lower()
        df.loc[df['媒体分类'].isin(['nan', 'none', 'nat', '']), '媒体分类'] = np.nan

        top_comm_ids = df['community_id'].value_counts().head(2).index.tolist()
        if len(top_comm_ids) < 2:
            continue

        cid_top1, cid_top2 = top_comm_ids[0], top_comm_ids[1]
        for cid in (cid_top1, cid_top2):
            sub_df = df[df['community_id'] == cid]
            med_df = sub_df[sub_df['媒体bias'].notna()]
            total_med = np.zeros(n_bins_med, dtype=float)
            for label_orig in COLOR_MAP_MEDIA.keys():
                label_lower = label_orig.lower()
                cat_data = med_df[med_df['媒体分类'] == label_lower]['媒体bias']
                if cat_data.empty:
                    continue
                c, _ = np.histogram(cat_data, bins=edges_med)
                total_med += c
            global_max_med_y = max(global_max_med_y, float(total_med.max()) if len(total_med) else 0.0)
        periods_loaded += 1

    y_lim_med_global = max(global_max_med_y * 1.05, 1.0)
    print(f"\n[统一 Y 轴]（不带坐标版）媒体子图 ylim 上限(跨所有季度 Top1/Top2): {y_lim_med_global:.1f}（读入季度数={periods_loaded}/{len(periods)}）")

    for period in periods:
        input_csv_path = os.path.join(base_root, period, f"{period}_top1pct_社团划分结果_完成分类.csv")
        if not os.path.exists(input_csv_path):
            print(f"[跳过] 文件不存在: {input_csv_path}")
            continue

        df = pd.read_csv(input_csv_path, encoding='utf-8-sig')
        if df.empty:
            print(f"[跳过] 空文件: {input_csv_path}")
            continue

        # Use the same input cleaning as the pooled version.
        df['媒体分类'] = df['媒体政治倾向分类'].astype(str).str.strip().str.lower()
        df.loc[df['媒体分类'].isin(['nan', 'none', 'nat', '']), '媒体分类'] = np.nan

        top_comm_ids = df['community_id'].value_counts().head(2).index.tolist()
        if len(top_comm_ids) < 2:
            print(f"[跳过] {period} 社团数量不足以生成 Top1+Top2 图（仅有 {len(top_comm_ids)} 个）")
            continue

        cid_top1, cid_top2 = top_comm_ids[0], top_comm_ids[1]
        sub_top1 = df[df['community_id'] == cid_top1].copy()
        sub_top2 = df[df['community_id'] == cid_top2].copy()

        # Use approximately square panels for comparison and page layout.
        fig, ax = plt.subplots(1, 1, figsize=(10, 10), dpi=150)
        # Omit titles and axis-label text.
        ax.set_xlim(med_range[0], med_range[1])
        ax.set_ylim(0, y_lim_med_global)

        def _plot_one(ax_, sub_df, *, hatch=None, alpha=0.7):
            med_df = sub_df[sub_df['媒体bias'].notna()]
            for label_orig, color in COLOR_MAP_MEDIA.items():
                label_lower = label_orig.lower()
                cat_data = med_df[med_df['媒体分类'] == label_lower]['媒体bias']
                if cat_data.empty:
                    continue
                ax_.hist(
                    cat_data,
                    bins=edges_med,
                    color=color,
                    alpha=alpha,
                    hatch=hatch,
                    edgecolor='black' if hatch else None,
                    linewidth=0.25 if hatch else 0,
                )

        # Draw Top2 first, then overlay hatched Top1.
        _plot_one(ax, sub_top2, hatch=None, alpha=0.55)
        _plot_one(ax, sub_top1, hatch='///', alpha=0.55)

        ax.grid(axis='y', linestyle='--', alpha=0.3)

        # Keep axis and tick lines while hiding tick-label text.
        ax.tick_params(axis='both', which='both', labelbottom=False, labelleft=False)
        ax.tick_params(axis='both', which='both', length=6, width=1)

        plt.subplots_adjust(top=0.88, bottom=0.10, left=0.10, right=0.98)

        save_path = os.path.join(base_root, period, f"{period}_Top1Top2_Media_Bias_Distribution_不带坐标版.png")
        plt.savefig(save_path, bbox_inches='tight')
        print(f"按季度 Top1+Top2 媒体分布图已生成：{save_path}")
        plt.show()

# Function added on 2026-08-13.
# Plot the Center group's media-bias distribution separately to show its within-category detail.
def plot_quarterly_center_media_bias_distribution_top1_top2_top1_percent(
    periods,
    base_root=project_path('outputs', f'analyses/转发网络/季度合并_Top1Percent度数网络提取/季度社团Hub分析')
):
    """Plot Center users' media-bias distributions separately for each window.
    
    Compare Top1 and Top2 communities and hatch the Top1 distribution.
    """

    COLOR_CENTER = (240/255, 230/255, 140/255)

    # Bias-score range.
    n_bins = 20
    center_range = (-0.5, 0.5)
    edges = np.linspace(center_range[0], center_range[1], n_bins + 1)


    # =========================
    # First pass: determine a shared y-axis limit.
    # =========================

    global_max_y = 0

    for period in periods:

        input_csv_path = os.path.join(
            base_root,
            period,
            f"{period}_top1pct_社团划分结果_完成分类.csv"
        )

        if not os.path.exists(input_csv_path):
            continue

        df = pd.read_csv(
            input_csv_path,
            encoding='utf-8-sig'
        )

        if df.empty:
            continue


        df['媒体分类'] = (
            df['媒体政治倾向分类']
            .astype(str)
            .str.strip()
            .str.lower()
        )


        top_comm_ids = (
            df['community_id']
            .value_counts()
            .head(2)
            .index
            .tolist()
        )


        if len(top_comm_ids)<2:
            continue


        for cid in top_comm_ids:

            sub = df[
                df['community_id']==cid
            ]

            center_data = sub[
                (sub['媒体分类']=='center')
                &
                (sub['媒体bias'].notna())
            ]['媒体bias']


            if len(center_data)>0:

                count,_ = np.histogram(
                    center_data,
                    bins=edges
                )

                global_max_y=max(
                    global_max_y,
                    count.max()
                )


    y_lim=max(global_max_y*1.1,1)



    # =========================
    # Second pass: draw the figures.
    # =========================

    for period in periods:


        input_csv_path = os.path.join(
            base_root,
            period,
            f"{period}_top1pct_社团划分结果_完成分类.csv"
        )


        if not os.path.exists(input_csv_path):
            continue


        df=pd.read_csv(
            input_csv_path,
            encoding='utf-8-sig'
        )


        if df.empty:
            continue


        df['媒体分类']=(
            df['媒体政治倾向分类']
            .astype(str)
            .str.strip()
            .str.lower()
        )


        top_comm_ids=(
            df['community_id']
            .value_counts()
            .head(2)
            .index
            .tolist()
        )


        if len(top_comm_ids)<2:
            continue


        cid_top1,cid_top2=top_comm_ids[0],top_comm_ids[1]


        sub_top1=df[
            df['community_id']==cid_top1
        ]

        sub_top2=df[
            df['community_id']==cid_top2
        ]


        fig,ax=plt.subplots(
            figsize=(8,6),
            dpi=150
        )


        def plot_center(sub,hatch=None,alpha=0.6):

            center_data=sub[
                (sub['媒体分类']=='center')
                &
                (sub['媒体bias'].notna())
            ]['媒体bias']


            if len(center_data)>0:

                ax.hist(
                    center_data,
                    bins=edges,
                    color=COLOR_CENTER,
                    alpha=alpha,
                    hatch=hatch,
                    edgecolor='black' if hatch else None,
                    linewidth=0.4 if hatch else 0
                )


        # Draw Top2 underneath.
        plot_center(
            sub_top2,
            hatch=None,
            alpha=0.6
        )


        # Overlay Top1 with hatching.
        plot_center(
            sub_top1,
            hatch='///',
            alpha=0.6
        )


        ax.set_title(
            f"Center Media Bias Distribution\n{period}",
            fontsize=16,
            fontweight='bold'
        )


        ax.set_xlabel(
            "Bias Score",
            fontsize=13
        )

        ax.set_ylabel(
            "Center User Count",
            fontsize=13
        )


        ax.set_xlim(
            center_range[0],
            center_range[1]
        )

        ax.set_ylim(
            0,
            y_lim
        )


        ax.grid(
            axis='y',
            linestyle='--',
            alpha=0.3
        )


        save_path=os.path.join(
            base_root,
            period,
            f"{period}_Center_Media_Bias_Distribution.png"
        )


        plt.savefig(
            save_path,
            bbox_inches='tight'
        )

        plt.close()

        print(
            f"Center中立群体分布图已生成:{save_path}"
        )




# Top3-community core-node extraction complete.
# ============================================================
# Extract each period's Top3-community core-node IDs from existing result files.
# ============================================================
def extract_top3_community_core_nodes_by_quarter_top2_percent(
    periods,
    base_root=project_path('outputs', f'analyses/转发网络/季度合并_Top2Percent度数网络提取/季度社团Hub分析'),
    resolution=1.0,
    random_seed=42,
    ranking_type='weighted_degree',
    top_k_core=1,
    save_per_period=True,
):
    """Extract core user IDs for each period's three largest communities.
    
    Required existing files:
    1. {period}_{params_tag}_top3_community_metrics.csv with rank and community_id.
       Ranks 1, 2 and 3 refer to community size.
    2. {period}_{params_tag}_top10_nodes.csv with user_id, louvain_community and
       ranking_type; weighted_degree and pagerank provide optional score columns.
       This table contains both rankings, distinguished by ranking_type.
    
    periods lists research windows. ranking_type selects weighted_degree or
    pagerank. top_k_core selects the first K entries from that community's
    corresponding Top10 list. save_per_period controls per-window CSV output.
    
    Return a combined DataFrame with period, community_rank, community_id,
    core_rank, user_id, ranking_type and score.
    """
    if ranking_type not in ('weighted_degree', 'pagerank'):
        raise ValueError("ranking_type 必须是 'weighted_degree' 或 'pagerank'")
    if not isinstance(top_k_core, int) or top_k_core <= 0:
        raise ValueError("top_k_core 必须为正整数")

    params_tag = f"res{resolution}_seed{random_seed}"
    score_col = 'weighted_degree' if ranking_type == 'weighted_degree' else 'pagerank'

    all_rows = []

    for period in periods:
        period_folder = os.path.join(base_root, period)
        metrics_path = os.path.join(period_folder, f"{period}_{params_tag}_top3_community_metrics.csv")
        top10_path = os.path.join(period_folder, f"{period}_{params_tag}_top10_nodes.csv")

        if not os.path.exists(metrics_path):
            print(f"[跳过] 指标文件不存在: {metrics_path}")
            continue
        if not os.path.exists(top10_path):
            print(f"[跳过] Top10文件不存在: {top10_path}")
            continue

        df_metrics = pd.read_csv(metrics_path, encoding='utf-8-sig')
        df_top10 = pd.read_csv(top10_path, encoding='utf-8-sig')

        # Validate required fields.
        if not {'rank', 'community_id'}.issubset(df_metrics.columns):
            raise ValueError(f"{metrics_path} 缺少必要字段 rank/community_id")
        if not {'user_id', 'louvain_community', 'ranking_type'}.issubset(df_top10.columns):
            raise ValueError(f"{top10_path} 缺少必要字段 user_id/louvain_community/ranking_type")

        # Keep the three largest communities, ranked 1 through 3.
        df_metrics = df_metrics.sort_values('rank').head(3).copy()

        # Keep the Top10 list for the selected ranking_type.
        df_top10_rt = df_top10[df_top10['ranking_type'] == ranking_type].copy()
        if score_col not in df_top10_rt.columns:
            df_top10_rt[score_col] = np.nan

        # Extract core nodes for each selected community.
        for _, mrow in df_metrics.iterrows():
            comm_rank = int(mrow['rank'])
            comm_id = mrow['community_id']

            comm_nodes = df_top10_rt[df_top10_rt['louvain_community'] == comm_id].copy()
            # Fallback to string comparison when community-ID types differ.
            if comm_nodes.empty:
                comm_nodes = df_top10_rt[df_top10_rt['louvain_community'].astype(str) == str(comm_id)].copy()

            if comm_nodes.empty:
                print(f"[警告] {period} Top{comm_rank} 社团(comm_id={comm_id}) 未在 Top10 文件中找到（ranking_type={ranking_type}）。")
                continue

            comm_nodes = comm_nodes.sort_values(score_col, ascending=False)
            core_nodes = comm_nodes.head(top_k_core)

            for core_rank, (_, nrow) in enumerate(core_nodes.iterrows(), 1):
                all_rows.append({
                    'period': period,
                    'community_rank': comm_rank,     # Ranks 1, 2 and 3 in descending community-size order.
                    'community_id': comm_id,
                    'core_rank': core_rank,          # Rank 1 through K by the selected centrality measure.
                    'user_id': str(nrow['user_id']),
                    'ranking_type': ranking_type,
                    'score': nrow.get(score_col, np.nan),
                })

        if save_per_period:
            out_df = pd.DataFrame([r for r in all_rows if r['period'] == period])
            out_path = os.path.join(
                period_folder,
                f"{period}_{params_tag}_top3_community_core_nodes_{ranking_type}_top{top_k_core}.csv"
            )
            out_df.to_csv(out_path, index=False, encoding='utf-8-sig')
            print(f"[保存] {period} Top3 社团核心节点: {out_path}")

    return pd.DataFrame(all_rows)


# Top3-community core-node extraction complete.
# Top1% degree-network variant introduced on 2026-04-08.
def extract_top3_community_core_nodes_by_quarter_top1_percent(
    periods,
    base_root=project_path('outputs', f'analyses/转发网络/季度合并_Top1Percent度数网络提取/季度社团Hub分析'),
    resolution=1.0,
    random_seed=42,
    ranking_type='weighted_degree',
    top_k_core=1,
    save_per_period=True,
):
    """Extract core user IDs for each period's three largest communities.
    
    Required existing files:
    1. {period}_{params_tag}_top3_community_metrics.csv with rank and community_id.
       Ranks 1, 2 and 3 refer to community size.
    2. {period}_{params_tag}_top10_nodes.csv with user_id, louvain_community and
       ranking_type; weighted_degree and pagerank provide optional score columns.
       This table contains both rankings, distinguished by ranking_type.
    
    periods lists research windows. ranking_type selects weighted_degree or
    pagerank. top_k_core selects the first K entries from that community's
    corresponding Top10 list. save_per_period controls per-window CSV output.
    
    Return a combined DataFrame with period, community_rank, community_id,
    core_rank, user_id, ranking_type and score.
    """
    if ranking_type not in ('weighted_degree', 'pagerank'):
        raise ValueError("ranking_type 必须是 'weighted_degree' 或 'pagerank'")
    if not isinstance(top_k_core, int) or top_k_core <= 0:
        raise ValueError("top_k_core 必须为正整数")

    params_tag = f"res{resolution}_seed{random_seed}"
    score_col = 'weighted_degree' if ranking_type == 'weighted_degree' else 'pagerank'

    all_rows = []

    for period in periods:
        period_folder = os.path.join(base_root, period)
        metrics_path = os.path.join(period_folder, f"{period}_{params_tag}_top3_community_metrics.csv")
        top10_path = os.path.join(period_folder, f"{period}_{params_tag}_top10_nodes.csv")

        if not os.path.exists(metrics_path):
            print(f"[跳过] 指标文件不存在: {metrics_path}")
            continue
        if not os.path.exists(top10_path):
            print(f"[跳过] Top10文件不存在: {top10_path}")
            continue

        df_metrics = pd.read_csv(metrics_path, encoding='utf-8-sig')
        df_top10 = pd.read_csv(top10_path, encoding='utf-8-sig')

        # Validate required fields.
        if not {'rank', 'community_id'}.issubset(df_metrics.columns):
            raise ValueError(f"{metrics_path} 缺少必要字段 rank/community_id")
        if not {'user_id', 'louvain_community', 'ranking_type'}.issubset(df_top10.columns):
            raise ValueError(f"{top10_path} 缺少必要字段 user_id/louvain_community/ranking_type")

        # Keep the three largest communities, ranked 1 through 3.
        df_metrics = df_metrics.sort_values('rank').head(3).copy()

        # Keep the Top10 list for the selected ranking_type.
        df_top10_rt = df_top10[df_top10['ranking_type'] == ranking_type].copy()
        if score_col not in df_top10_rt.columns:
            df_top10_rt[score_col] = np.nan

        # Extract core nodes for each selected community.
        for _, mrow in df_metrics.iterrows():
            comm_rank = int(mrow['rank'])
            comm_id = mrow['community_id']

            comm_nodes = df_top10_rt[df_top10_rt['louvain_community'] == comm_id].copy()
            # Fallback to string comparison when community-ID types differ.
            if comm_nodes.empty:
                comm_nodes = df_top10_rt[df_top10_rt['louvain_community'].astype(str) == str(comm_id)].copy()

            if comm_nodes.empty:
                print(f"[警告] {period} Top{comm_rank} 社团(comm_id={comm_id}) 未在 Top10 文件中找到（ranking_type={ranking_type}）。")
                continue

            comm_nodes = comm_nodes.sort_values(score_col, ascending=False)
            core_nodes = comm_nodes.head(top_k_core)

            for core_rank, (_, nrow) in enumerate(core_nodes.iterrows(), 1):
                all_rows.append({
                    'period': period,
                    'community_rank': comm_rank,     # Ranks 1, 2 and 3 in descending community-size order.
                    'community_id': comm_id,
                    'core_rank': core_rank,          # Rank 1 through K by the selected centrality measure.
                    'user_id': str(nrow['user_id']),
                    'ranking_type': ranking_type,
                    'score': nrow.get(score_col, np.nan),
                })

        if save_per_period:
            out_df = pd.DataFrame([r for r in all_rows if r['period'] == period])
            out_path = os.path.join(
                period_folder,
                f"{period}_{params_tag}_top3_community_core_nodes_{ranking_type}_top{top_k_core}.csv"
            )
            out_df.to_csv(out_path, index=False, encoding='utf-8-sig')
            print(f"[保存] {period} Top3 社团核心节点: {out_path}")

    return pd.DataFrame(all_rows)




























# ============================================================
# Attach mean media bias for each period's Top1 and Top2 communities.
# ============================================================
def append_top1_top2_mean_media_bias_to_top3_metrics_csv_top1_percent(
    periods,
    base_root=project_path('outputs', f'analyses/转发网络/季度合并_Top1Percent度数网络提取/季度社团Hub分析'),
    gexf_params_tag="res1.0_seed42",
    metrics_params_tag="res1.0_seed42",
    out_col_name="媒体平均bias",
):
    """Append Top1/Top2 mean media bias to each window's community-metrics table.
    
    Read {period}_{gexf_params_tag}_with_political_attributes.gexf. Find community
    attributes in order 'louvain community', 'louvain_community', 'community_id';
    read media scores from the unchanged attribute '媒体bias'. Read the existing
    {period}_{metrics_params_tag}_top3_community_metrics.csv and fill out_col_name
    for ranks 1 and 2 with mean nonmissing media bias. Rank 3 is left unchanged.
    Write the updated table to the same metrics CSV.
    """
    for period in periods:
        period_folder = os.path.join(base_root, period)

        gexf_path = os.path.join(
            period_folder,
            f"{period}_{gexf_params_tag}_with_political_attributes.gexf",
        )
        metrics_csv_path = os.path.join(
            period_folder,
            f"{period}_{metrics_params_tag}_top3_community_metrics.csv",
        )

        if not os.path.exists(metrics_csv_path):
            print(f"[跳过] 指标文件不存在: {metrics_csv_path}")
            continue
        if not os.path.exists(gexf_path):
            print(f"[跳过] GEXF 不存在: {gexf_path}")
            continue

        # 1. Read the Top3-community metrics table.
        metrics_df = pd.read_csv(metrics_csv_path, encoding="utf-8-sig")
        if metrics_df.empty or "rank" not in metrics_df.columns or "community_id" not in metrics_df.columns:
            print(f"[跳过] 指标表缺少必要列 rank/community_id 或为空: {metrics_csv_path}")
            continue

        # 2. Read GEXF node attributes, including community and media bias.
        nodes_df = _nodes_dataframe_from_top1pct_gexf(
            gexf_path,
            community_attr_candidates=("louvain community", "louvain_community", "community_id"),
        )
        if "媒体bias" not in nodes_df.columns:
            print(f"[跳过] GEXF 节点属性缺少列 '媒体bias': {gexf_path}")
            continue

        # Convert community_id to numeric for matching with metrics_df.
        nodes_df["community_id"] = pd.to_numeric(nodes_df["community_id"], errors="coerce")
        nodes_df["媒体bias"] = pd.to_numeric(nodes_df["媒体bias"], errors="coerce")

        # 2b. Compare the GEXF's two largest communities with metrics ranks 1 and 2.
        try:
            gexf_top2 = (
                nodes_df["community_id"]
                .dropna()
                .value_counts()
                .head(2)
                .index
                .tolist()
            )
        except Exception:
            gexf_top2 = []

        m_top1 = metrics_df.loc[metrics_df["rank"] == 1, "community_id"]
        m_top2 = metrics_df.loc[metrics_df["rank"] == 2, "community_id"]
        m_top1_id = pd.to_numeric(m_top1.iloc[0], errors="coerce") if not m_top1.empty else np.nan
        m_top2_id = pd.to_numeric(m_top2.iloc[0], errors="coerce") if not m_top2.empty else np.nan

        if len(gexf_top2) >= 2 and pd.notna(m_top1_id) and pd.notna(m_top2_id):
            g1, g2 = gexf_top2[0], gexf_top2[1]
            if float(g1) == float(m_top1_id) and float(g2) == float(m_top2_id):
                print(f"[检查通过] {period}：GEXF(louvain_community) 的 Top1/Top2 与 metrics.csv(rank=1/2) 编号一致：{g1}, {g2}")
            else:
                print(
                    f"[警告] {period}：Top1/Top2 社团编号可能不一致。\n"
                    f"  - metrics.csv: Top1={m_top1_id}, Top2={m_top2_id}\n"
                    f"  - gexf Top2 by node_count: Top1={g1}, Top2={g2}\n"
                    f"  将继续按 metrics.csv 的 community_id 计算 {out_col_name}（避免改变既有口径）。"
                )
        else:
            print(f"[提示] {period}：无法完成 Top1/Top2 编号一致性检查（GEXF 或 metrics 信息不足/无法解析）。")

        # 3. Calculate the added measure for ranks 1 and 2 only.
        if out_col_name not in metrics_df.columns:
            metrics_df[out_col_name] = np.nan

        for r in (1, 2):
            rows = metrics_df[metrics_df["rank"] == r]
            if rows.empty:
                continue
            comm_id = rows["community_id"].iloc[0]
            comm_id_num = pd.to_numeric(comm_id, errors="coerce")
            if pd.isna(comm_id_num):
                print(f"[跳过] {period} rank={r} 的 community_id 无法转为数值: {comm_id}")
                continue

            comm_nodes = nodes_df[nodes_df["community_id"] == comm_id_num]
            mean_bias = float(comm_nodes["媒体bias"].mean()) if not comm_nodes.empty else np.nan
            metrics_df.loc[metrics_df["rank"] == r, out_col_name] = mean_bias

        # 4. Write the table back with the added mean-bias column.
        metrics_df.to_csv(metrics_csv_path, index=False, encoding="utf-8-sig")
        v1 = metrics_df.loc[metrics_df["rank"] == 1, out_col_name].iloc[0] if (metrics_df["rank"] == 1).any() else np.nan
        v2 = metrics_df.loc[metrics_df["rank"] == 2, out_col_name].iloc[0] if (metrics_df["rank"] == 2).any() else np.nan
        print(f"[完成] {period} 已写回 {os.path.basename(metrics_csv_path)}；Top1均值={v1}，Top2均值={v2}")



import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import math
# Figure 4c radar chart with labels; the 2026-08-13 revision uses heterophily.
def plot_quarterly_community_radar_charts():
    # 1. Define the research windows and base paths.
    QUARTER_LIST = [
        "2019_12_2020_01_2020_02",
        "2020_03_2020_04_2020_05",
        "2020_06_2020_07_2020_08",
        "2020_09_2020_10",
        "2020_11_2020_12",
        "2021_01_2021_02"
    ]
    
    base_dir = project_path('outputs', 'analyses/转发网络/季度合并_Top1Percent度数网络提取/季度社团Hub分析')
    save_dir = project_path('outputs', 'analyses/转发网络/季度合并_Top1Percent度数网络提取/季度社团Hub分析/雷达图')
    os.makedirs(save_dir, exist_ok=True)

    # 2. First pass: read all periods and find global measure ranges.
    all_data_frames = []
    for quarter in QUARTER_LIST:
        file_path = os.path.join(base_dir, quarter, f"{quarter}_res1.0_seed42_top3_community_metrics.csv")
        
        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            try:
                df = pd.read_csv(file_path)
                if df.empty:
                    print(f"跳过空数据文件: {file_path}")
                    continue
                    
                df['quarter'] = quarter
                all_data_frames.append(df)
            except pd.errors.EmptyDataError:
                print(f"跳过无法解析的空文件: {file_path}")
        else:
            print(f"跳过不存在或大小为0的文件: {file_path}")

    if not all_data_frames:
        print("错误：没有读取到任何有效数据，程序退出。请检查文件夹路径。")
        return

    combined_df = pd.concat(all_data_frames)

    # 3. Determine common rounded axis limits.
    def get_nice_max(val):
        if val == 0 or pd.isna(val): return 0
        mag = 10 ** math.floor(math.log10(abs(val)))
        for multiplier in [1, 2, 4, 5, 8, 10]:
            if abs(val) <= multiplier * mag:
                return multiplier * mag if val > 0 else -multiplier * mag
        return 10 * mag if val > 0 else -10 * mag

    # Set common measure scales and omit the Community ID axis.
    # Use the displayed heterophily measure derived from assortativity.
    global_max_nodes = get_nice_max(combined_df['node_count'].max())
    global_max_edges = get_nice_max(combined_df['edge_count'].max())
    global_max_avg_degree = get_nice_max(combined_df['avg_degree'].max())
    global_max_heterophily = get_nice_max((-combined_df['assortativity']).max())
    global_max_clustering = get_nice_max(combined_df['clustering_coefficient'].max())
    # Add absolute mean media bias as a scaled radar dimension.
    if '媒体平均bias' not in combined_df.columns:
        raise KeyError(
            "未在 *_top3_community_metrics.csv 中找到列 '媒体平均bias'。"
            "请先运行 append_top1_top2_mean_media_bias_to_top3_metrics_csv_Top1Percent() 写回该列。"
        )
    global_max_abs_mean_media_bias = get_nice_max(combined_df['媒体平均bias'].abs().max())

    # Define measure names and limits; omit Community ID and diameter.
    english_metrics = [
        "Nodes", "Edges", "Avg Degree",
        "Heterophily", "Clustering Coeff",
        "Abs Mean Media Bias",
    ]

    custom_min_vals = [0, 0, 0, 0, 0, 0]
    custom_max_vals = [
        global_max_nodes, global_max_edges,
        global_max_avg_degree, global_max_heterophily, global_max_clustering,
        global_max_abs_mean_media_bias,
    ]
    
    print("全局统一刻度已设定：")
    for m, min_v, max_v in zip(english_metrics, custom_min_vals, custom_max_vals):
        print(f"{m}: [{min_v}, {max_v}]")

    # 4. Second pass: draw each window using the shared scales.
    angles = np.linspace(0, 2 * np.pi, len(english_metrics), endpoint=False).tolist()
    angles += angles[:1]

    # Preserve the original category colors.
    color_map = {1: (0.2, 0.4, 0.6), 2: (0.8, 0.4, 0.4)}
    label_map = {1: "Rank 1", 2: "Rank 2"}

    for df in all_data_frames:
        quarter = df['quarter'].iloc[0]
        fig, ax = plt.subplots(subplot_kw={'polar': True}, figsize=(10, 10))
        
        # Plot community ranks 1 and 2 only.
        for rank in [1, 2]:
            row = df[df['rank'] == rank]
            if row.empty: continue
            
            # Omit diameter from the plotted measures.
            raw_vals = [
                row['node_count'].iloc[0],
                row['edge_count'].iloc[0],
                row['avg_degree'].iloc[0],
                -row['assortativity'].iloc[0] if pd.notna(row['assortativity'].iloc[0]) else np.nan,
                row['clustering_coefficient'].iloc[0]
                ,abs(row['媒体平均bias'].iloc[0]) if pd.notna(row['媒体平均bias'].iloc[0]) else np.nan
            ]
            
            # Apply the same scaling to each measure.
            scaled_vals = []
            for i, v in enumerate(raw_vals):
                denom = custom_max_vals[i] - custom_min_vals[i]
                scaled_vals.append((v - custom_min_vals[i]) / denom if denom != 0 else 0.5)
            
            plot_vals = scaled_vals + [scaled_vals[0]]
            ax.plot(angles, plot_vals, label=label_map[rank], color=color_map[rank], linewidth=3)
            ax.fill(angles, plot_vals, color=color_map[rank], alpha=0.1)

        # 5. Configure axes and tick labels.
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(english_metrics, fontsize=11, fontweight='bold')
        ax.tick_params(axis='x', pad=30)
        
        ax.set_ylim(0, 1)
        ax.set_yticklabels([]) 
        
        # Draw custom radial labels at four equal intervals per axis.
        for i in range(len(english_metrics)):
            grid_vals = np.linspace(custom_min_vals[i], custom_max_vals[i], 5)
            for k, val in enumerate(grid_vals):
                if k == 0: continue 
                radius = k / 4.0
                
                # Format the numeric tick labels.
                if abs(val) >= 1000000: label_text = f"{val/1e6:g}M"
                elif abs(val) >= 1000: label_text = f"{val/1e3:g}K"
                elif 0 < abs(val) < 0.01: label_text = f"{val:.4f}"
                elif type(val) == np.float64 and abs(val) < 10: label_text = f"{val:.2f}"
                else: label_text = f"{val:g}"
                
                ax.text(angles[i], radius, label_text, ha='center', va='center', 
                        fontsize=8, color='gray', fontweight='semibold',
                        bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', pad=1))

        plt.title(f"Community Metrics Comparison\n{quarter}", pad=40, fontsize=16)
        plt.legend(loc='upper right', bbox_to_anchor=(1.25, 1.1))
        
        save_path = os.path.join(save_dir, f"{quarter}_radar_unified.png")
        plt.savefig(save_path, dpi=1200, bbox_inches='tight')
        plt.close()
        print(f"已生成统一比例尺雷达图(Top1+Top2，含媒体平均bias): {save_path}")


# Figure 4c radar-chart variant without labels, using heterophily.
def plot_quarterly_community_radar_charts_without_axes():
    # 1. Define the research windows and base paths.
    QUARTER_LIST = [
        "2019_12_2020_01_2020_02",
        "2020_03_2020_04_2020_05",
        "2020_06_2020_07_2020_08",
        "2020_09_2020_10",
        "2020_11_2020_12",
        "2021_01_2021_02"
    ]
    
    base_dir = project_path('outputs', 'analyses/转发网络/季度合并_Top1Percent度数网络提取/季度社团Hub分析')
    save_dir = project_path('outputs', 'analyses/转发网络/季度合并_Top1Percent度数网络提取/季度社团Hub分析/雷达图')
    os.makedirs(save_dir, exist_ok=True)

    # 2. First pass: read all periods and find global measure ranges.
    all_data_frames = []
    for quarter in QUARTER_LIST:
        file_path = os.path.join(base_dir, quarter, f"{quarter}_res1.0_seed42_top3_community_metrics.csv")
        
        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            try:
                df = pd.read_csv(file_path)
                if df.empty:
                    print(f"跳过空数据文件: {file_path}")
                    continue
                    
                df['quarter'] = quarter
                all_data_frames.append(df)
            except pd.errors.EmptyDataError:
                print(f"跳过无法解析的空文件: {file_path}")
        else:
            print(f"跳过不存在或大小为0的文件: {file_path}")

    if not all_data_frames:
        print("错误：没有读取到任何有效数据，程序退出。请检查文件夹路径。")
        return

    combined_df = pd.concat(all_data_frames)

    # 3. Determine common rounded axis limits.
    def get_nice_max(val):
        if val == 0 or pd.isna(val): return 0
        mag = 10 ** math.floor(math.log10(abs(val)))
        for multiplier in [1, 2, 4, 5, 8, 10]:
            if abs(val) <= multiplier * mag:
                return multiplier * mag if val > 0 else -multiplier * mag
        return 10 * mag if val > 0 else -10 * mag

    # Set common measure scales and omit the Community ID axis.
    # Use the displayed heterophily measure derived from assortativity.
    global_max_nodes = get_nice_max(combined_df['node_count'].max())
    global_max_edges = get_nice_max(combined_df['edge_count'].max())
    global_max_avg_degree = get_nice_max(combined_df['avg_degree'].max())
    global_max_heterophily = get_nice_max((-combined_df['assortativity']).max())
    global_max_clustering = get_nice_max(combined_df['clustering_coefficient'].max())
    # Add absolute mean media bias as a scaled radar dimension.
    if '媒体平均bias' not in combined_df.columns:
        raise KeyError(
            "未在 *_top3_community_metrics.csv 中找到列 '媒体平均bias'。"
            "请先运行 append_top1_top2_mean_media_bias_to_top3_metrics_csv_Top1Percent() 写回该列。"
        )
    global_max_abs_mean_media_bias = get_nice_max(combined_df['媒体平均bias'].abs().max())

    # Define measure names and limits; omit Community ID and diameter.
    english_metrics = [
        "Nodes", "Edges", "Avg Degree",
        "Heterophily", "Clustering Coeff",
        "Abs Mean Media Bias",
    ]

    custom_min_vals = [0, 0, 0, 0, 0, 0]
    custom_max_vals = [
        global_max_nodes, global_max_edges,
        global_max_avg_degree, global_max_heterophily, global_max_clustering,
        global_max_abs_mean_media_bias,
    ]
    
    print("全局统一刻度已设定：")
    for m, min_v, max_v in zip(english_metrics, custom_min_vals, custom_max_vals):
        print(f"{m}: [{min_v}, {max_v}]")

    # 4. Second pass: draw each window using the shared scales.
    angles = np.linspace(0, 2 * np.pi, len(english_metrics), endpoint=False).tolist()
    angles += angles[:1]

    # Preserve the original category colors.
    color_map = {1: (0.2, 0.4, 0.6), 2: (0.8, 0.4, 0.4)}
    label_map = {1: "Rank 1", 2: "Rank 2"}

    for df in all_data_frames:
        quarter = df['quarter'].iloc[0]
        fig, ax = plt.subplots(subplot_kw={'polar': True}, figsize=(10, 10))
        
        # Plot community ranks 1 and 2 only.
        for rank in [1, 2]:
            row = df[df['rank'] == rank]
            if row.empty: continue
            
            # Omit diameter from the plotted measures.
            raw_vals = [
                row['node_count'].iloc[0],
                row['edge_count'].iloc[0],
                row['avg_degree'].iloc[0],
                -row['assortativity'].iloc[0] if pd.notna(row['assortativity'].iloc[0]) else np.nan,
                row['clustering_coefficient'].iloc[0]
                ,abs(row['媒体平均bias'].iloc[0]) if pd.notna(row['媒体平均bias'].iloc[0]) else np.nan
            ]
            
            # Apply the same scaling to each measure.
            scaled_vals = []
            for i, v in enumerate(raw_vals):
                denom = custom_max_vals[i] - custom_min_vals[i]
                scaled_vals.append((v - custom_min_vals[i]) / denom if denom != 0 else 0.5)
            
            plot_vals = scaled_vals + [scaled_vals[0]]
            ax.plot(angles, plot_vals, label=label_map[rank], color=color_map[rank], linewidth=3)
            ax.fill(angles, plot_vals, color=color_map[rank], alpha=0.1)

        # 5. Configure axes without text labels.
        ax.set_xticks(angles[:-1])
        # Hide measure-name labels around the chart.
        ax.set_xticklabels([])
        ax.tick_params(axis='x', pad=30)
        
        ax.set_ylim(0, 1)
        ax.set_yticklabels([])
        
        # Omit custom radial tick-label text.
        # Omit titles and legends so no text remains.
        # plt.title(...)
        # plt.legend(...)
        
        save_path = os.path.join(save_dir, f"{quarter}_radar_unified_notext.png")
        plt.savefig(save_path, dpi=1200, bbox_inches='tight')
        plt.close()
        print(f"已生成雷达图不带坐标文字版本: {save_path}")


# ==========================================
# Run configuration.
# ==========================================
if __name__ == "__main__":
    QUARTER_LIST = [
        "2019_12_2020_01_2020_02",
        "2020_03_2020_04_2020_05",
        "2020_06_2020_07_2020_08",
        "2020_09_2020_10",
        "2020_11_2020_12",
        "2021_01_2021_02"
    ]
    # Prerequisite: the six quarterly Top1Percent node/edge CSV pairs already exist.
    # Stage 1: extract the network.
    # extract_top_degree_retweet_subgraphs()


    # Community detection, hub extraction and network metrics without diameter.
    # MY_RESOLUTION = 1.0
    # MY_SEED = 42
    # for PERIOD in QUARTER_LIST:
    # Legacy Top2Percent analysis call; retained as a commented historical example.
    # print('>>> Stage 1 complete: community analysis without diameter. <<<')


    # 2. Plot community distributions.
    # analyze_community_political_distribution_Top2Percent(QUARTER_LIST)
    # print('>>> Stage 2 complete: Top3-community ideology distributions. <<<')

    # 3. Plot distributions pooled across six windows.
    # plot_merged_bias_distribution_Top2Percent(QUARTER_LIST)
    # print('>>> Stage 3 complete: distributions pooled across six windows. <<<')

    # 4. Extract core-node IDs for each period's three largest communities.
    # extract_top3_community_core_nodes_by_quarter_top2_percent(QUARTER_LIST, ranking_type='pagerank', top_k_core=10)
    # print('>>> Stage 4 complete: Top3-community core-node extraction. <<<')




    # The following block analyzes Top1% degree networks; the earlier commented block used Top2% networks.
    # Run community detection, hub extraction and metrics without diameter.
    MY_RESOLUTION = 1.0
    MY_SEED = 42
    for PERIOD in QUARTER_LIST:
        analyze_quarterly_top_degree_communities(PERIOD, resolution=MY_RESOLUTION, random_seed=MY_SEED)
    # print('>>> Stage 1 complete: community analysis without diameter. <<<')
    attach_quarterly_bias_to_community_nodes()
    # print('>>> Community-node ideology scores attached. <<<')
    classify_community_node_ideology()
    # print('>>> Community-node ideology classification complete. <<<')
    export_gexf_with_ideology_attributes(
        QUARTER_LIST,
        gexf_params_tag=f"res{MY_RESOLUTION}_seed{MY_SEED}",
    )
    # print('>>> New GEXF exported with ideology scores and categories. <<<')






    # 2. Plot community distributions.
    analyze_community_political_distribution_top1_percent(QUARTER_LIST)
    # print('>>> Stage 2 complete: Top3-community ideology distributions. <<<')

    # 3. Plot Top1% network political-ideology distributions.
    # Historical pooled variant: six windows and Top1/Top2/Top3, with politician and media scores.
    # plot_merged_bias_distribution_top1_percent(QUARTER_LIST)  # Superseded plotting variant.
    # print('>>> Stage 3 complete: distributions pooled across six windows. <<<')

    # Current variant: one media-bias figure per window, overlaying Top1 and Top2 and hatching Top1.
    # Top1% degree-network plotting revision dated 2026-04-17.
    # Final Figure 4b selection, dated 2026-04-20.
    plot_quarterly_media_bias_distribution_top1_top2_top1_percent(QUARTER_LIST)
    # print('>>> Per-window Top1/Top2 media-ideology plots complete. <<<')

    plot_top_community_media_bias_without_axes(QUARTER_LIST)
    # print('>>> Top1/Top2 media-bias plots without coordinate text complete. <<<')

    # Function added on 2026-08-13.
    # Plot the Center group's media-bias distribution separately to show its within-category detail.
    plot_quarterly_center_media_bias_distribution_top1_top2_top1_percent(QUARTER_LIST)

    # 4. Extract core-node IDs for each period's three largest communities.
    extract_top3_community_core_nodes_by_quarter_top1_percent(QUARTER_LIST, ranking_type='pagerank', top_k_core=10)
    # print('>>> Stage 4 complete: Top3-community core-node extraction. <<<')


    append_top1_top2_mean_media_bias_to_top3_metrics_csv_top1_percent(QUARTER_LIST)
    # print('>>> Top1/Top2 mean media bias added. <<<')

    # Final Figure 4c selection, dated 2026-04-20.
    # Historical radar-chart reference file: `合并k核社团里每个社团的政治倾向分布图_20250512.py`; function plot_multi_quarter_radar_charts().
    # Revision dated 2026-08-13: display heterophily rather than an unexplained negative assortativity.
    plot_quarterly_community_radar_charts()
    # print('>>> Top1/Top2 community radar charts complete. <<<')

    # Revision dated 2026-08-13: use the heterophily display convention.
    plot_quarterly_community_radar_charts_without_axes()
    # print('>>> Top1/Top2 community radar charts without coordinate text complete. <<<')

