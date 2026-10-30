from pathlib import Path as _ReleasePath
import sys as _release_sys
_release_root = next(_p for _p in _ReleasePath(__file__).resolve().parents if (_p / 'runtime_config.py').is_file())
_release_sys.path.insert(0, str(_release_root))
from runtime_config import project_path

# Figure 1a.





# Figure 1a data calculation.
# Historical figure numbering: the 2026-02-03 Fig. 1b calculation became Fig. 1a on 2026-08-05.



# Count consumption records from each of the three sources by user political orientation.
import os
import pandas as pd
import plotly.graph_objects as go
from collections import defaultdict
def count_source_consumption_by_user_ideology():
    # 1. Root directory for total-source user categories.
    BIAS_ROOT_PATH = project_path('outputs', 'analyses/Average_Bias_Rating/media_average_rating/total_url-rating/user_bias_scores_by_quarter')

    # 2. Directories for the three consumption sources.
    SOURCE_PATHS = {
        "external_url": project_path('data', 'intermediate/Simplyfied Forwarding relationship/Simplyfied Forwarding relationship_Media/external_url'),
        "twitter_url": project_path('data', 'intermediate/Simplyfied Forwarding relationship/Simplyfied Forwarding relationship_Media/twitter_url'),
        "without_url": project_path('data', 'intermediate/Simplyfied Forwarding relationship/Simplyfied Forwarding relationship_Media/without_url')
    }
    # Output file name.
    OUTPUT_FILE = project_path('outputs', f'analyses/Average_Bias_Rating/media_average_rating/total_url-rating/user_bias_scores_by_quarter/每种政治倾向的用户在三种信息消费来源的消费的次数.csv')   
    # 3. Preserve the exact category-directory names.
    BIAS_CATEGORIES = [
        "extreme_left", 
        "left",
        "left_leaning",
        "center",
        "right_leaning",
        "right",
        "extreme_right" 
    ]

    # 4. Use the six research windows specified below.
    QUARTERS_LIST = [
        "2019_12_2020_01_2020_02",
        "2020_03_2020_04_2020_05",
        "2020_06_2020_07_2020_08",
        "2020_09_2020_10",
        "2020_11_2020_12",
        "2021_01_2021_02"
    ]

    # 5. Map each month to its research window.
    # Map month identifiers to quarterly directory names.
    MONTH_TO_QUARTER = {}
    # Construct the mapping explicitly.
    for q_str in QUARTERS_LIST:
        # Window identifiers have the form 2019_12_2020_01_2020_02.
        # Parse the year/month components of each window identifier.
        # Build the mapping from the months contained in each window identifier.
        parts = q_str.split('_')
        # Recombine year and month, for example 2019_12 and 2020_01.
        # The split components alternate year and month strings.
        for i in range(0, len(parts), 2):
            month_key = f"{parts[i]}_{parts[i+1]}" # For example, 2019_12.
            MONTH_TO_QUARTER[month_key] = q_str

    # List the months whose consumption records will be processed.
    TARGET_MONTHS = [
        '2019_12', '2020_01', '2020_02',
        '2020_03', '2020_04', '2020_05',
        '2020_06', '2020_07', '2020_08',
        '2020_09', '2020_10',
        '2020_11', '2020_12',
        '2021_01', '2021_02',
    ]
    def load_user_bias_data():
        """Load quarterly category membership as user_bias_map[quarter][category] sets."""
        print("正在加载用户政治倾向数据...")
        user_bias_map = defaultdict(lambda: defaultdict(set))

        for category in BIAS_CATEGORIES:
            cat_path = os.path.join(BIAS_ROOT_PATH, category)
            if not os.path.exists(cat_path):
                print(f"⚠️ 警告: 文件夹不存在 - {cat_path} (请检查BIAS_CATEGORIES列表是否与实际文件夹名一致)")
                continue

            # Iterate over the predefined research windows.
            for quarter_name in QUARTERS_LIST:
                # Look for a file named with the window identifier.
                # Also accept a file containing that window identifier.
                target_file = None
                for fname in os.listdir(cat_path):
                    if quarter_name in fname and fname.endswith('.csv'):
                        target_file = fname
                        break
                
                if not target_file:
                    # print(f'  No quarterly file in {category}: {quarter_name}')
                    continue

                file_path = os.path.join(cat_path, target_file)
                try:
                    # Detect the user-ID column.
                    df_head = pd.read_csv(file_path, nrows=1)
                    possible_id_cols = ['user_id', 'id', 'author_id', 'userid']
                    id_col = next((col for col in possible_id_cols if col in df_head.columns), None)

                    if id_col:
                        # Load the ID column and convert it to a string set.
                        df = pd.read_csv(file_path, usecols=[id_col])
                        ids = set(df[id_col].astype(str).str.strip()) # Convert to strings and strip whitespace.
                        user_bias_map[quarter_name][category].update(ids)
                    else:
                        print(f"❌ 错误: 文件 {target_file} 中没有找到 user_id 列")
                except Exception as e:
                    print(f"❌ 读取错误 {target_file}: {e}")
        
        return user_bias_map
    # ==========================================
    
    # 1. Load the user-category membership sets.
    user_bias_map = load_user_bias_data()
    print(f"用户画像加载完毕。")

    # 2. Initialize the result counters.
    # results[Source][Bias_Category] = Count
    results = defaultdict(lambda: defaultdict(int))

    # 3. Process the three sources.
    for source_name, source_path in SOURCE_PATHS.items():
        print(f"\n正在处理来源: {source_name} ...")
        
        # Iterate over target months.
        for month_str in TARGET_MONTHS:
            # Find the research-window key for this month.
            quarter_key = MONTH_TO_QUARTER.get(month_str)
            if not quarter_key:
                print(f"  跳过月份 {month_str}: 未找到对应的季度映射")
                continue
            
            if quarter_key not in user_bias_map:
                # print(f'  Skipping {month_str}: no user data for {quarter_key}')
                continue

            # Build output_with_bias_{month}.csv.
            # Also support file names whose month separator is a hyphen.
            # Try both supported month formats.
            file_name_underscore = f"output_with_bias_{month_str}.csv"
            file_name_hyphen = f"output_with_bias_{month_str.replace('_', '-')}.csv"
            
            file_path = os.path.join(source_path, file_name_underscore)
            if not os.path.exists(file_path):
                file_path = os.path.join(source_path, file_name_hyphen)
                if not os.path.exists(file_path):
                    # print(f'  Missing file: {file_name_underscore}; skipping')
                    continue
            
            # print(f'  Counting {os.path.basename(file_path)} for {quarter_key}')

            try:
                # Inspect the file's actual column names first.
                df_sample = pd.read_csv(file_path, nrows=5)
                actual_columns = df_sample.columns.tolist()
                print(f"  文件 {os.path.basename(file_path)} 的列名: {actual_columns}")
                
                # Choose the current-user column from the available names.
                if 'retweeted_user_id' in actual_columns:
                    target_col = 'retweeted_user_id'
                elif 'user_id' in actual_columns:
                    target_col = 'user_id'
                else:
                    # Try the alternative supported ID-column names.
                    possible_cols = ['retweeted_user_id', 'user_id', 'author_id', 'userid', 'user']
                    target_col = next((col for col in possible_cols if col in actual_columns), None)
                    
                    if not target_col:
                        print(f"  ❌ 无法找到用户ID列，可用列: {actual_columns}")
                        continue
                
                print(f"    使用列名: {target_col}")

                # Read large source files in chunks.
                chunk_iter = pd.read_csv(file_path, usecols=[target_col], chunksize=100000)
                
                for chunk in chunk_iter:
                    # Convert the current chunk's user IDs to strings.
                    active_users = chunk[target_col].astype(str).str.strip().tolist()
                    
                    # Count consumption records.
                    for user in active_users:
                        # Find the user's political category in the current window.
                        # Inspect the seven category membership sets.
                        found = False
                        for cat in BIAS_CATEGORIES:
                            if user in user_bias_map[quarter_key][cat]:
                                results[source_name][cat] += 1
                                found = True
                                # Assume categories are mutually exclusive and stop after the first match.
                                # Remove the break only if the category sets are intentionally nonexclusive.
                                break 
            
            except Exception as e:
                print(f"  ❌ 处理出错 {os.path.basename(file_path)}: {e}")

    # 4. Export the counts.
    print("\n正在导出统计结果...")
    final_data = []
    
    # Include every source/category combination, even when its count is zero.
    for source in SOURCE_PATHS.keys():
        for cat in BIAS_CATEGORIES:
            count = results[source][cat]
            final_data.append({
                'Source': source,
                'Political_Leaning': cat,
                'Consumption_Count': count
            })
    
    df_result = pd.DataFrame(final_data)
    
    # Create the pivot table.
    if not df_result.empty:
        df_pivot = df_result.pivot(index='Political_Leaning', columns='Source', values='Consumption_Count')
        # Apply the specified political-category order.
        df_pivot = df_pivot.reindex(BIAS_CATEGORIES)
        
        output_path = os.path.join(os.getcwd(), OUTPUT_FILE)
        df_pivot.to_csv(output_path)
        print(f"✅ 成功！结果已保存至: {output_path}")
        print(df_pivot)
    else:
        print("⚠️ 没有统计到任何数据，请检查文件名和路径是否匹配。")


# Plot Figure 1a.
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import matplotlib.patches as mpatches
def plot_source_consumption_panels():
# 0. Set the global line styling.
    plt.rcParams['hatch.linewidth'] = 2.5 

    # 1. Load the plotting data.
    try:
        input_file = project_path('outputs', f'analyses/Average_Bias_Rating/media_average_rating/total_url-rating/user_bias_scores_by_quarter/每种政治倾向的用户在三种信息消费来源的消费的次数.csv')
        df = pd.read_csv(input_file, index_col='Political_Leaning')
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"文件不存在，请检查路径：{input_file}")
    except FileNotFoundError:
        data = {
            'Political_Leaning': ['extreme_left', 'left', 'left_leaning', 'center', 'right_leaning', 'right', 'extreme_right'],
            # 'external_url': [1920,853121,31013242,2293681,4741027,10885382,496692],
            # 'twitter_url': [25384,216404,7200794,1146683,1638973,2667994,112678],
            # 'without_url': [51525,223450,3125639,425270,462785,969373,48341]
        }
        df = pd.DataFrame(data).set_index('Political_Leaning')

    # 2. Prepare the data.
    political_leanings = df.index.tolist()
    group_totals = df.sum(axis=1).values
    df_percent = df.div(group_totals, axis=0) * 100

    # Convert and map colors.
    def parse_rgb(rgb_str):
        return tuple(int(c.strip()) / 255.0 for c in rgb_str.replace('rgb(', '').replace(')', '').split(','))

    color_config = {
        'extreme_left': 'rgb(0, 51, 102)',
        'left': 'rgb(51, 102, 153)',
        'left_leaning': 'rgb(181, 216, 243)',
        'center': 'rgb(240, 230, 140)',
        'right_leaning': 'rgb(255, 153, 153)',
        'right': 'rgb(204, 102, 102)',
        'extreme_right': 'rgb(139, 26, 26)',
        'DEFAULT': 'rgb(128, 128, 128)'
    }
    
    top_colors = [parse_rgb(color_config.get(name.lower().replace(' ', '_'), color_config['DEFAULT'])) 
                  for name in political_leanings]

    # 3. Use equal-height panels and a small vertical gap.
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 12), sharex=True, 
                                   gridspec_kw={'height_ratios': [1, 1], 'hspace': 0.12})

    x_pos = np.arange(len(political_leanings))
    bar_width = 0.65

    # Upper panel: total counts without numeric annotations.
    ax1.bar(x_pos, group_totals, bar_width, color=top_colors, edgecolor='#333333', linewidth=1.0)
    ax1.set_ylabel('Total Consumption Count', fontsize=13, fontweight='bold')
    ax1.yaxis.set_major_formatter(ticker.StrMethodFormatter('{x:,.0f}'))
    ax1.grid(axis='y', linestyle='--', alpha=0.3)
    ax1.set_ylim(0, max(group_totals) * 1.1)

    # Lower panel: source proportions with category colors and distinct hatches.
    # External: solid fill.
    ax2.bar(x_pos, df_percent['external_url'], bar_width, 
            color=top_colors, edgecolor='#333333', alpha=1.0, linewidth=1.0)
    
    # Twitter: diagonal hatch.
    ax2.bar(x_pos, df_percent['twitter_url'], bar_width,
            bottom=df_percent['external_url'], 
            color=top_colors, edgecolor='#333333', hatch='/', alpha=0.7, linewidth=1.0)
    
    # Without URL: vertical hatch.
    ax2.bar(x_pos, df_percent['without_url'], bar_width,
            bottom=df_percent['external_url'] + df_percent['twitter_url'], 
            color=top_colors, edgecolor='#333333', hatch='|', alpha=0.4, linewidth=1.0)

    ax2.set_ylabel('Proportion (%)', fontsize=13, fontweight='bold')
    ax2.set_ylim(0, 100)
    ax2.yaxis.set_major_formatter(ticker.PercentFormatter())
    
    # Color the bottom-axis category labels.
    ax2.set_xlabel('Political Leaning', fontsize=13, fontweight='bold', labelpad=15)
    ax2.set_xticks(x_pos)
    xtick_labels = ax2.set_xticklabels(political_leanings, rotation=25, ha='right', fontsize=11, fontweight='bold')
    for label, color in zip(xtick_labels, top_colors):
        label.set_color(color)

    # No legend is drawn in this version.

    # 4. Refine the figure layout.
    plt.suptitle('Political Leaning vs. Information Consumption Analysis', fontsize=16, fontweight='bold', y=0.96)
    plt.tight_layout(rect=[0, 0, 1, 0.95])

    # Save the figure.
    output_path = project_path('outputs', 'analyses/Average_Bias_Rating/media_average_rating/total_url-rating/user_bias_scores_by_quarter/政治倾向消费分析_最终无标识版.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.show()







# Figure 1b.






# Calculate the Figure 1b data.
# Count users in each political-orientation category.
# Classify monthly mean scores with categorize_bias and count records by category.
def count_monthly_media_user_categories():
    # data_part = 'external_url'
    # data_part = 'multiple_url'
    # data_part = 'twitter_url'
    # data_part = 'without_url'
    data_part = 'total_url'


    months = ['2019_12', '2020_01', '2020_02', '2020_03', '2020_04', '2020_05', '2020_06', '2020_07', '2020_08',
              '2020_09', '2020_10', '2020_11', '2020_12', '2021_01', '2021_02']
    # Initialize the monthly category-count table.
    result_df = pd.DataFrame(columns=['month', 'Extreme bias Left', 'Left', 'Left leaning', 'Center',
                                      'Right leaning', 'Right', 'Extreme bias Right', 'Unknown'])

    # Classify average_bias_points with the intervals below.
    def categorize_bias(score):
        if -3 <= score < -2.5:
            return 'Extreme bias Left'
        elif -2.5 <= score < -1.5:
            return 'Left'
        elif -1.5 <= score < -0.5:
            return 'Left leaning'
        elif -0.5 <= score < 0.5:
            return 'Center'
        elif 0.5 <= score < 1.5:
            return 'Right leaning'
        elif 1.5 <= score < 2.5:
            return 'Right'
        elif 2.5 <= score <= 3:
            return 'Extreme bias Right'
        else:
            return 'Unknown'
    # Process each month.
    for month in months:
        # Read the combined score CSV.
        df = pd.read_csv(
            project_path('outputs', f'analyses/Average_Bias_Rating/media_average_rating/{data_part}-rating/user_bias_scores_by_month/user_bias_scores_{month}.csv'),
            encoding='utf-8')

        # Store the classification in a new column.
        df['category'] = df['average_bias_points'].apply(categorize_bias)

        # Count records in each category.
        category_counts = df['category'].value_counts()

        # Build this month's category-count record.
        counts = {
            'month': month,
            'Extreme bias Left': category_counts.get('Extreme bias Left', 0),
            'Left': category_counts.get('Left', 0),
            'Left leaning': category_counts.get('Left leaning', 0),
            'Center': category_counts.get('Center', 0),
            'Right leaning': category_counts.get('Right leaning', 0),
            'Right': category_counts.get('Right', 0),
            'Extreme bias Right': category_counts.get('Extreme bias Right', 0),
            'Unknown': category_counts.get('Unknown', 0)
        }

        # Append the monthly counts to the output table.
        result_df = result_df._append(counts, ignore_index=True)

    # Save the results as CSV.
    result_df.to_csv(
        project_path('outputs', f'analyses/Average_Bias_Rating/media_average_rating/{data_part}-rating/monthly_bias_category_counts_by_month.csv'),
        index=False, encoding='utf-8')

    print("分类统计完成并已保存到新的CSV文件中。")



# Historical function naming predates the exchange of Fig. 1a and Fig. 1b; this block plots Fig. 1b.
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
# Read the precomputed monthly category proportions and save a stacked bar chart.
# Input file:

# Input fields:
# month and seven proportion columns.
# Extreme bias Left Proportion, Left Proportion, Left leaning Proportion, Center Proportion, Right leaning Proportion, Right Proportion, Extreme bias Right Proportion
# Processing:
# Use month as the x-axis index.
# Order columns EL, L, LL, C, RL, R, ER.
# Plot stacked proportions and format the y-axis as percentages.
# Output image:

def plot_monthly_media_category_proportions():
    # 1. Use raw path strings to avoid accidental escape sequences.
    file_path = project_path('outputs', 'analyses/Average_Bias_Rating/media_average_rating/total_url-rating/monthly_bias_category_counts_by_month_比例.csv')

    # 2. Load the data.
    # If the input encoding differs, use its actual encoding, such as gbk or utf-8-sig.
    try:
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        print(f"错误：找不到文件，请检查路径是否正确：{file_path}")
        exit()

    # 3. Prepare the plotting table.
    # Use month as the x-axis index.
    df.set_index('month', inplace=True)

    # Keep the political spectrum ordered from left to right.
    column_order = [
        'Extreme bias Left Proportion',
        'Left Proportion',
        'Left leaning Proportion',
        'Center Proportion',
        'Right leaning Proportion',
        'Right Proportion',
        'Extreme bias Right Proportion'
    ]
    # Select only the requested columns present in the data.
    available_cols = [col for col in column_order if col in df.columns]
    df = df[available_cols]

    # 4. Define the political-spectrum color palette.
    # Keep category colors consistent across polarization figures.
    color_map = {
        'Extreme bias Left Proportion':  '#003366', # Dark blue.
        'Left Proportion':               '#336699', # Medium blue.
        'Left leaning Proportion':       '#B5D8F3', # Light blue.
        'Center Proportion':             '#F0E68C', # Neutral-category color.
        'Right leaning Proportion':      '#FF9999', # Light red.
        'Right Proportion':              '#CC6666', # Medium red.
        'Extreme bias Right Proportion': '#8B1A1A'  # Dark red.
    }
    # Build colors for the columns actually present.
    plot_colors = [color_map[col] for col in available_cols]

    # 5. Plot the figure.
    plt.figure(figsize=(15, 8)) # Use a 15-by-8-inch canvas.

    # Draw the stacked bars.
    # width controls bar width; alpha controls opacity.
    ax = df.plot(kind='bar', stacked=True, color=plot_colors, figsize=(15, 8), width=0.85, alpha=0.9)

    # 6. Refine the chart styling.
    plt.title('Monthly Distribution of Media Bias Categories', fontsize=16, pad=20)
    plt.xlabel('Month', fontsize=12)
    plt.ylabel('Proportion', fontsize=12)

    # Format the y-axis from 0% to 100%.
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))

    # Rotate x-axis labels to avoid overlap.
    plt.xticks(rotation=45, ha='right')

    # Place the legend outside the plot area.
    plt.legend(title='Bias Category', bbox_to_anchor=(1.01, 1), loc='upper left', borderaxespad=0.)

    # Add horizontal grid lines only.
    plt.grid(axis='y', linestyle='--', alpha=0.5)

    # Adjust layout so labels are not clipped.
    plt.tight_layout()

    # 7. Display or save the figure.
    plt.savefig(project_path('outputs', f'analyses/Average_Bias_Rating/media_average_rating/total_url-rating/total_url-user_bias_proportion_plot_不区分三种来源.png'), dpi=300) # Uncomment this line to save the image.
    plt.show()







# Figure 1c.
    
	
	
	
	
	# Compute the overall left-to-right transition proportion.
	
	
	# The Sankey is displayed as HTML and adjusted manually before figure export.
	
	



# Calculate the Figure 1c data.
# Total-media quarterly transition calculation checked on 2026-08-09.
# Build the media-score transition table used by the Sankey diagram.
# Count the 7 x 7 category transitions between adjacent windows and save them as CSV.
def build_total_media_transition_tables():
    # data_part_name = 'external_url'
    # data_part_name = 'without_url'
    # data_part_name = 'twitter_url'
    # data_part_name = 'multiple_url'
    data_part_name = 'total_url'
    # Configure file paths.
    date1s = ['2019_12_2020_01_2020_02', '2020_03_2020_04_2020_05', '2020_06_2020_07_2020_08', '2020_09_2020_10', '2020_11_2020_12']
    date2s = ['2020_03_2020_04_2020_05', '2020_06_2020_07_2020_08', '2020_09_2020_10', '2020_11_2020_12', '2021_01_2021_02']
    for date1, date2 in zip(date1s, date2s):
        # Load the data.
        file_path = project_path('outputs', f'analyses/Average_Bias_Rating/media_average_rating/{data_part_name}-rating/sankey_plot/every_quarter/common_user_bias/common_users_{date1}_to_{date2}.csv')

        output_transition_matrix_path = project_path('outputs', f'analyses/Average_Bias_Rating/media_average_rating/{data_part_name}-rating/sankey_plot/every_quarter/cross_table/transitions_sankey_{date1}_to_{date2}_20260809检查.csv')
        os.makedirs(os.path.dirname(output_transition_matrix_path), exist_ok=True)  # Create the parent output directory when missing.
        df = pd.read_csv(file_path)
        # Define the score intervals and category labels.
        bins = [-3, -2.5, -1.5, -0.5, 0.5, 1.5, 2.5, 3]
        labels = ['Extreme bias Left', 'Left', 'Left leaning', 'Center', 'Right leaning', 'Right', 'Extreme bias right']

        # Classify political orientation from the numeric score.
        def categorize_bias(score):
            if -3 <= score < -2.5:
                return 'Extreme bias Left'
            elif -2.5 <= score < -1.5:
                return 'Left'
            elif -1.5 <= score < -0.5:
                return 'Left leaning'
            elif -0.5 <= score < 0.5:
                return 'Center'
            elif 0.5 <= score < 1.5:
                return 'Right leaning'
            elif 1.5 <= score < 2.5:
                return 'Right'
            elif 2.5 <= score <= 3:
                return 'Extreme bias right'
            else:
                return 'Unknown'  # Use Unknown for values outside [-3, 3] or otherwise unmatched.

        # Apply the classifier to both score columns.
        df['date1_average'] = df['date1_average'].apply(categorize_bias)
        df['date2_average'] = df['date2_average'].apply(categorize_bias)
        # Count records in each category.
        count_2019_12 = df['date1_average'].value_counts()
        count_2020_01 = df['date2_average'].value_counts()
        # Initialize all category-pair counts.
        transitions = {f'{l1} to {l2}': 0 for l1 in labels for l2 in labels}
        # Count transitions between categories.
        for _, row in df.iterrows():
            transitions[f'{row["date1_average"]} to {row["date2_average"]}'] += 1
        # Report category counts and transition counts.
        print('date1的各区间数量:', count_2019_12)
        print('date2的各区间数量:', count_2020_01)
        # Compute and print the totals.
        total_count_2019_12 = count_2019_12.sum()
        total_count_2020_01 = count_2020_01.sum()

        print('count_2019_12的总和:', total_count_2019_12)
        print('count_2020_01的总和:', total_count_2020_01)
        for k, v in transitions.items():
            print(f'{k}: {v}')
        # Write the transition records to CSV.
        transitions_data = []
        for k, v in transitions.items():
            source, target = k.split(' to ')
            transitions_data.append({
                'source': f'{date1}_{source}',
                'target': f'{date2}_{target}',
                'value': v
            })
        transitions_df = pd.DataFrame(transitions_data)
        transitions_df.to_csv(
            output_transition_matrix_path,index=False)






# Plot Figure 1c.
# Final Sankey plotting procedure checked on 2026-08-05; positioning is adjusted manually.
def plot_multi_columns_sankey_by_media():
    # Source-part name.
    # data_part_name = 'external_url'
    # data_part_name = 'without_url'
    # data_part_name = 'twitter_url'
    # data_part_name = 'multiple_url'
    data_part_name = 'total_url'

    # Define the research-window lists.
    date1s = ['2019_12_2020_01_2020_02', '2020_03_2020_04_2020_05', '2020_06_2020_07_2020_08', '2020_09_2020_10',
              '2020_11_2020_12']
    date2s = ['2020_03_2020_04_2020_05', '2020_06_2020_07_2020_08', '2020_09_2020_10', '2020_11_2020_12',
              '2021_01_2021_02']

    # Initialize a long-format table for all window pairs.
    long_df = pd.DataFrame()

    for date1, date2 in zip(date1s, date2s):
        # Build the transition CSV path.
        csv_file = project_path('outputs', f'analyses/Average_Bias_Rating/media_average_rating/{data_part_name}-rating/sankey_plot/every_quarter/cross_table/transitions_sankey_{date1}_to_{date2}.csv')
        
        # Check that the input file exists.
        if not os.path.exists(csv_file):
            print(f"警告：文件不存在，跳过：{csv_file}")
            continue

        temp_df = pd.read_csv(csv_file)
        temp_df.columns = ['source', 'target', 'value']

        # Prefix node names with their research-window identifier.
        temp_df['source'] = date1 + '_' + temp_df['source']
        temp_df['target'] = date2 + '_' + temp_df['target']

        # Append the current window-pair records.
        long_df = pd.concat([long_df, temp_df], ignore_index=True)

    # Return when long_df contains no records.
    if long_df.empty:
        print("没有找到有效的数据文件，无法绘制桑基图。")
        return

    # Apply the selected Sankey filtering.

    # Exclude New users records from both source and target.
    long_df = long_df[~long_df['source'].str.contains("New users", case=False, na=False)]
    long_df = long_df[~long_df['target'].str.contains("New users", case=False, na=False)]

    # Rebuild the node list after filtering.
    nodes = list(set(long_df['source']).union(set(long_df['target'])))
    nodes.sort()
    node_dict = {node: i for i, node in enumerate(nodes)}

    # Define node and link colors.
    node_color_map = {
        'Extreme bias Left': 'rgb(0, 51, 102)',
        'Left': 'rgb(51, 102, 153)',
        'Left leaning': 'rgb(181, 216, 243)',
        'Center': 'rgb(240, 230, 140)',
        'Right leaning': 'rgb(255, 153, 153)',
        'Right': 'rgb(204, 102, 102)',
        'Extreme bias right': 'rgb(139, 26, 26)',
        'DEFAULT': 'rgb(128, 128, 128)'
    }

    # Extract a category key from the node name for coloring.
    def extract_color_suffix(node_name):
        if 'Extreme bias Left' in node_name:
            return 'Extreme bias Left'
        elif 'Left leaning' in node_name:
            return 'Left leaning'
        elif 'Left' in node_name:
            return 'Left'
        elif 'Center' in node_name:
            return 'Center'
        elif 'Right leaning' in node_name:
            return 'Right leaning'
        elif 'Right' in node_name:
            return 'Right'
        elif 'Extreme bias right' in node_name:
            return 'Extreme bias right'
        else:
            return 'DEFAULT'

    node_colors = [node_color_map[extract_color_suffix(node)] for node in nodes]
    link_colors = [f"rgba{node_color_map[extract_color_suffix(long_df.iloc[i]['source'])][3:-1]},0.5)" for i in
                   range(len(long_df))]

    # Prepare the Sankey link data.
    link = {
        'source': long_df['source'].map(node_dict).astype(int),
        'target': long_df['target'].map(node_dict).astype(int),
        'value': long_df['value'],
        'color': link_colors
    }

    # Create the Sankey figure.
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color='black', width=0.5),
            label=[],  # Use an empty label list to omit node labels.
            color=node_colors
        ),
        link=link
    )])

    # Configure layout and title.
    fig.update_layout(
        title_text=rf"{data_part_name} Multi-Quarter User Bias Flow Sankey Diagram (Media)",
        font_size=10,
        height=800,
        width=2000,
    )

    # Display the chart.
    fig.show()




