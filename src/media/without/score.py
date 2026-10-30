from pathlib import Path as _ReleasePath
import sys as _release_sys
_release_root = next(_p for _p in _ReleasePath(__file__).resolve().parents if (_p / 'runtime_config.py').is_file())
_release_sys.path.insert(0, str(_release_root))
from runtime_config import project_path

import os
from urllib.parse import urlparse
import pandas as pd
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from label_io import label_path, read_label_csv
import logging



def load_media_author_id_scores(file_path=None):
    # Read Url and bias from the media domain-label table.
    if file_path is None:
        file_path = label_path("media-bias-final-username-display.csv")
    df = read_label_csv(file_path)

    # Define the original label-to-score mapping.
    bias_mapping = {
        'Extreme Bias Right': 3,
        'Right': 2,
        'Right Leaning': 1,
        'Center': 0,
        'Left Leaning': -1,
        'Left': -2,
        'Extreme Bias Left': -3,
    }
    # Debug: inspect the DataFrame contents.
    print(df)
    # Count label frequencies in the input CSV.
    bias_counts = df['bias'].value_counts()

    # Print the summary counts.
    print("Bias Category Counts in CSV:")
    for bias, count in bias_counts.items():
        print(f"{bias}: {count} entries")
    
    # Map recognized bias labels to numerical scores.
    df['score'] = df['bias'].map(bias_mapping)

    # Identify and report unrecognized or missing bias labels.
    unmapped_mask = df['score'].isna()
    if unmapped_mask.any():
        print("Unrecognized or missing bias labels excluded from scoring:")
        print(df.loc[unmapped_mask, 'bias'].value_counts(dropna=False))

    # Exclude rows with unrecognized or missing bias labels.
    df = df.loc[~unmapped_mask].copy()
    df['score'] = df['score'].astype(int)

    print(df)

    # Convert id_str and score columns into a dictionary.
    url_score = dict(zip(df['id_str'].str.strip(), df['score']))

    # Count scores represented in the lookup dictionary.
    score_counts = pd.Series(url_score.values()).value_counts()

    # Print the summary counts.
    print("Bias Category Counts in url_score Dictionary:")
    for score, count in score_counts.items():
        bias_category = [k for k, v in bias_mapping.items() if v == score]
        if bias_category:
            print(f"{bias_category[0]} (score {score}): {count} entries")
        else:
            print(f"Unmapped score {score}: {count} entries")
    return url_score






def user_bias_by_without_url():

    # Build the matching-key-to-score dictionary.
    url_score_file_path = label_path("media-bias-final-username-display.csv")
    url_score = load_media_author_id_scores(url_score_file_path)
    print(url_score)

    # '2019_12', '2020_01', '2020_02', '2020_03', '2020_04', '2020_05', '2020_06', '2020_07', '2020_08',
    months = ['2019_12', '2020_01', '2020_02', '2020_03', '2020_04', '2020_05', '2020_06', '2020_07', '2020_08',
              '2020_09', '2020_10', '2020_11', '2020_12', '2021_01', '2021_02', ]
    # months = ['2019_12']

    for month in months:
        print(
            f"{month}=========================================================================================================")
        monthly_retweet_count = 0
        monthly_quote_count = 0
        monthly_missing_source_count = 0
        monthly_other_count = 0
        monthly_matched_retweet_count = 0
        monthly_matched_quote_count = 0
        # Maintain dictionaries for user score totals and valid-record counts.
        user_bias_score = {}
        user_appearance_count = {}
        # Directory path.
        folder_path = project_path('data', f'sources/without_url/output_{month}')
        
        # Process files ending in -output.csv.
        for filename in os.listdir(folder_path):
            if filename.endswith("-output.csv"):
                # print(folder_path)
                # print(filename)
                file_path = os.path.join(folder_path, filename)
                # print(file_path)
                df = pd.read_csv(file_path, usecols=['retweeted_user_id', 'retweet_origin_user_id',
                                                     'quoted_origin_user_id'],
                                 dtype={'retweeted_user_id': 'str', 'retweet_origin_user_id': 'str',
                                        'quoted_origin_user_id': 'str'})
                # print(df)
                print('正在处理：', file_path)

                for index, row in df.iterrows():
                    user_id = row['retweeted_user_id']
                    retweet_user_id = row['retweet_origin_user_id']  # Read the source URL or author field for this record.
                    quoted_user_id = row['quoted_origin_user_id']  # Read the source URL or author field for this record.

                    if pd.notna(retweet_user_id):
                        # print(f"{user_id}   1")
                        monthly_retweet_count += 1
                        score = url_score.get(retweet_user_id)  # Return None when the lookup key has no score.

                        if score is not None:  # Continue scoring only when the lookup returns a score, including zero.
                            monthly_matched_retweet_count += 1
                            if user_id in user_bias_score:
                                user_bias_score[user_id] += score
                                user_appearance_count[user_id] += 1
                            else:
                                user_bias_score[user_id] = score
                                user_appearance_count[user_id] = 1
                    elif pd.notna(quoted_user_id):
                        # print(f"{user_id}   2")
                        monthly_quote_count += 1
                        score = url_score.get(quoted_user_id)  # Return None when the lookup key has no score.

                        if score is not None:  # Continue scoring only when the lookup returns a score, including zero.
                            monthly_matched_quote_count += 1
                            if user_id in user_bias_score:
                                user_bias_score[user_id] += score
                                user_appearance_count[user_id] += 1
                            else:
                                user_bias_score[user_id] = score
                                user_appearance_count[user_id] = 1
                    elif pd.isna(retweet_user_id) and pd.isna(quoted_user_id):
                        # print(f"{user_id}   3")
                        monthly_missing_source_count += 1
                    else:
                        monthly_other_count += 1

        print(
            f"retweet_num:{monthly_retweet_count}\tquoted_num:{monthly_quote_count}\tnot_num:{monthly_missing_source_count}\tother_num:{monthly_other_count}\t"
            f"retweet_have_soure_num:{monthly_matched_retweet_count}\tquoted_have_num:{monthly_matched_quote_count}")

        # Configure logging.
        logging.basicConfig(filename=project_path('outputs', 'logs/without_bias.log'), level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s')

        # Format the log message.
        log_message = (
            f"retweet_num:{monthly_retweet_count}\tquoted_num:{monthly_quote_count}\tnot_num:{monthly_missing_source_count}\tother_num:{monthly_other_count}\t"
            f"retweet_have_soure_num:{monthly_matched_retweet_count}\tquoted_have_num:{monthly_matched_quote_count}")

        # Record the summary in the log.
        logging.info(log_message)

        # Combine user IDs, score totals and counts into an output table.
        user_stats = pd.DataFrame({
            'user_id': list(user_bias_score.keys()),
            'total_score': list(user_bias_score.values()),
            'appearance_count': list(user_appearance_count.values())
        })

        print(user_stats)

        # Save the table as CSV.
        output_path = project_path('outputs', f'analyses/Average_Bias_Rating/media_average_rating/without_url-rating/user_bias_scores_{month}.csv')

        user_stats.to_csv(output_path, index=False)









if __name__ == "__main__":
    # Display complete columns without truncation.
    pd.set_option('display.max_colwidth', None)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)

    user_bias_by_without_url()










