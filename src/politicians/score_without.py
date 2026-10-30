from pathlib import Path as _ReleasePath
import sys as _release_sys
_release_root = next(_p for _p in _ReleasePath(__file__).resolve().parents if (_p / 'runtime_config.py').is_file())
_release_sys.path.insert(0, str(_release_root))
from runtime_config import project_path

import pandas as pd
import os
from tqdm import tqdm
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from label_io import label_path, read_label_csv, read_exposure_csv

def load_politician_id_scores(file_path=None, id_mapping_path=None):
    """Join external author IDs to scores from the original username dictionary."""
    from label_io import politician_id_scores_from_usernames
    if file_path is None:
        file_path = label_path("politician_twitter-username-bias-type-final_without_media.csv")
    if id_mapping_path is None:
        id_mapping_path = project_path("data", "lookups/politician_account_ids.csv")
    return politician_id_scores_from_usernames(file_path, id_mapping_path)


# Score the Without URL source separately.
# Keep relation extraction and user-score aggregation as separate stages.


def extract_politician_relations_without_urls(value_map):
    months = ['2019_12', '2020_01', '2020_02', '2020_03', '2020_04', '2020_05', '2020_06', '2020_07', '2020_08',
              '2020_09', '2020_10', '2020_11', '2020_12', '2021_01', '2021_02']
    for month in months:
        # Example usage
        input_folder = project_path('data', f'sources/without_url/output_{month}')
        
        output_folder = project_path('data', f'intermediate/Average_Bias_Rating/without_url_politician_influence_output')# Test input.
        # Save detailed relation records and summary counts.
        statistic_results_file = project_path('data', f'intermediate/Average_Bias_Rating/without_url_politician_influence_output/平均值方法的简化转发关系统计_{month}.csv')

        # Create output folder if it doesn't exist
        os.makedirs(output_folder, exist_ok=True)

        # Prepare output file path
        output_file_path = os.path.join(output_folder, rf'politician_influence_output_{month}.csv')

        # Prepare the list to store the extracted rows
        result_data = []
        total_retweet_count = 0
        total_quote_count = 0
        summary_data = []
        # Loop through all files in the input folder
        for file_name in os.listdir(input_folder):
            if file_name.endswith('-output.csv'):
                file_path = os.path.join(input_folder, file_name)
                # Read the csv file
                df = read_exposure_csv(file_path)
                print('正在读取文件:', file_path)
                retweet_count = 0
                quote_count = 0
                if len(df.columns) >= 20:
                    # Loop through each row
                    for index, row in df.iterrows():
                        # Check if the row has enough columns
                        if len(row) >= 20:
                            retweeted_user_id = row.iloc[2]  # 3rd column
                            retweet_origin_user_id = row.iloc[9]  # 10th column
                            quote_origin_user_id = row.iloc[19]  # 20th column

                            # Check if either 10th or 20th column is in the value_map
                            if (retweet_origin_user_id in value_map) or (quote_origin_user_id in value_map):
                                # Determine which one is not empty for retweet_or_quote_origin_user_id
                                retweet_or_quote_origin_user_id = retweet_origin_user_id if pd.notna(retweet_origin_user_id) else quote_origin_user_id
                                bias_value = value_map[retweet_or_quote_origin_user_id]
                                # Increment retweet or quote count
                                if retweet_origin_user_id in value_map:# The source key exists in the score dictionary.
                                    retweet_count += 1
                                if quote_origin_user_id in value_map:
                                    quote_count += 1
                                # Append to result list
                                result_data.append({
                                    'retweeted_user_id': retweeted_user_id,
                                    'retweet_or_quote_origin_user_id': retweet_or_quote_origin_user_id,
                                    'bias_value': bias_value
                                })
                else:
                    print(f"Skipping file {file_name} because it doesn't have enough columns.")
                # Print the retweet and quote counts
                print(f"文件 {file_path}里能被政客标签影响的总的转贴次数为: {retweet_count}")
                print(f"文件 {file_path}的被政客标签影响的总的引用帖子次数为 {quote_count}")
                retweet_and_quote_count = retweet_count + quote_count
                print(f"文件 {file_path}的被政客标签影响的总的转贴和引用帖子次数为 {retweet_and_quote_count}")
                total_retweet_count += retweet_count
                total_quote_count += quote_count
                # Append this file's counts to summary_data.
                summary_data.append({
                    '文件名': file_path,
                    '转发次数': retweet_count,
                    '引用次数': quote_count,
                    '转贴和引用次数': retweet_and_quote_count
                })
        print(f"{input_folder}路径下的所有文件里能被政客标签影响的总的转贴次数为: {total_retweet_count}")
        print(f"{input_folder}路径下的所有文件里被政客标签影响的总的引用帖子次数为 {total_quote_count}")
        total_count = total_retweet_count + total_quote_count
        print(f"{input_folder}路径下的所有文件里被政客标签影响的总的转贴和引用帖子次数为 {total_count}")
        statistic_results_df = pd.DataFrame(summary_data)
        statistic_results_df.to_csv(statistic_results_file, index=False)
        print(f"已成功筛选并保存政客的转发信息和统计数据到 {statistic_results_file}")
        # Convert the result list to a DataFrame and save as CSV
        if result_data:
            result_df = pd.DataFrame(result_data)
            result_df.to_csv(output_file_path, index=False, columns=['retweeted_user_id', 'retweet_or_quote_origin_user_id', 'bias_value'])

# Accumulate bias_value and the number of relation rows per retweeted_user_id using two dictionaries.
# Write retweeted_user_id, total_bias_points, retweet_times and average_bias_points; the average is total_bias_points / retweet_times.
def aggregate_monthly_politician_scores():
    months = ['2019_12', '2020_01', '2020_02', '2020_03', '2020_04', '2020_05', '2020_06', '2020_07', '2020_08',
              '2020_09', '2020_10', '2020_11', '2020_12', '2021_01', '2021_02']
    for month in months:
        # File path.
        file_path = project_path('data', f'intermediate/Average_Bias_Rating/without_url_politician_influence_output/politician_influence_output_{month}.csv')
        # Read the CSV file.
        df = pd.read_csv(file_path,
                         dtype={'retweeted_user_id': str, 'retweet_or_quote_origin_user_id': str, 'bias_value': float})
        print('正在处理文件：', file_path)
        # Initialize the two accumulators.
        total_bias_points_dict = {}
        retweet_times_dict = {}
        # Iterate over DataFrame rows.
        for index, row in tqdm(df.iterrows(), total=df.shape[0], desc="Processing rows"):
            retweeted_user_id = row['retweeted_user_id']
            bias_value = row['bias_value']
            # Accumulate bias_value in total_bias_points_dict.
            if retweeted_user_id in total_bias_points_dict:
                total_bias_points_dict[retweeted_user_id] += bias_value
            else:
                total_bias_points_dict[retweeted_user_id] = bias_value
            # Count records per retweeted_user_id.
            if retweeted_user_id in retweet_times_dict:
                retweet_times_dict[retweeted_user_id] += 1
            else:
                retweet_times_dict[retweeted_user_id] = 1


        # Sum the user-level record counts.
        total_retweet_times = sum(retweet_times_dict.values())
        print(f"Retweet times total: {total_retweet_times}")
        # Build the final output DataFrame.
        result_data = []
        for retweeted_user_id in total_bias_points_dict:
            total_bias_points = total_bias_points_dict[retweeted_user_id]
            retweet_times = retweet_times_dict[retweeted_user_id]
            average_bias_points = total_bias_points / retweet_times  # Compute the average bias score.
            result_data.append({
                'retweeted_user_id': retweeted_user_id,
                'total_bias_points': total_bias_points,
                'retweet_times': retweet_times,
                'average_bias_points': average_bias_points
            })
        result_df = pd.DataFrame(result_data)
        # Write the result to a new CSV file.
        output_file = project_path('outputs', f'analyses/Average_Bias_Rating/politician_average_rating/without_url-rating/monthly_users_bias/{month}_output.csv')
        result_df.to_csv(output_file, index=False)
        print(f"处理结果已保存到 {output_file}")


if __name__ == '__main__':
    bias_dict = load_politician_id_scores()# Load the source-author-ID-to-score mapping.
    extract_politician_relations_without_urls(bias_dict)
    aggregate_monthly_politician_scores()
