from pathlib import Path as _ReleasePath
import sys as _release_sys
_release_root = next(_p for _p in _ReleasePath(__file__).resolve().parents if (_p / 'runtime_config.py').is_file())
_release_sys.path.insert(0, str(_release_root))
from runtime_config import project_path

import pandas as pd
import os
import re
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from label_io import label_path, read_label_csv, read_exposure_csv

def load_politician_username_scores(file_path=None):
    # Historical politician-label input path.
    
    if file_path is None:
        file_path = label_path("politician_twitter-username-bias-type-final_without_media.csv")
    # Read the CSV file.
    df = read_label_csv(file_path)
    
    # Extract the screen name and bias label columns.
    username_column = df["username"].astype("string").str.strip()
    score_column = df["bias"].map(
        {'Left': -1, 'Right': 1, 'Center': 0}
    )

    # Keep username-score pairs from the same valid rows.
    valid_mask = (
        username_column.notna()
        & username_column.ne("")
        & score_column.notna()
    )

    mapping_dict = dict(zip(
        username_column[valid_mask],
        score_column[valid_mask].astype(int)
    ))

    return mapping_dict

# Extract an account username from its URL.
def extract_username(url):
    match = re.search(r"https://twitter.com/([^/]+)/", url)
    if match:
        return match.group(1)
    return None


# Historical note: this implementation was retained after verification.
def extract_politician_relations_from_twitter_urls(value_map):
    months = ['2019_12', '2020_01', '2020_02', '2020_03', '2020_04', '2020_05', '2020_06', '2020_07', '2020_08',
              '2020_09', '2020_10', '2020_11', '2020_12', '2021_01', '2021_02']
    for month in months:
        # Example usage
        input_folder = project_path('data', f'sources/single_url/twitter_url/output_{month}')
        
        output_folder = project_path('data', f'intermediate/Average_Bias_Rating/twitter_url_politician_influence_output')# Test input.
        # Save detailed relation records and summary counts.
        statistic_results_file = project_path('data', f'intermediate/Average_Bias_Rating/twitter_url_politician_influence_output/平均值方法的简化转发关系统计_{month}.csv')

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
                            retweet_expanded_urls_array = row.iloc[8]  # 9th column
                            retweet_origin_user_id = row.iloc[9]  # 10th column
                            quoted_expanded_urls_array = row.iloc[18]  # 19th column
                            quote_origin_user_id = row.iloc[19]  # 20th column
                            # Treat a matched politician username in the source URL as a scored retweet/quote exposure.
                            match_retweet_expanded_urls_username = extract_username(str(retweet_expanded_urls_array))
                            match_quoted_expanded_urls_username = extract_username(str(quoted_expanded_urls_array))
                            # Keep the current user ID, source-author ID, matched politician username and bias score in the Twitter relation table.
                            # Check if either 10th or 20th column is in the value_map
                            if (match_retweet_expanded_urls_username in value_map) or (match_quoted_expanded_urls_username in value_map):
                                # Determine which one is not empty for retweet_or_quote_origin_user_id
                                # Select the source-post author ID.
                                retweet_or_quote_origin_user_id = retweet_origin_user_id if pd.notna(retweet_origin_user_id) else quote_origin_user_id
                                # Select the matched username from the source URL.
                                match_retweet_or_quote_username = match_retweet_expanded_urls_username if pd.notna(match_retweet_expanded_urls_username) else match_quoted_expanded_urls_username
                                bias_value = value_map[match_retweet_or_quote_username]


                                # Increment retweet or quote count
                                if match_retweet_expanded_urls_username in value_map:# The source key exists in the score dictionary.
                                    retweet_count += 1
                                if match_quoted_expanded_urls_username in value_map:
                                    quote_count += 1
                                # Append to result list
                                result_data.append({
                                    'retweeted_user_id': retweeted_user_id,
                                    'retweet_or_quote_origin_user_id': retweet_or_quote_origin_user_id,
                                    'match_retweet_or_quote_username': match_retweet_or_quote_username,
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
            result_df.to_csv(output_file_path, index=False, columns=['retweeted_user_id', 'retweet_or_quote_origin_user_id', 'match_retweet_or_quote_username', 'bias_value'])




if __name__ == '__main__':
    bias_dict = load_politician_username_scores()# Load the source-author-ID-to-score mapping.
    extract_politician_relations_from_twitter_urls(bias_dict)
