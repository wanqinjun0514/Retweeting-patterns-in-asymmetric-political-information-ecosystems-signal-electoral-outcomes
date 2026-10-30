from pathlib import Path as _ReleasePath
import sys as _release_sys
_release_root = next(_p for _p in _ReleasePath(__file__).resolve().parents if (_p / 'runtime_config.py').is_file())
_release_sys.path.insert(0, str(_release_root))
from runtime_config import project_path


# Use average_bias_points in the interval [-1, 1].

# Write [-1/3, 1/3] to center_user and (1/3, 1] to right_user; retain the stated open/closed boundaries.

import pandas as pd
import os
import matplotlib.pyplot as plt
def classify_monthly_politician_users():
    influencer = 'politician'

    # data_part = 'without'
    # data_part = 'twitter'
    data_part = 'external'
    months = ['2019_12', '2020_01', '2020_02', '2020_03', '2020_04', '2020_05', '2020_06', '2020_07', '2020_08',
                  '2020_09', '2020_10', '2020_11', '2020_12', '2021_01', '2021_02', ]
    for month in months:
        # Define the file paths.
        input_file = project_path('outputs', f'analyses/Average_Bias_Rating/{influencer}_average_rating/{data_part}_url-rating/monthly_users_bias/{month}_output.csv')
        left_user_dir = project_path('outputs', f'analyses/Average_Bias_Rating/{influencer}_average_rating/{data_part}_url-rating/monthly_users_bias/left_user')
        center_user_dir = project_path('outputs', f'analyses/Average_Bias_Rating/{influencer}_average_rating/{data_part}_url-rating/monthly_users_bias/center_user')
        right_user_dir = project_path('outputs', f'analyses/Average_Bias_Rating/{influencer}_average_rating/{data_part}_url-rating/monthly_users_bias/right_user')

        # Create category directories when missing.
        os.makedirs(left_user_dir, exist_ok=True)
        os.makedirs(center_user_dir, exist_ok=True)
        os.makedirs(right_user_dir, exist_ok=True)

        # Read the CSV file.
        df = pd.read_csv(input_file)

        # Apply the classification intervals.
        left_user_df = df[(df['average_bias_points'] >= -1) & (df['average_bias_points'] < -1 / 3)]
        center_user_df = df[(df['average_bias_points'] >= -1 / 3) & (df['average_bias_points'] <= 1 / 3)]
        right_user_df = df[(df['average_bias_points'] > 1 / 3) & (df['average_bias_points'] <= 1)]
        # Sort by retweet_times.
        left_user_df = left_user_df.sort_values(by='retweet_times', ascending=False)
        center_user_df = center_user_df.sort_values(by='retweet_times', ascending=False)
        right_user_df = right_user_df.sort_values(by='retweet_times', ascending=False)
        # Save each category to its corresponding directory.
        left_user_df.to_csv(os.path.join(left_user_dir, f'{month}_left_user.csv'), index=False)
        center_user_df.to_csv(os.path.join(center_user_dir, f'{month}_center_user.csv'), index=False)
        right_user_df.to_csv(os.path.join(right_user_dir, f'{month}_right_user.csv'), index=False)

        print(f"{input_file}的用户分类完成！")


def classify_monthly_media_users():
    influencer = 'media'
    # data_part = 'external'
    # data_part = 'without'
    data_part = 'twitter'
    months = ['2019_12', '2020_01', '2020_02', '2020_03', '2020_04', '2020_05', '2020_06', '2020_07', '2020_08',
              '2020_09', '2020_10', '2020_11', '2020_12', '2021_01', '2021_02']

    # The seven category directories.
    categories = ['extreme_left', 'left', 'left_leaning', 'center', 'right_leaning', 'right', 'extreme_right']

    for month in months:
        # Define the file paths.
        input_file = project_path('outputs', f'analyses/Average_Bias_Rating/{influencer}_average_rating/{data_part}_url-rating/user_bias_scores_by_month/user_bias_scores_{month}.csv')

        # Create all seven category directories when missing.
        for category in categories:
            category_dir = project_path('outputs', f'analyses/Average_Bias_Rating/{influencer}_average_rating/{data_part}_url-rating/user_bias_scores_by_month/{category}')
            os.makedirs(category_dir, exist_ok=True)

        # Read the CSV file.
        df = pd.read_csv(input_file)

        # Apply the seven classification intervals.
        extreme_left_df = df[(df['average_bias_points'] >= -3) & (df['average_bias_points'] < -2.5)]
        left_df = df[(df['average_bias_points'] >= -2.5) & (df['average_bias_points'] < -1.5)]
        left_leaning_df = df[(df['average_bias_points'] >= -1.5) & (df['average_bias_points'] < -0.5)]
        center_df = df[(df['average_bias_points'] >= -0.5) & (df['average_bias_points'] < 0.5)]
        right_leaning_df = df[(df['average_bias_points'] >= 0.5) & (df['average_bias_points'] < 1.5)]
        right_df = df[(df['average_bias_points'] >= 1.5) & (df['average_bias_points'] < 2.5)]
        extreme_right_df = df[(df['average_bias_points'] >= 2.5) & (df['average_bias_points'] <= 3)]

        # Sort each category by appearance_count.
        extreme_left_df = extreme_left_df.sort_values(by='appearance_count', ascending=False)
        left_df = left_df.sort_values(by='appearance_count', ascending=False)
        left_leaning_df = left_leaning_df.sort_values(by='appearance_count', ascending=False)
        center_df = center_df.sort_values(by='appearance_count', ascending=False)
        right_leaning_df = right_leaning_df.sort_values(by='appearance_count', ascending=False)
        right_df = right_df.sort_values(by='appearance_count', ascending=False)
        extreme_right_df = extreme_right_df.sort_values(by='appearance_count', ascending=False)

        # Save each category to its corresponding directory.
        extreme_left_df.to_csv(os.path.join(
            project_path('outputs', f'analyses/Average_Bias_Rating/{influencer}_average_rating/{data_part}_url-rating/user_bias_scores_by_month/extreme_left/{month}_extreme_left_user.csv')),
                               index=False)
        left_df.to_csv(os.path.join(
            project_path('outputs', f'analyses/Average_Bias_Rating/{influencer}_average_rating/{data_part}_url-rating/user_bias_scores_by_month/left/{month}_left_user.csv')),
                       index=False)
        left_leaning_df.to_csv(os.path.join(
            project_path('outputs', f'analyses/Average_Bias_Rating/{influencer}_average_rating/{data_part}_url-rating/user_bias_scores_by_month/left_leaning/{month}_left_leaning_user.csv')),
                               index=False)
        center_df.to_csv(os.path.join(
            project_path('outputs', f'analyses/Average_Bias_Rating/{influencer}_average_rating/{data_part}_url-rating/user_bias_scores_by_month/center/{month}_center_user.csv')),
                         index=False)
        right_leaning_df.to_csv(os.path.join(
            project_path('outputs', f'analyses/Average_Bias_Rating/{influencer}_average_rating/{data_part}_url-rating/user_bias_scores_by_month/right_leaning/{month}_right_leaning_user.csv')),
                                index=False)
        right_df.to_csv(os.path.join(
            project_path('outputs', f'analyses/Average_Bias_Rating/{influencer}_average_rating/{data_part}_url-rating/user_bias_scores_by_month/right/{month}_right_user.csv')),
                        index=False)
        extreme_right_df.to_csv(os.path.join(
            project_path('outputs', f'analyses/Average_Bias_Rating/{influencer}_average_rating/{data_part}_url-rating/user_bias_scores_by_month/extreme_right/{month}_extreme_right_user.csv')),
                                index=False)

        print(f"{input_file}的用户七分类完成！")


# Classify quarterly politician-score records.
def classify_quarterly_politician_users():
    influencer = 'politician'

    # data_part = 'without'
    # data_part = 'twitter'
    data_part = 'external'
    quarters = ['2019_12_2020_01_2020_02', '2020_03_2020_04_2020_05', '2020_06_2020_07_2020_08', '2020_09_2020_10', '2020_11_2020_12', '2021_01_2021_02',]
    for quarter in quarters:
        # Define the file paths.
        input_file = project_path('outputs', f'analyses/Average_Bias_Rating/{influencer}_average_rating/相邻季度之间的转变/{data_part}_url-rating/quaterly_users_bias/quarterly_user_bias{quarter}.csv')
        left_user_dir = project_path('outputs', f'analyses/Average_Bias_Rating/{influencer}_average_rating/{data_part}_url-rating/quaterly_users_bias/left_user')
        center_user_dir = project_path('outputs', f'analyses/Average_Bias_Rating/{influencer}_average_rating/{data_part}_url-rating/quaterly_users_bias/center_user')
        right_user_dir = project_path('outputs', f'analyses/Average_Bias_Rating/{influencer}_average_rating/{data_part}_url-rating/quaterly_users_bias/right_user')

        # Create category directories when missing.
        os.makedirs(left_user_dir, exist_ok=True)
        os.makedirs(center_user_dir, exist_ok=True)
        os.makedirs(right_user_dir, exist_ok=True)

        # Read the CSV file.
        df = pd.read_csv(input_file)

        # Apply the classification intervals.
        left_user_df = df[(df['average_bias_points'] >= -1) & (df['average_bias_points'] < -1 / 3)]
        center_user_df = df[(df['average_bias_points'] >= -1 / 3) & (df['average_bias_points'] <= 1 / 3)]
        right_user_df = df[(df['average_bias_points'] > 1 / 3) & (df['average_bias_points'] <= 1)]
        # Sort by retweet_times.
        left_user_df = left_user_df.sort_values(by='retweet_times', ascending=False)
        center_user_df = center_user_df.sort_values(by='retweet_times', ascending=False)
        right_user_df = right_user_df.sort_values(by='retweet_times', ascending=False)
        # Save each category to its corresponding directory.
        left_user_df.to_csv(os.path.join(left_user_dir, f'{quarter}_left_user.csv'), index=False)
        center_user_df.to_csv(os.path.join(center_user_dir, f'{quarter}_center_user.csv'), index=False)
        right_user_df.to_csv(os.path.join(right_user_dir, f'{quarter}_right_user.csv'), index=False)

        print(f"{input_file}的用户分类完成！")


def classify_quarterly_media_users():
    influencer = 'media'
    # data_part = 'external'
    # data_part = 'without'
    data_part = 'twitter'
    # The seven category directories.
    categories = ['extreme_left', 'left', 'left_leaning', 'center', 'right_leaning', 'right', 'extreme_right']

    quarters = ['2019_12_2020_01_2020_02', '2020_03_2020_04_2020_05', '2020_06_2020_07_2020_08', '2020_09_2020_10',
               '2020_11_2020_12', '2021_01_2021_02', ]
    for quarter in quarters:
        # Define the file paths.
        input_file = project_path('outputs', f'analyses/Average_Bias_Rating/{influencer}_average_rating/{data_part}_url-rating/user_bias_scores_by_quarter/quarterly_user_bias_scores_{quarter}.csv')

        # Create all seven category directories when missing.
        for category in categories:
            category_dir = project_path('outputs', f'analyses/Average_Bias_Rating/{influencer}_average_rating/{data_part}_url-rating/user_bias_scores_by_quarter/{category}')
            os.makedirs(category_dir, exist_ok=True)

        # Read the CSV file.
        df = pd.read_csv(input_file)

        # Apply the seven classification intervals.
        extreme_left_df = df[(df['average_bias_points'] >= -3) & (df['average_bias_points'] < -2.5)]
        left_df = df[(df['average_bias_points'] >= -2.5) & (df['average_bias_points'] < -1.5)]
        left_leaning_df = df[(df['average_bias_points'] >= -1.5) & (df['average_bias_points'] < -0.5)]
        center_df = df[(df['average_bias_points'] >= -0.5) & (df['average_bias_points'] < 0.5)]
        right_leaning_df = df[(df['average_bias_points'] >= 0.5) & (df['average_bias_points'] < 1.5)]
        right_df = df[(df['average_bias_points'] >= 1.5) & (df['average_bias_points'] < 2.5)]
        extreme_right_df = df[(df['average_bias_points'] >= 2.5) & (df['average_bias_points'] <= 3)]

        # Sort each category by appearance_count.
        extreme_left_df = extreme_left_df.sort_values(by='appearance_count', ascending=False)
        left_df = left_df.sort_values(by='appearance_count', ascending=False)
        left_leaning_df = left_leaning_df.sort_values(by='appearance_count', ascending=False)
        center_df = center_df.sort_values(by='appearance_count', ascending=False)
        right_leaning_df = right_leaning_df.sort_values(by='appearance_count', ascending=False)
        right_df = right_df.sort_values(by='appearance_count', ascending=False)
        extreme_right_df = extreme_right_df.sort_values(by='appearance_count', ascending=False)

        # Save each category to its corresponding directory.
        extreme_left_df.to_csv(os.path.join(
            project_path('outputs', f'analyses/Average_Bias_Rating/{influencer}_average_rating/{data_part}_url-rating/user_bias_scores_by_quarter/extreme_left/{quarter}_extreme_left_user.csv')),
                               index=False)
        left_df.to_csv(os.path.join(
            project_path('outputs', f'analyses/Average_Bias_Rating/{influencer}_average_rating/{data_part}_url-rating/user_bias_scores_by_quarter/left/{quarter}_left_user.csv')),
                       index=False)
        left_leaning_df.to_csv(os.path.join(
            project_path('outputs', f'analyses/Average_Bias_Rating/{influencer}_average_rating/{data_part}_url-rating/user_bias_scores_by_quarter/left_leaning/{quarter}_left_leaning_user.csv')),
                               index=False)
        center_df.to_csv(os.path.join(
            project_path('outputs', f'analyses/Average_Bias_Rating/{influencer}_average_rating/{data_part}_url-rating/user_bias_scores_by_quarter/center/{quarter}_center_user.csv')),
                         index=False)
        right_leaning_df.to_csv(os.path.join(
            project_path('outputs', f'analyses/Average_Bias_Rating/{influencer}_average_rating/{data_part}_url-rating/user_bias_scores_by_quarter/right_leaning/{quarter}_right_leaning_user.csv')),
                                index=False)
        right_df.to_csv(os.path.join(
            project_path('outputs', f'analyses/Average_Bias_Rating/{influencer}_average_rating/{data_part}_url-rating/user_bias_scores_by_quarter/right/{quarter}_right_user.csv')),
                        index=False)
        extreme_right_df.to_csv(os.path.join(
            project_path('outputs', f'analyses/Average_Bias_Rating/{influencer}_average_rating/{data_part}_url-rating/user_bias_scores_by_quarter/extreme_right/{quarter}_extreme_right_user.csv')),
                                index=False)

        print(f"{input_file}的用户七分类完成！")


# Plot monthly Left, Center and Right user counts on one chart.
def plot_left_center_right_politician_bias_count():
    # File path.
    file_path = project_path('outputs', 'analyses/Interference with Important Events/filter_retweet_with_bias/covid/external/politician_bias/对服务器第一批导出的新冠用户数据进行id的去重以及keywords的拼接_20241022/covid_external_monthly_bias_category_counts.csv')

    # Load the input data.
    data = pd.read_csv(file_path)

    # Plot the series using the specified colors.
    plt.figure(figsize=(10, 6))
    plt.plot(data['month'], data['Left'], label='Left', marker='o', color='blue')
    plt.plot(data['month'], data['Center'], label='Center', marker='o', color='green')
    plt.plot(data['month'], data['Right'], label='Right', marker='o', color='red')

    # Configure the legend, title and axis labels.
    plt.legend()
    plt.title('Covid External Monthly Bias Category Counts Over Time')
    plt.xlabel('Month')
    plt.ylabel('Counts')
    plt.xticks(rotation=45)  # Rotate x-axis tick labels for readability.
    plt.grid(True)
    plt.savefig(project_path('outputs', 'analyses/Interference with Important Events/filter_retweet_with_bias/covid/external/politician_bias/对服务器第一批导出的新冠用户数据进行id的去重以及keywords的拼接_20241022/covid_external_monthly_bias_category_counts_over_time.png'))
    print("图片已保存为 'monthly_bias_category_counts_over_time.png'")
    # Display the chart.
    plt.tight_layout()
    plt.show()




if __name__ == '__main__':
    classify_monthly_media_users()
    classify_monthly_politician_users()
    classify_quarterly_politician_users()
    classify_quarterly_media_users()
    plot_left_center_right_politician_bias_count()