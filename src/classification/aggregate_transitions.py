from pathlib import Path as _ReleasePath
import sys as _release_sys
_release_root = next(_p for _p in _ReleasePath(__file__).resolve().parents if (_p / 'runtime_config.py').is_file())
_release_sys.path.insert(0, str(_release_root))
from runtime_config import project_path

import pandas as pd
import os
import plotly.graph_objects as go
import re

# Use user_id as the key and sum total_score and appearance_count across months in each window.
# Recompute average_bias_points as the accumulated total_score divided by accumulated appearance_count.
# Write one user-score table per window with the original four-column schema.
def process_quarterly_user_bias_scores():
    data_part_name = 'external_url'
    data_part_name = 'without_url'
    data_part_name = 'twitter_url'
    data_part_name = 'multiple_url'

    # Define the source directory and months in each research window.
    base_path = project_path('outputs', f'analyses/Average_Bias_Rating/media_average_rating/{data_part_name}-rating')
    quarter_months = [
        ['2019_12', '2020_01', '2020_02'],
        ['2020_03', '2020_04', '2020_05'],
        ['2020_06', '2020_07', '2020_08'],
        ['2020_09', '2020_10'],
        ['2020_11', '2020_12'],
        ['2021_01', '2021_02']
    ]

    # Iterate over research windows.
    for i, months in enumerate(quarter_months):
        # Initialize the table used to accumulate monthly records.
        quarterly_data = pd.DataFrame()

        # Read each month in the current window.
        for month in months:
            file_path = os.path.join(base_path, f'user_bias_scores_{month}.csv')

            if os.path.exists(file_path):
                # Read the CSV file.
                temp_df = pd.read_csv(file_path,
                                      usecols=['user_id', 'total_score', 'appearance_count', 'average_bias_points'],
                                      dtype={'user_id': 'str', 'total_score': 'float64', 'appearance_count': 'int64'})

                # Sum total_score and appearance_count for each user_id.
                if quarterly_data.empty:
                    quarterly_data = temp_df
                else:
                    quarterly_data = pd.concat([quarterly_data, temp_df])
                    quarterly_data = quarterly_data.groupby('user_id', as_index=False).agg({
                        'total_score': 'sum',
                        'appearance_count': 'sum'
                    })

        # Recompute average_bias_points from the accumulated totals.
        quarterly_data['average_bias_points'] = quarterly_data['total_score'] / quarterly_data['appearance_count']

        # Build the window identifier and save the output.
        quarter_str = "_".join(months)
        output_file = os.path.join(base_path, f'quarterly_user_bias_scores_{quarter_str}.csv')
        quarterly_data.to_csv(output_file, index=False)

        print(f"Saved quarterly data for {quarter_str} to {output_file}")


# Join each user's mean scores from two adjacent windows.
def find_common_users_between_quarters():
    data_part_name = 'external_url'
    data_part_name = 'without_url'
    data_part_name = 'twitter_url'
    data_part_name = 'multiple_url'
    base_path = project_path('outputs', f'analyses/Average_Bias_Rating/media_average_rating/{data_part_name}-rating')
    quarter_files = [
        'quarterly_user_bias_scores_2019_12_2020_01_2020_02.csv',
        'quarterly_user_bias_scores_2020_03_2020_04_2020_05.csv',
        'quarterly_user_bias_scores_2020_06_2020_07_2020_08.csv',
        'quarterly_user_bias_scores_2020_09_2020_10.csv',
        'quarterly_user_bias_scores_2020_11_2020_12.csv',
        'quarterly_user_bias_scores_2021_01_2021_02.csv'
    ]

    for i in range(len(quarter_files) - 1):
        path1 = os.path.join(base_path, quarter_files[i])
        path2 = os.path.join(base_path, quarter_files[i + 1])

        # Output file path.
        q1_str = quarter_files[i].replace('quarterly_user_bias_scores_', '').replace('.csv', '')
        q2_str = quarter_files[i + 1].replace('quarterly_user_bias_scores_', '').replace('.csv', '')
        output_path = project_path('outputs', f'analyses/Average_Bias_Rating/media_average_rating/{data_part_name}-rating/sankey_plot/every_quarter/common_user_bias/common_users_{q1_str}_to_{q2_str}.csv')

        # Read the two quarterly score files.
        df1 = pd.read_csv(path1, usecols=['user_id', 'average_bias_points'],
                          dtype={'user_id': 'str', 'average_bias_points': 'float64'})
        df2 = pd.read_csv(path2, usecols=['user_id', 'average_bias_points'],
                          dtype={'user_id': 'str', 'average_bias_points': 'float64'})

        # Rename the score columns to distinguish the two windows.
        df1.rename(columns={'average_bias_points': 'date1_average'}, inplace=True)
        df2.rename(columns={'average_bias_points': 'date2_average'}, inplace=True)

        # Join users present in both windows.
        common_users = pd.merge(df1[['user_id', 'date1_average']], df2[['user_id', 'date2_average']], on='user_id')

        # Write the common-user records.
        print(f"Common users between {q1_str} and {q2_str}:")
        print(common_users)
        common_users.to_csv(output_path, index=False)

        print(f"Saved common users between {q1_str} and {q2_str} to {output_path}")



# Build the media-score transition table used by the Sankey diagram.
# Count the 7 x 7 category transitions between adjacent windows and save them as CSV.
def build_media_transition_tables():
    data_part_name = 'external_url'
    data_part_name = 'without_url'
    data_part_name = 'twitter_url'
    data_part_name = 'multiple_url'
    # Configure file paths.
    date1s = ['2019_12_2020_01_2020_02', '2020_03_2020_04_2020_05', '2020_06_2020_07_2020_08', '2020_09_2020_10', '2020_11_2020_12']
    date2s = ['2020_03_2020_04_2020_05', '2020_06_2020_07_2020_08', '2020_09_2020_10', '2020_11_2020_12', '2021_01_2021_02']
    for date1, date2 in zip(date1s, date2s):
        # Load the data.
        file_path = project_path('outputs', f'analyses/Average_Bias_Rating/media_average_rating/{data_part_name}-rating/sankey_plot/every_quarter/common_user_bias/common_users_{date1}_to_{date2}.csv')

        output_transition_matrix_path = project_path('outputs', f'analyses/Average_Bias_Rating/media_average_rating/{data_part_name}-rating/sankey_plot/every_quarter/cross_table/transitions_sankey_{date1}_to_{date2}.csv')
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


def report_transition_value_totals():
    # Directory path.
    folder_path = project_path('outputs', 'analyses/Average_Bias_Rating/media_average_rating/multiple_url-rating/sankey_plot/cross_table')

    # Store each file's value-column total.
    file_value_sums = {}

    # Process CSV files in the directory.
    for file in os.listdir(folder_path):
        if file.endswith('.csv'):
            file_path = os.path.join(folder_path, file)
            df = pd.read_csv(file_path)

            # Check whether the value column is present.
            if 'value' in df.columns:
                # Sum the value column.
                value_sum = df['value'].sum()
                # Store the result in the dictionary.
                file_value_sums[file] = value_sum
    # Display file_value_sums as a summary table.
    print("月份/数据量\t相邻月份之间相同用户数量")
    for file, value_sum in file_value_sums.items():
        # Print each file name and its value total.
        print(f"{file}\t{value_sum}")



def plot_quarterly_media_sankey():
    data_part_name = 'external_url'
    data_part_name = 'without_url'
    data_part_name = 'twitter_url'
    data_part_name = 'multiple_url'
    # Common users in two adjacent research windows.
    # Configure file paths.
    date1s = ['2019_12_2020_01_2020_02', '2020_03_2020_04_2020_05', '2020_06_2020_07_2020_08', '2020_09_2020_10',
              '2020_11_2020_12']
    date2s = ['2020_03_2020_04_2020_05', '2020_06_2020_07_2020_08', '2020_09_2020_10', '2020_11_2020_12',
              '2021_01_2021_02']
    for date1, date2 in zip(date1s, date2s):
        csv_file = project_path('outputs', f'analyses/Average_Bias_Rating/media_average_rating/{data_part_name}-rating/sankey_plot/every_quarter/cross_table/transitions_sankey_{date1}_to_{date2}.csv')

        df = pd.read_csv(csv_file)
        df.columns = ['source', 'target', 'value']  # Read the CSV using its header row.
        # Predefine the node order.
        nodes = [
            f'{date1}_Extreme bias Left', f'{date1}_Left', f'{date1}_Left leaning', f'{date1}_Center',
            f'{date1}_Right leaning', f'{date1}_Right', f'{date1}_Extreme bias right',
            f'{date2}_Extreme bias Left', f'{date2}_Left', f'{date2}_Left leaning', f'{date2}_Center',
            f'{date2}_Right leaning', f'{date2}_Right', f'{date2}_Extreme bias right'
        ]

        # Map node names to the numeric indices required by Plotly Sankey links.
        node_dict = {node: i for i, node in enumerate(nodes)}

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
                return 'DEFAULT'  # Return a default color key when no category matches.

        # Map node categories to colors.
        node_color_map = {
            'Extreme bias Left': 'rgb(0, 51, 102)',  # Darkest blue.
            'Left': 'rgb(51, 102, 153)',  # Dark blue.
            'Left leaning': 'rgb(181, 216, 243)',  # Medium blue.
            'Center': 'rgb(240, 230, 140)',  # Light yellow.
            'Right leaning': 'rgb(255, 153, 153)',  # Light red.
            'Right': 'rgb(204, 102, 102)',  # Medium red.
            'Extreme bias right': 'rgb(139, 26, 26)',  # Dark red.
            'DEFAULT': 'rgb(128, 128, 128)'  # Default gray for unmatched categories.
        }

        # Use category colors with transparency for links.
        link_color_map = {
            'Extreme bias Left': 'rgba(0, 51, 102, 0.5)',  # Darkest blue, semitransparent.
            'Left': 'rgba(51, 102, 153, 0.5)',  # Dark blue, semitransparent.
            'Left leaning': 'rgba(181, 216, 243, 0.5)',  # Medium blue, semitransparent.
            'Center': 'rgba(240, 230, 140, 0.7)',  # Light yellow, slightly transparent.
            'Right leaning': 'rgba(255, 153, 153, 0.5)',  # Light red, semitransparent.
            'Right': 'rgba(204, 102, 102, 0.5)',  # Medium red, semitransparent.
            'Extreme bias right': 'rgba(139, 26, 26, 0.5)',  # Dark red, semitransparent.
            'DEFAULT': 'rgb(128, 128, 128)'  # Default gray for unmatched categories.
        }
        # Assign colors to the nodes using their category keys.
        node_colors = [node_color_map[extract_color_suffix(node)] for node in nodes]

        # Color each link using the category of its source node.
        link_colors = [link_color_map[extract_color_suffix(link['source'])] for _, link in df.iterrows()]

        # Prepare the Sankey link data.
        link = {
            'source': df['source'].map(node_dict).astype(int),
            'target': df['target'].map(node_dict).astype(int),
            'value': df['value'],
            'color': link_colors  # Set link colors.
        }
        # Create the Sankey figure.
        fig = go.Figure(data=[go.Sankey(
            node=dict(
                pad=15,
                thickness=20,
                line=dict(color='black', width=0.5),
                label=nodes,
                color=node_colors  # Set node colors.
            ),
            link=link
        )])

        # Update the layout and display the figure.
        fig.update_layout(title_text="Time Series Sankey Diagram", font_size=10)
        fig.show()

# Rename downloaded newplot.png images in sequence.
def rename_downloaded_sankey_images():
    data_part_name = 'external_url'
    data_part_name = 'without_url'
    data_part_name = 'twitter_url'
    data_part_name = 'multiple_url'
    # Directory path.
    folder_path = project_path('outputs', f'analyses/Average_Bias_Rating/media_average_rating/{data_part_name}-rating/sankey_plot/every_quarter/Sankey_plot')

    # List the target file names.
    new_filenames = [
        "common_user_bias_2019_12_2020_01_2020_02_to_2020_03_2020_04_2020_05.png",
        "common_user_bias_2020_03_2020_04_2020_05_to_2020_06_2020_07_2020_08.png",
        "common_user_bias_2020_06_2020_07_2020_08_to_2020_09_2020_10.png",
        "common_user_bias_2020_09_2020_10_to_2020_11_2020_12.png",
        "common_user_bias_2020_11_2020_12_to_2021_01_2021_02.png",
    ]

    # Extract the numeric suffix used to order downloaded files.
    def extract_file_number(filename):
        # Match names such as newplot.png and newplot (1).png.
        match = re.search(r'newplot(?: \((\d+)\))?.png', filename)
        if match:
            return int(match.group(1)) if match.group(1) else 0
        return -1

    # Collect matching image files from the directory.
    image_files = [f for f in os.listdir(folder_path) if f.startswith('newplot') and f.endswith('.png')]

    # Sort files by their numeric suffix.
    image_files_sorted = sorted(image_files, key=extract_file_number)

    # Check that the number of files matches the target-name list.
    if len(image_files_sorted) != len(new_filenames):
        print("文件数量不匹配，请检查文件夹中的图片数量。")
    else:
        # Rename files in sequence.
        for i, image_file in enumerate(image_files_sorted):
            old_path = os.path.join(folder_path, image_file)
            new_path = os.path.join(folder_path, new_filenames[i])
            os.rename(old_path, new_path)
            print(f'Renamed {image_file} to {new_filenames[i]}')

    print("重命名完成！")



if __name__ == '__main__':
    process_quarterly_user_bias_scores()
    find_common_users_between_quarters()
    build_media_transition_tables()
    report_transition_value_totals()
    plot_quarterly_media_sankey()
    rename_downloaded_sankey_images()