from pathlib import Path as _ReleasePath
import sys as _release_sys
_release_root = next(_p for _p in _ReleasePath(__file__).resolve().parents if (_p / 'runtime_config.py').is_file())
_release_sys.path.insert(0, str(_release_root))
from runtime_config import project_path

# Figure 2a heatmap.
    
	
	
	
	
	
	


# Compute the three source-specific consumption matrices.
def count_external_media_consumption():
    # Define the file paths.
    months = [
        '2019_12','2020_01', '2020_02', '2020_03', '2020_04', '2020_05', '2020_06', '2020_07', '2020_08',
        '2020_09', '2020_10', '2020_11', '2020_12',
        '2021_01', '2021_02'
    ]
    data_part = 'external'
    for month in months:
        extreme_left_user_file = project_path('outputs', f'analyses/Average_Bias_Rating/media_average_rating/{data_part}_url-rating/user_bias_scores_by_month/extreme_left/{month}_extreme_left_user.csv')
        left_user_file = project_path('outputs', f'analyses/Average_Bias_Rating/media_average_rating/{data_part}_url-rating/user_bias_scores_by_month/left/{month}_left_user.csv')
        left_leaning_user_file = project_path('outputs', f'analyses/Average_Bias_Rating/media_average_rating/{data_part}_url-rating/user_bias_scores_by_month/left_leaning/{month}_left_leaning_user.csv')
        center_user_file = project_path('outputs', f'analyses/Average_Bias_Rating/media_average_rating/{data_part}_url-rating/user_bias_scores_by_month/center/{month}_center_user.csv')
        right_leaning_user_file = project_path('outputs', f'analyses/Average_Bias_Rating/media_average_rating/{data_part}_url-rating/user_bias_scores_by_month/right_leaning/{month}_right_leaning_user.csv')
        right_user_file = project_path('outputs', f'analyses/Average_Bias_Rating/media_average_rating/{data_part}_url-rating/user_bias_scores_by_month/right/{month}_right_user.csv')
        extreme_right_user_file = project_path('outputs', f'analyses/Average_Bias_Rating/media_average_rating/{data_part}_url-rating/user_bias_scores_by_month/extreme_right/{month}_extreme_right_user.csv')

        forwarding_relationship_file = project_path('data', f'intermediate/Simplyfied Forwarding relationship/Simplyfied Forwarding relationship_Media/{data_part}_url/output_with_bias_{month}.csv')

        # Read user IDs into category membership sets.
        extreme_left_user_set = set(pd.read_csv(extreme_left_user_file)['user_id'])
        left_user_set = set(pd.read_csv(left_user_file)['user_id'])
        left_leaning_user_set = set(pd.read_csv(left_leaning_user_file)['user_id'])
        center_user_set = set(pd.read_csv(center_user_file)['user_id'])
        right_leaning_user_set = set(pd.read_csv(right_leaning_user_file)['user_id'])
        right_user_set = set(pd.read_csv(right_user_file)['user_id'])
        extreme_right_user_set = set(pd.read_csv(extreme_right_user_file)['user_id'])

        # Read the forwarding-relation records.
        forwarding_df = pd.read_csv(forwarding_relationship_file)

        # Assign user_group from retweeted_user_id membership.
        forwarding_df['user_group'] = forwarding_df['retweeted_user_id'].apply(
            lambda x:
            'extreme bias left' if x in extreme_left_user_set else
            'left' if x in left_user_set else
            'left leaning' if x in left_leaning_user_set else
            'center' if x in center_user_set else
            'right leaning' if x in right_leaning_user_set else
            'right' if x in right_user_set else
            'extreme bias right' if x in extreme_right_user_set else
            'Unknown'
        )

        # Count consumed media categories within each user category.
        counts = forwarding_df[forwarding_df['user_group'] != 'Unknown'].groupby(['user_group', 'bias']).size().unstack(
            fill_value=0)
        print(counts)
        # Reorder the rows as specified.
        counts = counts.reindex(
            ['extreme bias left', 'left', 'left leaning', 'center', 'right leaning', 'right', 'extreme bias right'])
        counts = counts[['extreme bias left', 'left', 'left leaning', 'center', 'right leaning', 'right', 'extreme bias right']]  # Reorder the columns as specified.
        

        # Print the results.
        for group in ['extreme bias left', 'left', 'left leaning', 'center', 'right leaning', 'right', 'extreme bias right']:
            if group in counts.index:
                print(f"{month} {group} user consume counts:", counts.loc[group].to_dict())

        # Save the counts as a tab-separated text file.
        counts.to_csv(
            project_path('data', f'intermediate/Simplyfied Forwarding relationship/Simplyfied Forwarding relationship_Media/{data_part}_url/Media_external_information_consume/consumption_counts_{month}.txt'),
            sep='\t')

# Historical source-label capitalization differs between Twitter and Without URL data.
def count_twitter_media_consumption():
    # Define the file paths.
    months = [
        '2019_12',
        '2020_01', '2020_02', '2020_03', '2020_04', '2020_05', '2020_06', '2020_07', '2020_08',
        '2020_09', '2020_10', '2020_11', '2020_12', '2021_01', '2021_02'
    ]
    # data_part = 'without'
    data_part = 'twitter'
    for month in months:
        extreme_left_user_file = project_path('outputs', f'analyses/Average_Bias_Rating/media_average_rating/{data_part}_url-rating/user_bias_scores_by_month/extreme_left/{month}_extreme_left_user.csv')
        left_user_file = project_path('outputs', f'analyses/Average_Bias_Rating/media_average_rating/{data_part}_url-rating/user_bias_scores_by_month/left/{month}_left_user.csv')
        left_leaning_user_file = project_path('outputs', f'analyses/Average_Bias_Rating/media_average_rating/{data_part}_url-rating/user_bias_scores_by_month/left_leaning/{month}_left_leaning_user.csv')
        center_user_file = project_path('outputs', f'analyses/Average_Bias_Rating/media_average_rating/{data_part}_url-rating/user_bias_scores_by_month/center/{month}_center_user.csv')
        right_leaning_user_file = project_path('outputs', f'analyses/Average_Bias_Rating/media_average_rating/{data_part}_url-rating/user_bias_scores_by_month/right_leaning/{month}_right_leaning_user.csv')
        right_user_file = project_path('outputs', f'analyses/Average_Bias_Rating/media_average_rating/{data_part}_url-rating/user_bias_scores_by_month/right/{month}_right_user.csv')
        extreme_right_user_file = project_path('outputs', f'analyses/Average_Bias_Rating/media_average_rating/{data_part}_url-rating/user_bias_scores_by_month/extreme_right/{month}_extreme_right_user.csv')

        forwarding_relationship_file = project_path('data', f'intermediate/Simplyfied Forwarding relationship/Simplyfied Forwarding relationship_Media/{data_part}_url/output_with_bias_{month}.csv')

        # Read user IDs into category membership sets.
        extreme_left_user_set = set(pd.read_csv(extreme_left_user_file)['user_id'])
        left_user_set = set(pd.read_csv(left_user_file)['user_id'])
        left_leaning_user_set = set(pd.read_csv(left_leaning_user_file)['user_id'])
        center_user_set = set(pd.read_csv(center_user_file)['user_id'])
        right_leaning_user_set = set(pd.read_csv(right_leaning_user_file)['user_id'])
        right_user_set = set(pd.read_csv(right_user_file)['user_id'])
        extreme_right_user_set = set(pd.read_csv(extreme_right_user_file)['user_id'])

        # Read the forwarding-relation records.
        forwarding_df = pd.read_csv(forwarding_relationship_file)

        # Assign user_group from retweeted_user_id membership.
        forwarding_df['user_group'] = forwarding_df['retweeted_user_id'].apply(
            lambda x:
            'Extreme Bias Left' if x in extreme_left_user_set else
            'Left' if x in left_user_set else
            'Left Leaning' if x in left_leaning_user_set else
            'Center' if x in center_user_set else
            'Right Leaning' if x in right_leaning_user_set else
            'Right' if x in right_user_set else
            'Extreme Bias Right' if x in extreme_right_user_set else
            'Unknown'
        )

        # Count consumed media categories within each user category.
        counts = forwarding_df[forwarding_df['user_group'] != 'Unknown'].groupby(['user_group', 'bias']).size().unstack(
            fill_value=0)
        # Reorder the rows as specified.
        counts = counts.reindex(
            ['Extreme Bias Left', 'Left', 'Left Leaning', 'Center', 'Right Leaning', 'Right', 'Extreme Bias Right'])
        counts = counts[['Extreme Bias Left', 'Left', 'Left Leaning', 'Center', 'Right Leaning', 'Right', 'Extreme Bias Right']]  # Reorder the columns as specified.
        # Print the results.
        for group in ['Extreme Bias Left', 'Left', 'Left Leaning', 'Center', 'Right Leaning', 'Right', 'Extreme Bias Right']:
            if group in counts.index:
                print(f"{month} {group} user consume counts:", counts.loc[group].to_dict())

        # Save the counts as a tab-separated text file.
        counts.to_csv(
            project_path('data', f'intermediate/Simplyfied Forwarding relationship/Simplyfied Forwarding relationship_Media/{data_part}_url/information_consume/consumption_counts_{month}.txt'),
            sep='\t')

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import seaborn as sns
from matplotlib.colors import LogNorm
# Combine the source-specific consumption matrices.
def merge_media_consumption_matrices():
    # ==========================================
    # Step 1: read and align matrices, normalizing category capitalization.
    # ==========================================
    source_folders = [
        project_path('outputs', 'analyses/Information Consume/Media/Media_external_information_consume'),
        project_path('outputs', 'analyses/Information Consume/Media/Media_twitter_information_consume'),
        project_path('outputs', 'analyses/Information Consume/Media/Media_without_information_consume')
    ]
    months = ["2019_12"] + [f"2020_{str(m).zfill(2)}" for m in range(1, 13)] + ["2021_01", "2021_02"]
    
    # Define the canonical political-category name mapping.
    std_mapping = {
        'extreme bias left': 'Extreme Left',
        'extreme left': 'Extreme Left',
        'left': 'Left',
        'left leaning': 'Left Leaning',
        'center': 'Center',
        'right leaning': 'Right Leaning',
        'right': 'Right',
        'extreme bias right': 'Extreme Right',
        'extreme right': 'Extreme Right'
    }
    
    # Use the fixed order from Extreme Left to Extreme Right.
    ordered_categories = ['Extreme Left', 'Left', 'Left Leaning', 'Center', 
                          'Right Leaning', 'Right', 'Extreme Right']

    total_df = pd.DataFrame()

    for folder in source_folders:
        for month in months:
            filepath = os.path.join(folder, f"consumption_counts_{month}.txt")
            if os.path.exists(filepath):
                df_month = pd.read_csv(filepath, sep='\t', index_col=0)
                
                # Lowercase and strip row/column labels before mapping canonical names.
                df_month.index = df_month.index.str.lower().str.strip().map(std_mapping)
                df_month.columns = df_month.columns.str.lower().str.strip().map(std_mapping)
                
                # Add monthly counts with aligned labels and fill missing entries with zero.
                total_df = total_df.add(df_month, fill_value=0)

    # Sum duplicate row and column labels.
    final_matrix = total_df.groupby(total_df.index).sum().T.groupby(total_df.columns).sum().T
    
    # Reindex rows and columns in political-spectrum order.
    final_matrix = final_matrix.reindex(index=ordered_categories, columns=ordered_categories).fillna(0)
    
    print("✅ 数据合并与清洗完成！最终 7x7 矩阵如下：")
    print(final_matrix)

    # Save the combined matrix.
    output_csv = project_path('outputs', 'analyses/Information Consume/Media/Merged_Cleaned_Consumption_Matrix.csv')
    try:
        final_matrix.to_csv(output_csv)
    except Exception as e:
        print(f"提示：文件正在被占用或路径错误，保存失败 ({e})")

    # ==========================================
    # Step 2: plot the count heatmap.
    # ==========================================
    plt.figure(figsize=(10, 8))
    
    # Replace zeros with one for the logarithmic color scale.
    plot_data = final_matrix.replace(0, 1)
    
    # Draw the heatmap.
    # YlGnBu maps low values to light colors and high values to dark blue.
    # Use LogNorm to display differences across count magnitudes.
    # ax = sns.heatmap(plot_data, 
    #                  cmap="YlGnBu", 
    #                  norm=LogNorm(vmin=plot_data.values.min(), vmax=plot_data.values.max()),
    # annot=final_matrix,  # Annotate with the original counts.
    # fmt='.0f',  # Display integer counts without scientific notation.
    #                  cbar_kws={'label': 'Consumption Count (Log Scale)'},
    # linewidths=.5,  # Separate cells with thin white lines.
    #                  annot_kws={"size": 10})
    ax = sns.heatmap(plot_data, 
                     cmap="YlGnBu", 
                     norm=LogNorm(vmin=plot_data.values.min(), vmax=plot_data.values.max()),
                     annot=False, # Do not annotate individual raw counts.
                     cbar_kws={'label': ''}, # Omit colorbar label text.
                     linewidths=.5,      # Separate cells with thin white lines.
                     annot_kws={"size": 10})

    # Configure axis labels and title.
    # plt.xlabel('Media Political Leaning', fontsize=12, fontweight='bold', labelpad=10)
    # plt.ylabel('User Political Leaning', fontsize=12, fontweight='bold', labelpad=10)
    # plt.title('Heatmap of Information Consumption by Ideological Alignment', 
    #           fontsize=14, fontweight='bold', pad=20)

    # Refine tick-label styling.
    plt.xticks(rotation=30, ha='right', fontsize=10)
    plt.yticks(rotation=0, fontsize=10)
    
    plt.tight_layout()
    
    # Save the figure.
    output_img = project_path('outputs', 'analyses/Information Consume/Media/Figure_4a_Heatmap_LogScale.png')
    try:
        plt.savefig(output_img, dpi=300, bbox_inches='tight')
        print(f"✅ 图表已保存至: {output_img}")
    except:
        pass
        
    plt.show()

# Final total-source proportion heatmap, revision dated 2026-08-09.
# Y-axis category order, from top to bottom:
# Extreme Right → Right → Right Leaning → Center → Left Leaning → Left → Extreme Left
# X-axis category order remains left to right:
# Extreme Left → Left → Left Leaning → Center → Right Leaning → Right → Extreme Right
def plot_media_consumption_ratio_heatmap():
    # ==========================================
    # Step 1: read the matrix containing counts and ratio columns.
    # ==========================================
    input_csv = project_path('outputs', 'analyses/Information Consume/Media/Merged_Cleaned_Consumption_Matrix.csv')

    ordered_categories = [
        'Extreme Left', 'Left', 'Left Leaning', 'Center',
        'Right Leaning', 'Right', 'Extreme Right'
    ]

    ratio_cols = [
        'EL_ratio', 'L_ratio', 'LL_ratio', 'C_ratio',
        'RL_ratio', 'R_ratio', 'ER_ratio'
    ]

    ratio_col_rename = {
        'EL_ratio': 'Extreme Left',
        'L_ratio': 'Left',
        'LL_ratio': 'Left Leaning',
        'C_ratio': 'Center',
        'RL_ratio': 'Right Leaning',
        'R_ratio': 'Right',
        'ER_ratio': 'Extreme Right'
    }

    df = pd.read_csv(input_csv)

    # Strip column-name whitespace and any BOM marker.
    df.columns = df.columns.astype(str).str.strip().str.replace('\ufeff', '', regex=False)

    # Validate required columns.
    required_cols = ['user_group'] + ratio_cols
    missing_cols = [col for col in required_cols if col not in df.columns]

    if missing_cols:
        raise ValueError(f"缺少必要列：{missing_cols}。当前文件列名为：{df.columns.tolist()}")

    # Keep user_group and the proportion columns only.
    final_matrix = df[['user_group'] + ratio_cols].copy()

    # Set the row index.
    final_matrix['user_group'] = final_matrix['user_group'].astype(str).str.strip()
    final_matrix = final_matrix.set_index('user_group')

    # Rename ratio columns to the full category names.
    final_matrix = final_matrix.rename(columns=ratio_col_rename)

    # Apply the fixed political-category order to both axes.
    final_matrix = final_matrix.reindex(
        index=ordered_categories,
        columns=ordered_categories
    )

    # Convert values to numeric and replace missing values with zero.
    final_matrix = final_matrix.apply(pd.to_numeric, errors='coerce').fillna(0)

    # ==========================================
    # Step 2: detect proportion units and convert to percentages.
    # ==========================================
    # Multiply by 100 when values are expressed as fractions no greater than one.
    if final_matrix.max().max() <= 1:
        plot_matrix = final_matrix * 100
    else:
        plot_matrix = final_matrix.copy()

    print("✅ 已读取比例版 7×7 消费矩阵：")
    print(plot_matrix)

    print("\n✅ 矩阵形状：", plot_matrix.shape)
    print("✅ 行标签：", list(plot_matrix.index))
    print("✅ 列标签：", list(plot_matrix.columns))

    # Inspect row-wise proportion sums.
    row_sum_check = plot_matrix.sum(axis=1)

    print("\n✅ 每行比例和检查，理论上应接近 100：")
    print(row_sum_check)

    # Inspect the diagonal entries.
    diag_values = np.diag(plot_matrix.values)

    diag_check = pd.DataFrame({
        "User Political Leaning": ordered_categories,
        "Diagonal Share (%)": diag_values,
        "Row Sum (%)": row_sum_check.values
    })

    print("\n✅ 对角线比例检查：")
    print(diag_check)

    # ==========================================
    # Step 3: plot the proportion heatmap.
    # ==========================================
    plt.figure(figsize=(10, 8))

    cmap = plt.get_cmap("YlGnBu").copy()

    # Reverse the row order on the y-axis only.
    plot_matrix_for_plot = plot_matrix.iloc[::-1]

    ax = sns.heatmap(
        plot_matrix_for_plot,
        cmap=cmap,
        vmin=0,
        vmax=100,
        annot=False,
        linewidths=0.6,
        linecolor="white",
        square=True,
        cbar_kws={
            'label': '',
            'ticks': [0, 20, 40, 60, 80, 100]
        }
    )

    # Format the colorbar as percentages.
    cbar = ax.collections[0].colorbar
    cbar.ax.yaxis.set_major_formatter(ticker.PercentFormatter(xmax=100))

    # Leave axis labels and title empty for the paper figure.
    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.set_title("")

    # Refine tick-label styling.
    plt.xticks(rotation=30, ha='right', fontsize=11)
    plt.yticks(rotation=0, fontsize=11)

    plt.tight_layout()

    # ==========================================
    # Step 4: save the image.
    # ==========================================
    output_img = project_path('outputs', 'analyses/Information Consume/Media/Figure_4a_Heatmap_RatioScale_翻转y.png')

    plt.savefig(output_img, dpi=300, bbox_inches='tight')
    print(f"\n✅ 比例版热力图已保存至: {output_img}")

    plt.show()















# Figure 2b: ridgelines of continuous ideological permeability.
    
	
	
	
	
	
	

# Overall continuous ideological-permeability processing flow:
# Layer 1: source-specific open-mindedness results.
# ────────────────────────────────────────

# External source.
# Each analysis period and each of seven user categories.
# Per-user fields already available:
# user_id
# info_score
# appear_count

# Twitter source.
# Each analysis period and each of seven user categories.
# Per-user fields already available:
# user_id
# info_score
# appear_count

# Without URL source.
# Each analysis period and each of seven user categories.
# Per-user fields already available:
# user_id
# info_score
# appear_count

#               ↓

# Layer 2: merge source-specific results.
# merge_quarterly_source_ideop()

# For the same user in the same analysis period,
# combine External, Twitter and Without URL sources,
# and sum info_score and appear_count separately.

# Result:
# user_id
# total_info_score
# total_appear_count
# average_score

# That is:
# Each user and analysis period
# has one combined open-mindedness record.

#               ↓

# Layer 3: attach the total-source category.
# build_total_ideop_plot_data()

# Read:
# 1. Combined open-mindedness from the previous stage.
# 2. Total-media ideology for the same user and analysis period.

# Join on user_id.

# Result:
# quarter
# user_id
# bias
# total_info_score
# total_appear_count
# average_score

# The joined row contains:
# The user's political category in this period.
# +
# The user's combined open-mindedness in this period.

# Concatenate the six analysis periods
# to generate:
# plot_data_total_correct.csv

#               ↓

# Layer 4: reuse plot_data_total_correct.csv.
# Use the same data for two purposes.

#         ┌───────────────────────┐
#         ↓                       ↓

# Summary-statistics function and plotting function.
# Compute paper statistics and plot ridgelines, respectively.

# Compute:
# Zero-value proportions; group the plot data by seven political categories.
# Q1; exclude zeros from the KDE.
# Median; pool the six analysis periods.
# Q3; plot seven category distributions.
# IQR
# Proportion with score >= 2.

#         ↓                       ↓
# Numerical Results summaries and the corresponding ridgeline figure.


# Compute source-specific continuous ideological permeability.
# Define Center using the continuous interval rather than requiring p == 0.
# Skip users with count == 0 rather than assigning a zero permeability value.
# Center uses -0.5 <= p < 0.5, following the 2026-08-10 boundary revision.
def compute_quarterly_source_ideop():
    # datapart = "external"
    # datapart = "twitter"
    # datapart = "without"
    dataparts = [
        "external",
        "twitter",
        "without"
    ]

    # Map media labels to source scores P_i.
    media_bias_to_score = {
        'extreme bias left': -3,
        'left': -2,
        'left leaning': -1,
        'center': 0,
        'right leaning': 1,
        'right': 2,
        'extreme bias right': 3,
    }

    def calculate_g(p, q):
        """Compute the weighted ideology distance for one consumption record."""
        distance = abs(p - q)
        # Center users.
        if -0.5 <= p < 0.5:
            return 2 * distance if abs(q) > 1 else distance
        # Cross-camp consumption by non-Center users.
        return 2 * distance if np.sign(p) * np.sign(q) < 0 else distance

    user_biases = ["extreme_left", "left", "left_leaning", "center", "right_leaning", "right", "extreme_right"]
    for datapart in dataparts:
        print("\n" + "=" * 90)
        print(f"开始处理信息来源：{datapart}")
        print("=" * 90)
        for user_bias in user_biases:
            print(f"正在处理 {user_bias} 政治倾向的每个季度的信息消费开放程度")
            quarters = ['2019_12_2020_01_2020_02', '2020_03_2020_04_2020_05', '2020_06_2020_07_2020_08', '2020_09_2020_10', '2020_11_2020_12', '2021_01_2021_02']
            months = [['2019_12', '2020_01', '2020_02'], ['2020_03', '2020_04', '2020_05'], ['2020_06', '2020_07', '2020_08'], ['2020_09', '2020_10'], ['2020_11', '2020_12'], ['2021_01', '2021_02']]

            for quarter, quarter_months in zip(quarters, months):
                # 1. Read user IDs and continuous average_bias_points, denoted P_u.
                user_file_path = project_path('outputs', f'analyses/Average_Bias_Rating/media_average_rating/{datapart}_url-rating/user_bias_scores_by_quarter/{user_bias}/{quarter}_{user_bias}_user.csv')
                if not os.path.exists(user_file_path):
                    continue
                    
                user_df = pd.read_csv(user_file_path, usecols=['user_id', 'average_bias_points'], dtype={'user_id': str})
                
                # Build the user-score lookup and per-user counters.
                # key: user_id, value: P_u (float)
                # Convert continuous ideology scores to numeric.
                user_df['average_bias_points'] = pd.to_numeric(
                    user_df['average_bias_points'],
                    errors='coerce'
                )

                # Drop records missing a user ID or ideology score.
                user_df = user_df.dropna(
                    subset=['user_id', 'average_bias_points']
                )

                # Keep scores within the theoretical range.
                user_df = user_df[
                    user_df['average_bias_points'].between(-3, 3, inclusive='both')
                ]

                user_pu_dict = dict(
                    zip(user_df['user_id'], user_df['average_bias_points'])
                )

                user_score_sum_dict = {
                    uid: 0.0 for uid in user_pu_dict
                }

                user_count_dict = {
                    uid: 0 for uid in user_pu_dict
                }

                # 2. Read consumption CSVs for the months in this window.
                input_files = [
                    project_path('data', f'intermediate/Simplyfied Forwarding relationship/Simplyfied Forwarding relationship_Media/{datapart}_url/output_with_bias_{month}.csv')
                    for month in quarter_months
                ]
                for file_path in input_files:
                    if not os.path.exists(file_path):
                        continue
                    
                    # Only the current-user ID and source-media bias are needed.
                    df_iter = pd.read_csv(file_path, usecols=['retweeted_user_id', 'bias'], dtype=str)
                    
                    for row in df_iter.itertuples(index=False):
                        uid = row.retweeted_user_id
                        media_bias_label = str(row.bias).lower().strip()
                        if uid in user_pu_dict:
                            if media_bias_label not in media_bias_to_score:
                                continue
                            p_u = user_pu_dict[uid]
                            p_i = media_bias_to_score[media_bias_label]
                            score = calculate_g(p_u, p_i)
                            user_score_sum_dict[uid] += score
                            user_count_dict[uid] += 1

                # 3. Compute IdeoP_u = sum(g) / n.
                final_data = []
                for uid in user_pu_dict.keys():
                    count = user_count_dict[uid]
                    # Do not calculate permeability without valid consumption records.
                    if count == 0:
                        continue
                    total_g = user_score_sum_dict[uid]
                    ideo_p = total_g / count if count > 0 else 0
                    
                    final_data.append({
                        'user_id': uid,
                        'info_score': total_g,              # Store total_g, the sum of weighted distances.
                        'appear_count': count,
                        'average_info_openmindness': ideo_p # Store the mean weighted distance as continuous IdeoP_u.
                    })

                result_df = pd.DataFrame(final_data)
                cols = ['user_id', 'info_score', 'appear_count', 'average_info_openmindness']
                result_df = result_df[cols]
                # 4. Save the results.
                output_path = project_path('data', f'intermediate/Openmindness/media/连续的/{datapart}/{user_bias}/{quarter}_{user_bias}_user_info_consumption_openmindness_score.csv')
                parent_dir = os.path.dirname(output_path)
                if not os.path.exists(parent_dir):
                    os.makedirs(parent_dir)
                
                result_df.to_csv(output_path, index=False, encoding='utf-8-sig')
                print(f"结果已保存到 {output_path}")



# Combine results across the three sources.
import os
import numpy as np
import pandas as pd
# Sum score totals and occurrence counts by user and period across sources, then recompute the combined mean.
# For each user and window, sum source info_score and appear_count, then divide total score by total consumption count to obtain average_score.
# Calculate combined open-mindedness for user u in period q.
def merge_quarterly_source_ideop():
    # Configure paths.
    base_dir = project_path('data', 'intermediate/Openmindness/media/连续的')
    source_folders = [
        "external",
        "twitter",
        "without"
    ]

    biases = [
        "extreme_left",
        "left",
        "left_leaning",
        "center",
        "right_leaning",
        "right",
        "extreme_right"
    ]

    quarters = [
        "2019_12_2020_01_2020_02",
        "2020_03_2020_04_2020_05",
        "2020_06_2020_07_2020_08",
        "2020_09_2020_10",
        "2020_11_2020_12",
        "2021_01_2021_02"
    ]

    target_dir = os.path.join(base_dir, "total")
    os.makedirs(target_dir, exist_ok=True)

    audit_records = []

    # Merge each research window separately.
    for quarter in quarters:

        print("\n" + "=" * 90)
        print(f"开始合并时期：{quarter}")
        print("=" * 90)

        quarter_dfs = []

        # Read all seven source-specific categories from each of the three sources.
        for source in source_folders:

            source_dfs = []

            for bias in biases:

                filename = (
                    f"{quarter}_{bias}_"
                    f"user_info_consumption_openmindness_score.csv"
                )

                file_path = os.path.join(
                    base_dir,
                    source,
                    bias,
                    filename
                )

                if not os.path.exists(file_path):
                    audit_records.append({
                        "quarter": quarter,
                        "source": source,
                        "source_bias": bias,
                        "status": "missing_file",
                        "detail": file_path
                    })
                    continue

                try:
                    df = pd.read_csv(
                        file_path,
                        usecols=[
                            "user_id",
                            "info_score",
                            "appear_count"
                        ],
                        dtype={
                            "user_id": str
                        }
                    )

                except Exception as e:
                    audit_records.append({
                        "quarter": quarter,
                        "source": source,
                        "source_bias": bias,
                        "status": "read_error",
                        "detail": str(e)
                    })
                    continue

                raw_row_count = len(df)

                # Clean user-ID whitespace.
                df["user_id"] = df["user_id"].str.strip()

                # Convert numeric columns explicitly to avoid string concatenation.
                df["info_score"] = pd.to_numeric(
                    df["info_score"],
                    errors="coerce"
                )

                df["appear_count"] = pd.to_numeric(
                    df["appear_count"],
                    errors="coerce"
                )

                # Identify invalid records.
                invalid_mask = (
                    df["user_id"].isna()
                    | (df["user_id"] == "")
                    | df["info_score"].isna()
                    | df["appear_count"].isna()
                    | (df["appear_count"] <= 0)
                )

                invalid_count = int(invalid_mask.sum())

                if invalid_count > 0:
                    audit_records.append({
                        "quarter": quarter,
                        "source": source,
                        "source_bias": bias,
                        "status": "invalid_rows_removed",
                        "detail": invalid_count
                    })

                df = df.loc[~invalid_mask].copy()

                if df.empty:
                    audit_records.append({
                        "quarter": quarter,
                        "source": source,
                        "source_bias": bias,
                        "status": "empty_after_cleaning",
                        "detail": raw_row_count
                    })
                    continue

                # Check for duplicate user IDs within a source file.
                duplicate_count = int(
                    df.duplicated(
                        subset=["user_id"],
                        keep=False
                    ).sum()
                )

                if duplicate_count > 0:
                    audit_records.append({
                        "quarter": quarter,
                        "source": source,
                        "source_bias": bias,
                        "status": "duplicate_user_in_file",
                        "detail": duplicate_count
                    })

                    # Stop rather than hiding upstream duplicate records.
                    raise ValueError(
                        f"文件中存在重复用户ID：{file_path}，"
                        f"重复相关记录数为 {duplicate_count}"
                    )

                # Retain source and source-specific category metadata for quality control.
                df["source"] = source
                df["source_bias"] = bias

                source_dfs.append(df)

            # Check whether a user occurs in multiple categories within the same source.
            if source_dfs:

                source_df = pd.concat(
                    source_dfs,
                    ignore_index=True
                )

                duplicated_across_bias = source_df.duplicated(
                    subset=["user_id"],
                    keep=False
                )

                duplicated_across_bias_count = int(
                    duplicated_across_bias.sum()
                )

                if duplicated_across_bias_count > 0:

                    duplicate_users = (
                        source_df.loc[
                            duplicated_across_bias,
                            ["user_id", "source_bias"]
                        ]
                        .sort_values(["user_id", "source_bias"])
                    )

                    duplicate_output_path = os.path.join(
                        target_dir,
                        f"{quarter}_{source}_"
                        f"duplicate_users_across_bias.csv"
                    )

                    duplicate_users.to_csv(
                        duplicate_output_path,
                        index=False,
                        encoding="utf-8-sig"
                    )

                    raise ValueError(
                        f"{quarter} 的 {source} 来源中，"
                        f"存在同一用户被划入多个政治倾向类别的情况。"
                        f"重复明细已保存至：{duplicate_output_path}"
                    )

                quarter_dfs.append(source_df)

        # No valid source records were read for this period.
        if not quarter_dfs:
            print(f"警告：{quarter} 没有任何有效数据，跳过。")

            audit_records.append({
                "quarter": quarter,
                "source": "all",
                "source_bias": "all",
                "status": "no_valid_data",
                "detail": ""
            })

            continue

        # Concatenate sources and source-specific categories.
        combined_df = pd.concat(
            quarter_dfs,
            ignore_index=True
        )

        # A user may legitimately occur in more than one source.
        result_df = (
            combined_df
            .groupby(
                "user_id",
                as_index=False
            )
            .agg(
                total_info_score=(
                    "info_score",
                    "sum"
                ),
                total_appear_count=(
                    "appear_count",
                    "sum"
                )
            )
        )

        # Check for nonpositive total counts even though valid inputs should exclude them.
        zero_count_mask = (
            result_df["total_appear_count"] <= 0
        )

        zero_count_users = int(zero_count_mask.sum())

        if zero_count_users > 0:
            audit_records.append({
                "quarter": quarter,
                "source": "all",
                "source_bias": "all",
                "status": "non_positive_total_count_removed",
                "detail": zero_count_users
            })

            # Do not assign zero to users without valid records.
            result_df = result_df.loc[
                ~zero_count_mask
            ].copy()

        # Compute combined ideological permeability.
        result_df["average_score"] = (
            result_df["total_info_score"]
            / result_df["total_appear_count"]
        )

        # Set the output-column order.
        result_df = result_df[
            [
                "user_id",
                "total_info_score",
                "total_appear_count",
                "average_score"
            ]
        ]

        result_df = result_df.sort_values(
            by="user_id"
        ).reset_index(drop=True)

        # Save one combined table per analysis period.
        output_filename = (
            f"{quarter}_"
            f"user_info_consumption_openmindness_score.csv"
        )

        output_path = os.path.join(
            target_dir,
            output_filename
        )

        result_df.to_csv(
            output_path,
            index=False,
            encoding="utf-8-sig"
        )

        print(
            f"已保存：{output_path}，"
            f"用户数：{len(result_df)}"
        )

    # Save the quality-control report.
    audit_df = pd.DataFrame(
        audit_records,
        columns=[
            "quarter",
            "source",
            "source_bias",
            "status",
            "detail"
        ]
    )

    audit_output_path = os.path.join(
        target_dir,
        "openmindness_merge_audit_report.csv"
    )

    audit_df.to_csv(
        audit_output_path,
        index=False,
        encoding="utf-8-sig"
    )

    print("\n所有时期处理完成。")
    print(f"数据检查报告已保存至：{audit_output_path}")



# Attach the user's seven-category total-media ideology for this period.
# Read the output of merge_quarterly_source_ideop.
# user_id
# total_info_score
# total_appear_count
# average_score
# Then read:
# total_url-rating/
# user_bias_scores_by_quarter/
# The seven total-media category files; folder membership supplies bias.
# Each output record now contains:
# quarter
# user_id
# bias
# total_info_score
# total_appear_count
# average_score
# Concatenate user-period observations from all six windows into plot_data_total_correct.csv.
# The statistical unit is a user-period observation, not a unique user across all periods.
# A user observed in all six periods may contribute six rows.
def build_total_ideop_plot_data():
    """Join combined user-quarter IdeoP to total-media quarterly categories.
    
    Read the combined total-source open-mindedness results and the seven total
    user-category files. Return plotting records with quarter, user_id, bias,
    total_info_score, total_appear_count and average_score.
    """

    # Configure input and output paths.
    # Directory containing the combined total-source open-mindedness results.
    OPENMINDNESS_TOTAL_DIR = project_path('data', 'intermediate/Openmindness/media/连续的/total')
    OPENMINDNESS_TOTAL_RIDGELINE_DIR = project_path('data', 'intermediate/Openmindness/media/连续的/total/plots_ridgeline_correct_total')
    # Directory containing total-source quarterly user-category files.
    # Expected layout: ...\{bias}\{quarter}_{bias}_user.csv.
    TOTAL_USER_BIAS_DIR = (
        project_path('outputs', 'analyses/Average_Bias_Rating/media_average_rating/total_url-rating/user_bias_scores_by_quarter')
    )

    OUT_CSV = os.path.join(
        OPENMINDNESS_TOTAL_RIDGELINE_DIR,
        "plot_data_total_correct.csv"
    )

    quarters = [
        "2019_12_2020_01_2020_02",
        "2020_03_2020_04_2020_05",
        "2020_06_2020_07_2020_08",
        "2020_09_2020_10",
        "2020_11_2020_12",
        "2021_01_2021_02"
    ]

    biases = [
        "extreme_left",
        "left",
        "left_leaning",
        "center",
        "right_leaning",
        "right",
        "extreme_right"
    ]

    all_merged = []
    audit_records = []

    for quarter in quarters:
        print("\n" + "=" * 90)
        print(f"开始处理季度：{quarter}")
        print("=" * 90)

        # 1. Read total-source open-mindedness.
        openmindness_file = os.path.join(
            OPENMINDNESS_TOTAL_DIR,
            f"{quarter}_user_info_consumption_openmindness_score.csv"
        )

        if not os.path.exists(openmindness_file):
            audit_records.append({
                "quarter": quarter,
                "type": "missing_openmindness_file",
                "detail": openmindness_file
            })
            print(f"缺失 total openmindness 文件：{openmindness_file}")
            continue

        om_df = pd.read_csv(
            openmindness_file,
            dtype={"user_id": str}
        )
        om_df.columns = om_df.columns.str.strip()

        required_om_cols = [
            "user_id",
            "total_info_score",
            "total_appear_count",
            "average_score"
        ]
        if not all(col in om_df.columns for col in required_om_cols):
            audit_records.append({
                "quarter": quarter,
                "type": "openmindness_missing_columns",
                "detail": str(list(om_df.columns))
            })
            print(f"列缺失：{openmindness_file}")
            continue

        om_df = om_df[required_om_cols].copy()
        om_df["user_id"] = om_df["user_id"].astype(str).str.strip()
        om_df["total_info_score"] = pd.to_numeric(
            om_df["total_info_score"], errors="coerce"
        )
        om_df["total_appear_count"] = pd.to_numeric(
            om_df["total_appear_count"], errors="coerce"
        )
        om_df["average_score"] = pd.to_numeric(
            om_df["average_score"], errors="coerce"
        )

        om_df = om_df.dropna(subset=[
            "user_id", "total_info_score", "total_appear_count", "average_score"
        ])

        om_df = om_df[om_df["total_appear_count"] > 0].copy()

        # 2. Read total-source user political categories.
        bias_dfs = []

        for bias in biases:
            bias_file = os.path.join(
                TOTAL_USER_BIAS_DIR,
                bias,
                f"{quarter}_{bias}_user.csv"
            )

            if not os.path.exists(bias_file):
                audit_records.append({
                    "quarter": quarter,
                    "type": "missing_bias_file",
                    "detail": bias_file
                })
                continue

            try:
                bdf = pd.read_csv(
                    bias_file,
                    dtype={"user_id": str}
                )
                bdf.columns = bdf.columns.str.strip()

                if "user_id" not in bdf.columns:
                    audit_records.append({
                        "quarter": quarter,
                        "type": "bias_file_missing_user_id",
                        "detail": bias_file
                    })
                    continue

                bdf = bdf[["user_id"]].copy()
                bdf["user_id"] = bdf["user_id"].astype(str).str.strip()
                bdf["bias"] = bias

                bias_dfs.append(bdf)

            except Exception as e:
                audit_records.append({
                    "quarter": quarter,
                    "type": "bias_file_read_error",
                    "detail": f"{bias_file} | {e}"
                })

        if not bias_dfs:
            print(f"⚠️ {quarter} 没有读到任何 total 口径用户倾向文件，跳过。")
            continue

        bias_df = pd.concat(bias_dfs, ignore_index=True)

        # Check for user IDs appearing in multiple category folders in the same quarter.
        dup_mask = bias_df.duplicated(subset=["user_id"], keep=False)
        dup_count = int(dup_mask.sum())

        if dup_count > 0:
            dup_df = bias_df.loc[dup_mask].sort_values("user_id")
            dup_path = os.path.join(
                OPENMINDNESS_TOTAL_DIR,
                f"{quarter}_duplicate_users_in_total_bias.csv"
            )
            dup_df.to_csv(dup_path, index=False, encoding="utf-8-sig")
            raise ValueError(
                f"{quarter} 的 total 用户政治倾向文件中，同一 user_id 出现在多个 bias 文件夹中。"
                f"重复明细已保存到：{dup_path}"
            )

        # 3. Join the two user-period tables.
        merged_df = pd.merge(
            om_df,
            bias_df,
            on="user_id",
            how="inner"
        )

        merged_df["quarter"] = quarter

        merged_df = merged_df[
            [
                "quarter",
                "user_id",
                "bias",
                "total_info_score",
                "total_appear_count",
                "average_score"
            ]
        ]

        all_merged.append(merged_df)

        print(f"✅ {quarter} 合并完成，样本数：{len(merged_df)}")

    if not all_merged:
        print("❌ 没有成功构建任何绘图数据。")
        return

    final_df = pd.concat(all_merged, ignore_index=True)

    final_df.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")

    print("\n" + "=" * 90)
    print(f"✅ 正确 total 口径绘图数据已保存：{OUT_CSV}")
    print(f"✅ 总样本数：{len(final_df)}")
    print(f"✅ total_appear_count 总和：{final_df['total_appear_count'].sum():,.0f}")

    audit_df = pd.DataFrame(audit_records)
    audit_path = os.path.join(
        OPENMINDNESS_TOTAL_RIDGELINE_DIR,
        "plot_data_total_correct_audit.csv"
    )
    audit_df.to_csv(audit_path, index=False, encoding="utf-8-sig")
    print(f"✅ 质控文件已保存：{audit_path}")




import importlib
import joypy
def to_plt_color(rgb_str):
    """Convert an rgb(0, 51, 102) string to a Matplotlib RGB tuple with values in [0,1]."""
    rgb_values = (
        rgb_str
        .replace("rgb(", "")
        .replace(")", "")
        .split(",")
    )

    return tuple(
        int(value.strip()) / 255.0
        for value in rgb_values
    )

def patch_joypy_flatten():
    """Patch JoyPy flattening for environments where a generator cannot be indexed.
    
    Convert JoyPy's _flatten result to a list before subsequent indexed access,
    avoiding TypeError: 'generator' object is not subscriptable.
    """
    joyplot_module = importlib.import_module("joypy.joyplot")

    current_flatten = joyplot_module._flatten

    # Avoid applying the same patch twice within one Python process.
    if getattr(current_flatten, "_joypy_list_patch", False):
        return

    original_flatten = current_flatten

    def flatten_as_list(axes):
        return list(original_flatten(axes))

    flatten_as_list._joypy_list_patch = True
    joyplot_module._flatten = flatten_as_list


from pathlib import Path
import numpy as np
import pandas as pd
"""
    根据 plot_data_total_correct.csv 计算 Fig. 4b 所需统计量。

    统计口径与山脊图代码保持一致：
    1. 保留 total_appear_count >= 5 的用户—季度观测；
    2. 保留 average_score 位于理论范围 [0, 12] 内的有限值；
    3. 零值比例以该政治倾向组的全部保留观测为分母；
    4. 中位数、Q1、Q3 和 IQR 仅基于非零得分计算；
    5. 得分 >= 2 的比例以该组全部保留观测为分母；
    6. 同时额外输出非零样本中得分 >= 2 的比例，供质控使用。
"""
# Use the combined total-source data for the ridgeline analysis.
# Compute the paper's distribution summaries from plot_data_total_correct.csv.
# Require at least five valid consumption records per user-period observation.
# Output: ridgeline_statistics_with_quartiles_appear_ge_5.csv.
def summarize_total_ideop_quantiles():
    # -*- coding: utf-8 -*-
    # ==========================================================
    # 1. Configure file paths and parameters.
    # ==========================================================

    INPUT_CSV = Path(
        project_path('data', 'intermediate/Openmindness/media/连续的/total/plots_ridgeline_correct_total/plot_data_total_correct.csv')
    )

    OUTPUT_CSV = INPUT_CSV.parent / (
        "ridgeline_statistics_with_quartiles_appear_ge_5.csv"
    )

    # Keep this threshold consistent with the ridgeline plot.
    APPEAR_THRESHOLD = 5
    VALID_SCORE_RANGE = (0, 12)

    # Tolerance for floating-point zero comparisons.
    ZERO_ATOL = 1e-12

    # Read large files in chunks.
    CHUNK_SIZE = 500_000

    BIAS_ORDER = [
        "extreme_left",
        "left",
        "left_leaning",
        "center",
        "right_leaning",
        "right",
        "extreme_right"
    ]

    BIAS_LABELS = {
        "extreme_left": "Extreme Left",
        "left": "Left",
        "left_leaning": "Left-Leaning",
        "center": "Center",
        "right_leaning": "Right-Leaning",
        "right": "Right",
        "extreme_right": "Extreme Right"
    }


    # ==========================================================
    # 2. Validate the input file.
    # ==========================================================

    if not INPUT_CSV.exists():
        raise FileNotFoundError(
            f"找不到输入文件：{INPUT_CSV}"
        )


    # ==========================================================
    # 3. Read chunks and apply the ridgeline sample filters.
    # ==========================================================

    # Collect retained average_score values for each category.
    values_by_bias = {
        bias: []
        for bias in BIAS_ORDER
    }

    raw_rows = 0
    retained_rows = 0

    usecols = [
        "bias",
        "total_appear_count",
        "average_score"
    ]

    for chunk_index, chunk in enumerate(
        pd.read_csv(
            INPUT_CSV,
            usecols=usecols,
            chunksize=CHUNK_SIZE,
            dtype={"bias": str}
        ),
        start=1
    ):
        raw_rows += len(chunk)

        chunk.columns = chunk.columns.str.strip()

        # Normalize category-name whitespace.
        chunk["bias"] = (
            chunk["bias"]
            .astype(str)
            .str.strip()
        )

        # Convert numeric columns.
        chunk["total_appear_count"] = pd.to_numeric(
            chunk["total_appear_count"],
            errors="coerce"
        )

        chunk["average_score"] = pd.to_numeric(
            chunk["average_score"],
            errors="coerce"
        )

        # Drop missing values.
        chunk = chunk.dropna(
            subset=[
                "bias",
                "total_appear_count",
                "average_score"
            ]
        ).copy()

        # Keep the seven configured political categories.
        chunk = chunk[
            chunk["bias"].isin(BIAS_ORDER)
        ].copy()

        # Apply the valid-consumption count threshold.
        chunk = chunk[
            chunk["total_appear_count"]
            >= APPEAR_THRESHOLD
        ].copy()

        # Remove non-finite values.
        chunk = chunk[
            np.isfinite(chunk["total_appear_count"])
            & np.isfinite(chunk["average_score"])
        ].copy()

        # Keep scores in the theoretical range.
        chunk = chunk[
            chunk["average_score"].between(
                VALID_SCORE_RANGE[0],
                VALID_SCORE_RANGE[1],
                inclusive="both"
            )
        ].copy()

        retained_rows += len(chunk)

        # Collect scores by political category.
        for bias, group in chunk.groupby("bias"):
            values_by_bias[bias].append(
                group["average_score"].to_numpy(
                    dtype=float
                )
            )

        print(
            f"已处理第 {chunk_index} 个数据块，"
            f"累计读取 {raw_rows:,} 行，"
            f"累计保留 {retained_rows:,} 行。"
        )


    # ==========================================================
    # 4. Compute statistics for each political category.
    # ==========================================================

    statistics_records = []

    for bias in BIAS_ORDER:

        arrays = values_by_bias[bias]

        if arrays:
            all_values = np.concatenate(arrays)
        else:
            all_values = np.array([], dtype=float)

        total_count = len(all_values)

        if total_count == 0:
            statistics_records.append({
                "bias": bias,
                "bias_label": BIAS_LABELS[bias],
                "total_count": 0,
                "zero_count": 0,
                "zero_pct_all": np.nan,
                "nonzero_count": 0,
                "q1_nonzero": np.nan,
                "median_nonzero": np.nan,
                "q3_nonzero": np.nan,
                "iqr_width_nonzero": np.nan,
                "ge2_count_all": 0,
                "ge2_pct_all": np.nan,
                "ge2_count_nonzero": 0,
                "ge2_pct_nonzero": np.nan
            })
            continue

        # Use the same floating-point zero tolerance as the ridgeline plot.
        zero_mask = np.isclose(
            all_values,
            0.0,
            atol=ZERO_ATOL,
            rtol=0
        )

        zero_count = int(zero_mask.sum())
        zero_pct_all = zero_count / total_count * 100

        # Use strictly positive scores for the ridgeline and nonzero statistics.
        nonzero_values = all_values[
            (~zero_mask)
            & (all_values > 0)
        ]

        nonzero_count = len(nonzero_values)

        if nonzero_count > 0:
            q1_nonzero = float(
                np.quantile(nonzero_values, 0.25)
            )

            median_nonzero = float(
                np.quantile(nonzero_values, 0.50)
            )

            q3_nonzero = float(
                np.quantile(nonzero_values, 0.75)
            )

            iqr_width_nonzero = (
                q3_nonzero - q1_nonzero
            )

            ge2_count_nonzero = int(
                (nonzero_values >= 2).sum()
            )

            ge2_pct_nonzero = (
                ge2_count_nonzero
                / nonzero_count
                * 100
            )

        else:
            q1_nonzero = np.nan
            median_nonzero = np.nan
            q3_nonzero = np.nan
            iqr_width_nonzero = np.nan
            ge2_count_nonzero = 0
            ge2_pct_nonzero = np.nan

        # For the paper's statistics referring to all retained users:
        # Include zero-valued user-period observations in the denominator.
        ge2_count_all = int(
            (all_values >= 2).sum()
        )

        ge2_pct_all = (
            ge2_count_all
            / total_count
            * 100
        )

        statistics_records.append({
            "bias": bias,
            "bias_label": BIAS_LABELS[bias],
            "total_count": total_count,
            "zero_count": zero_count,
            "zero_pct_all": zero_pct_all,
            "nonzero_count": nonzero_count,
            "q1_nonzero": q1_nonzero,
            "median_nonzero": median_nonzero,
            "q3_nonzero": q3_nonzero,
            "iqr_width_nonzero": iqr_width_nonzero,
            "ge2_count_all": ge2_count_all,
            "ge2_pct_all": ge2_pct_all,
            "ge2_count_nonzero": ge2_count_nonzero,
            "ge2_pct_nonzero": ge2_pct_nonzero
        })


    # ==========================================================
    # 5. Build the result table and formatted manuscript fields.
    # ==========================================================

    stats_df = pd.DataFrame(statistics_records)

    # Apply the predefined category order.
    stats_df["bias"] = pd.Categorical(
        stats_df["bias"],
        categories=BIAS_ORDER,
        ordered=True
    )

    stats_df = (
        stats_df
        .sort_values("bias")
        .reset_index(drop=True)
    )

    # Format fields for manuscript reporting.
    stats_df["zero_pct_1dp"] = (
        stats_df["zero_pct_all"].round(1)
    )

    stats_df["q1_nonzero_3dp"] = (
        stats_df["q1_nonzero"].round(3)
    )

    stats_df["median_nonzero_3dp"] = (
        stats_df["median_nonzero"].round(3)
    )

    stats_df["q3_nonzero_3dp"] = (
        stats_df["q3_nonzero"].round(3)
    )

    stats_df["iqr_width_nonzero_3dp"] = (
        stats_df["iqr_width_nonzero"].round(3)
    )

    stats_df["ge2_pct_all_2dp"] = (
        stats_df["ge2_pct_all"].round(2)
    )

    stats_df["ge2_pct_nonzero_2dp"] = (
        stats_df["ge2_pct_nonzero"].round(2)
    )

    # Format the quartile interval, for example 1.479 to 2.055.
    stats_df["iqr_interval_nonzero"] = stats_df.apply(
        lambda row: (
            f"{row['q1_nonzero']:.3f} to "
            f"{row['q3_nonzero']:.3f}"
        )
        if pd.notna(row["q1_nonzero"])
        and pd.notna(row["q3_nonzero"])
        else ""
        ,
        axis=1
    )

    stats_df.to_csv(
        OUTPUT_CSV,
        index=False,
        encoding="utf-8-sig"
    )


    # ==========================================================
    # 6. Print the complete results.
    # ==========================================================

    display_columns = [
        "bias_label",
        "total_count",
        "zero_count",
        "zero_pct_1dp",
        "nonzero_count",
        "q1_nonzero_3dp",
        "median_nonzero_3dp",
        "q3_nonzero_3dp",
        "iqr_width_nonzero_3dp",
        "ge2_count_all",
        "ge2_pct_all_2dp",
        "ge2_pct_nonzero_2dp"
    ]

    print("\n" + "=" * 120)
    print("Fig. 4b 观念渗透性统计结果")
    print("=" * 120)

    print(
        stats_df[display_columns]
        .to_string(index=False)
    )

    print("\n字段说明：")
    print("zero_pct_1dp：零值占该组全部观测的比例，保留1位小数。")
    print("q1_nonzero_3dp：非零得分的第一四分位数。")
    print("median_nonzero_3dp：非零得分的中位数。")
    print("q3_nonzero_3dp：非零得分的第三四分位数。")
    print("iqr_width_nonzero_3dp：非零得分的IQR宽度，即Q3-Q1。")
    print("ge2_pct_all_2dp：得分>=2占该组全部观测的比例，正文使用这一列。")
    print("ge2_pct_nonzero_2dp：得分>=2占非零观测的比例，仅供质控。")

    print(f"\n结果文件已保存至：{OUTPUT_CSV}")


    # ==========================================================
    # 7. Print summaries for checking manuscript values.
    # ==========================================================

    print("\n" + "=" * 120)
    print("正文数据核对")
    print("=" * 120)

    for _, row in stats_df.iterrows():
        print(
            f"{row['bias_label']}: "
            f"zero={row['zero_pct_all']:.1f}%, "
            f"non-zero median={row['median_nonzero']:.3f}, "
            f"non-zero IQR interval="
            f"{row['q1_nonzero']:.3f}--{row['q3_nonzero']:.3f}, "
            f"score>=2 among all observations="
            f"{row['ge2_pct_all']:.2f}%"
        )

# Final Figure 2b ridgeline plotting code.
# Report zeros separately; exclude them from the KDE curves.
def plot_total_ideop_ridgelines():
    """Plot total-source ideological-permeability ridgelines from user-quarter data.
    
    Require quarter, user_id, bias, total_info_score, total_appear_count and
    average_score. The table must already contain combined source totals and
    the total-source category for each user-quarter observation.
    
    Apply total_appear_count >= APPEAR_THRESHOLD and the theoretical score range.
    Report zero counts and proportions by category, but exclude zeros from KDEs.
    Pool the six research windows to draw the seven category distributions.
    """

    # ==========================================================
    # 1. Configure paths and parameters.
    # ==========================================================

    # Minimum valid-consumption count.
    APPEAR_THRESHOLD = 5

    # With distance multiplier 2, theoretical permeability ranges from 0 to 12.
    VALID_RANGE = (0, 12)

    # Displayed x-axis range.
    PLOT_XLIM = (0, 6)

    IN_CSV = (
        project_path('data', 'intermediate/Openmindness/media/连续的/total/plots_ridgeline_correct_total/plot_data_total_correct.csv')
    )

    OUT_DIR = os.path.join(
        os.path.dirname(IN_CSV),
        "plots_ridgeline_correct_total"
    )

    # Political-category order from top to bottom.
    BIAS_ORDER = [
        "extreme_right",
        "right",
        "right_leaning",
        "center",
        "left_leaning",
        "left",
        "extreme_left"
    ]

    BIAS_ABBR = {
        "extreme_left": "EL",
        "left": "L",
        "left_leaning": "LL",
        "center": "C",
        "right_leaning": "RL",
        "right": "R",
        "extreme_right": "ER"
    }

    node_color_map = {
        "extreme_left": "rgb(0, 51, 102)",
        "left": "rgb(51, 102, 153)",
        "left_leaning": "rgb(181, 216, 243)",
        "center": "rgb(240, 230, 140)",
        "right_leaning": "rgb(255, 153, 153)",
        "right": "rgb(204, 102, 102)",
        "extreme_right": "rgb(139, 26, 26)"
    }

    plt_color_map = {
        bias: to_plt_color(rgb)
        for bias, rgb in node_color_map.items()
    }

    # ==========================================================
    # 2. Check the input and create the output directory.
    # ==========================================================

    if not os.path.exists(IN_CSV):
        print(f"❌ 找不到绘图输入文件：{IN_CSV}")
        return

    os.makedirs(OUT_DIR, exist_ok=True)

    # Apply the JoyPy compatibility patch.
    patch_joypy_flatten()

    # ==========================================================
    # 3. Read the total-source user-period table.
    # ==========================================================

    try:
        df = pd.read_csv(
            IN_CSV,
            dtype={
                "user_id": str,
                "quarter": str,
                "bias": str
            }
        )
    except Exception as e:
        print(f"❌ 读取文件失败：{e}")
        return

    df.columns = df.columns.str.strip()

    required_cols = [
        "quarter",
        "user_id",
        "bias",
        "total_info_score",
        "total_appear_count",
        "average_score"
    ]

    missing_cols = [
        col for col in required_cols
        if col not in df.columns
    ]

    if missing_cols:
        print(f"❌ 输入数据缺少必要列：{missing_cols}")
        print(f"当前文件列名：{list(df.columns)}")
        return

    # Keep required columns only.
    df = df[required_cols].copy()

    # Clean the string columns.
    df["user_id"] = df["user_id"].astype(str).str.strip()
    df["quarter"] = df["quarter"].astype(str).str.strip()
    df["bias"] = df["bias"].astype(str).str.strip()

    # Convert numeric columns.
    df["total_info_score"] = pd.to_numeric(
        df["total_info_score"],
        errors="coerce"
    )

    df["total_appear_count"] = pd.to_numeric(
        df["total_appear_count"],
        errors="coerce"
    )

    df["average_score"] = pd.to_numeric(
        df["average_score"],
        errors="coerce"
    )

    # ==========================================================
    # 4. Audit the data-filtering stages.
    # ==========================================================

    def report_data(step_name, current_df):
        appear_sum = current_df["total_appear_count"].sum()

        print(
            f"{step_name}: "
            f"样本数={len(current_df):,}，"
            f"total_appear_count总和={appear_sum:,.0f}"
        )

    report_data("原始数据", df)

    # Drop records missing required fields.
    df = df.dropna(
        subset=[
            "quarter",
            "user_id",
            "bias",
            "total_info_score",
            "total_appear_count",
            "average_score"
        ]
    ).copy()

    # Remove empty user IDs and category names.
    df = df[
        (df["user_id"] != "")
        & (df["bias"] != "")
        & (df["bias"].str.lower() != "nan")
    ].copy()

    report_data("删除缺失值后", df)

    # Keep the seven configured political categories.
    unknown_bias_mask = ~df["bias"].isin(BIAS_ORDER)
    unknown_bias_count = int(unknown_bias_mask.sum())

    if unknown_bias_count > 0:
        unknown_bias_stats = (
            df.loc[unknown_bias_mask, "bias"]
            .value_counts(dropna=False)
        )

        print(
            f"⚠️ 发现 {unknown_bias_count:,} 条未识别政治倾向记录，"
            "这些记录将不参与绘图："
        )
        print(unknown_bias_stats)

        unknown_bias_path = os.path.join(
            OUT_DIR,
            "unknown_bias_records.csv"
        )

        df.loc[unknown_bias_mask].to_csv(
            unknown_bias_path,
            index=False,
            encoding="utf-8-sig"
        )

    df = df[df["bias"].isin(BIAS_ORDER)].copy()

    report_data("保留七类政治倾向后", df)

    # Validate uniqueness of each user-quarter pair.
    duplicate_mask = df.duplicated(
        subset=["quarter", "user_id"],
        keep=False
    )

    duplicate_count = int(duplicate_mask.sum())

    if duplicate_count > 0:
        duplicate_path = os.path.join(
            OUT_DIR,
            "duplicate_quarter_user_records.csv"
        )

        duplicate_df = (
            df.loc[duplicate_mask]
            .sort_values(["quarter", "user_id", "bias"])
        )

        duplicate_df.to_csv(
            duplicate_path,
            index=False,
            encoding="utf-8-sig"
        )

        raise ValueError(
            f"发现 {duplicate_count:,} 条重复的用户—季度记录。"
            f"重复明细已保存至：{duplicate_path}"
        )

    # Require consumption count at least equal to the configured threshold.
    df = df[
        df["total_appear_count"] >= APPEAR_THRESHOLD
    ].copy()

    report_data(
        f"appear_count >= {APPEAR_THRESHOLD} 后",
        df
    )

    # Remove infinite values.
    finite_mask = (
        np.isfinite(df["total_info_score"])
        & np.isfinite(df["total_appear_count"])
        & np.isfinite(df["average_score"])
    )

    df = df.loc[finite_mask].copy()

    report_data("删除非有限值后", df)

    # Check that the average equals total score divided by total count.
    calculated_average = (
        df["total_info_score"]
        / df["total_appear_count"]
    )

    average_difference = np.abs(
        calculated_average - df["average_score"]
    )

    inconsistent_mask = average_difference > 1e-10
    inconsistent_count = int(inconsistent_mask.sum())

    if inconsistent_count > 0:
        inconsistent_path = os.path.join(
            OUT_DIR,
            "inconsistent_average_score_records.csv"
        )

        inconsistent_df = df.loc[inconsistent_mask].copy()
        inconsistent_df["calculated_average_score"] = (
            calculated_average.loc[inconsistent_mask]
        )
        inconsistent_df["average_difference"] = (
            average_difference.loc[inconsistent_mask]
        )

        inconsistent_df.to_csv(
            inconsistent_path,
            index=False,
            encoding="utf-8-sig"
        )

        print(
            f"⚠️ 发现 {inconsistent_count:,} 条 average_score "
            f"与 total_info_score / total_appear_count 不一致的记录。"
        )
        print(f"明细已保存至：{inconsistent_path}")

        # Recompute the mean from totals for plotting consistency.
        df["average_score"] = (
            df["total_info_score"]
            / df["total_appear_count"]
        )

    # Inspect score ranges.
    below_valid_count = int(
        (df["average_score"] < VALID_RANGE[0]).sum()
    )

    above_valid_count = int(
        (df["average_score"] > VALID_RANGE[1]).sum()
    )

    above_six_count = int(
        (df["average_score"] > 6).sum()
    )

    print(
        f"average_score < {VALID_RANGE[0]} 的样本数："
        f"{below_valid_count:,}"
    )

    print(
        f"average_score > 6 的样本数："
        f"{above_six_count:,}"
    )

    print(
        f"average_score > {VALID_RANGE[1]} 的样本数："
        f"{above_valid_count:,}"
    )

    # Keep scores in the theoretical range.
    df = df[
        df["average_score"].between(
            VALID_RANGE[0],
            VALID_RANGE[1],
            inclusive="both"
        )
    ].copy()

    report_data(
        f"保留理论范围 {VALID_RANGE} 后",
        df
    )

    if df.empty:
        print("❌ 数据筛选后为空，无法绘图。")
        return

    # ==========================================================
    # 5. Prepare the ridgeline data.
    # ==========================================================

    existing_biases = set(
        df["bias"].dropna().unique()
    )

    present_biases = [
        bias
        for bias in BIAS_ORDER
        if bias in existing_biases
    ]

    if not present_biases:
        print("❌ 数据中没有可绘制的政治倾向类别。")
        return

    data = []
    labels = []
    plot_colors = []
    stats_records = []

    print("\n========== 各政治倾向绘图样本统计 ==========")

    for bias in present_biases:

        all_vals = (
            df.loc[
                df["bias"] == bias,
                "average_score"
            ]
            .dropna()
            .to_numpy(dtype=float)
        )

        if len(all_vals) == 0:
            continue

        # Sample size after filtering and count thresholding, before removing zeros.
        total_count = len(all_vals)

        # Identify zero values using the floating-point tolerance.
        zero_mask = np.isclose(
            all_vals,
            0.0,
            atol=1e-12,
            rtol=0
        )

        zero_count = int(zero_mask.sum())

        zero_pct = (
            zero_count / total_count * 100
            if total_count > 0
            else 0
        )

        # Use strictly positive permeability values for the KDE.
        non_zero_vals = all_vals[
            (~zero_mask) & (all_vals > 0)
        ]

        non_zero_count = len(non_zero_vals)

        stats_records.append({
            "bias": bias,
            "bias_abbr": BIAS_ABBR.get(bias, bias),
            "total_count_before_zero_removal": total_count,
            "zero_count": zero_count,
            "zero_pct": zero_pct,
            "non_zero_count_for_plot": non_zero_count,
            "minimum_all": (
                float(np.min(all_vals))
                if total_count > 0
                else np.nan
            ),
            "maximum_all": (
                float(np.max(all_vals))
                if total_count > 0
                else np.nan
            ),
            "mean_all": (
                float(np.mean(all_vals))
                if total_count > 0
                else np.nan
            ),
            "median_all": (
                float(np.median(all_vals))
                if total_count > 0
                else np.nan
            ),
            "minimum_non_zero": (
                float(np.min(non_zero_vals))
                if non_zero_count > 0
                else np.nan
            ),
            "mean_non_zero": (
                float(np.mean(non_zero_vals))
                if non_zero_count > 0
                else np.nan
            ),
            "median_non_zero": (
                float(np.median(non_zero_vals))
                if non_zero_count > 0
                else np.nan
            )
        })

        print(
            f"{bias}: "
            f"总样本={total_count:,}，"
            f"0值={zero_count:,}（{zero_pct:.1f}%），"
            f"用于KDE={non_zero_count:,}"
        )

        # Require at least two values to estimate a KDE.
        if non_zero_count < 2:
            print(
                f"⚠️ {bias} 的非零样本少于2条，"
                "无法稳定绘制KDE，已跳过。"
            )
            continue

        data.append(non_zero_vals)

        label_str = (
            f"{BIAS_ABBR.get(bias, bias)} "
            f"(Total={total_count:,})\n"
            f"0 values: {zero_count:,} "
            f"({zero_pct:.1f}%)"
        )

        labels.append(label_str)

        plot_colors.append(
            plt_color_map.get(
                bias,
                (0.5, 0.5, 0.5)
            )
        )

    if not data:
        print("❌ 剔除0值后，没有足够的数据用于KDE绘图。")
        return

    # ==========================================================
    # 6. Save plotting statistics.
    # ==========================================================

    stats_df = pd.DataFrame(stats_records)

    stats_path = os.path.join(
        OUT_DIR,
        (
            "ridgeline_total_correct_stats_"
            f"appear_ge_{APPEAR_THRESHOLD}.csv"
        )
    )

    stats_df.to_csv(
        stats_path,
        index=False,
        encoding="utf-8-sig"
    )

    print(f"\n✅ 山脊图统计表已保存：{stats_path}")

    # ==========================================================
    # 7. Draw the ridgeline plot.
    # ==========================================================

    plt.rcParams["font.family"] = "Times New Roman"
    plt.rcParams["figure.subplot.left"] = 0.15

    try:
        fig, axes = joypy.joyplot(
            data,
            labels=labels,
            grid="y",
            linewidth=1,
            figsize=(12, 8),
            color=plot_colors,
            x_range=PLOT_XLIM
            # An explicit KDE bandwidth can be supplied here if required by a separate analysis.
            # bw_method=0.2
        )
    except Exception as e:
        print(f"❌ JoyPy绘图失败：{e}")
        raise

    # JoyPy generally returns axes as an array or list.
    axes[-1].set_xlabel(
        "Open-mindedness (>0)"
    )

    # Omit the figure title to preserve the selected styling.
    # fig.suptitle(...)

    # ==========================================================
    # 8. Save the image.
    # ==========================================================

    save_path = os.path.join(
        OUT_DIR,
        (
            "ridgeline_total_correct_"
            f"appear_ge_{APPEAR_THRESHOLD}_"
            "no_zeros.png"
        )
    )

    plt.savefig(
        save_path,
        dpi=300,
        bbox_inches="tight"
    )

    plt.close(fig)

    print(f"✅ 山脊图已保存：{save_path}")
    print(
        f"✅ 最终用于阈值筛选后的用户—季度样本数："
        f"{len(df):,}"
    )
    print(
        f"✅ 最终用于阈值筛选后的消费次数总和："
        f"{df['total_appear_count'].sum():,.0f}"
    )





if __name__ == "__main__":
    # Historical note: the Figure 2b workflow was rerun on 2026-08-10.
    compute_quarterly_source_ideop()    # Revision dated 2026-08-10: Center uses -0.5 <= p < 0.5.
    merge_quarterly_source_ideop()
    build_total_ideop_plot_data()
    summarize_total_ideop_quantiles()
    plot_total_ideop_ridgelines()