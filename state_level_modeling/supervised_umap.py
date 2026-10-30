from pathlib import Path as _ReleasePath
import sys as _release_sys
_release_root = next(_p for _p in _ReleasePath(__file__).resolve().parents if (_p / 'runtime_config.py').is_file())
_release_sys.path.insert(0, str(_release_root))
from runtime_config import project_path

# import pandas as pd
# import numpy as np
# import matplotlib.pyplot as plt
# import seaborn as sns
# import umap  # 导入 UMAP
# from sklearn.preprocessing import StandardScaler

# # 设置中文字体支持
# plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans'] 
# plt.rcParams['axes.unicode_minus'] = False

# # 1. 数据准备
# file_path = 'df_combined.csv'
# df = pd.read_csv(file_path)

# # 计算 Y: 共和党 - 民主党
# try:
#     df['Y'] = df['Republican Vote Percentage'] - df['Democratic Vote Percentage']
# except KeyError:
#     df['Y'] = df.iloc[:, 3] - df.iloc[:, 2]

# # 提取特征列
# feature_cols = df.columns[4:]
# numeric_cols = df[feature_cols].select_dtypes(include=[np.number]).columns.tolist()
# feature_cols = [c for c in numeric_cols if 'Unnamed' not in c and c != 'Y']

# print(f"使用的特征数量: {len(feature_cols)}")
# X_raw = df[feature_cols]

# # 2. 数据预处理
# X_log = np.log1p(X_raw)
# scaler = StandardScaler()
# X_scaled = scaler.fit_transform(X_log)
# X_scaled = scaler.fit_transform(X_raw)


# # ---------------------------------------------------------
# # 3. UMAP 降维 (替换 PCA)
# # ---------------------------------------------------------
# # n_neighbors: 邻居数量，较小捕捉局部结构，较大捕捉全局结构
# # min_dist: 点之间的最小距离，控制压缩程度
# reducer = umap.UMAP(n_neighbors=15, min_dist=0.1, n_components=2, random_state=42)
# embedding = reducer.fit_transform(X_scaled)

# # 创建包含 UMAP 结果的 DataFrame
# umap_df = pd.DataFrame(data=embedding, columns=['UMAP1', 'UMAP2'])
# umap_df['State'] = df['State']
# umap_df['Y'] = df['Y']
# umap_df['Abs_Y'] = df['Y'].abs()

# # 定义摇摆州 (根据你的需求调整阈值)
# swing_threshold = 5.0 # 假设 5% 以内算摇摆
# umap_df['Is_Swing'] = umap_df['Abs_Y'] < swing_threshold

# # 4. 绘图
# plt.figure(figsize=(14, 8))

# # A. 绘制所有州 (散点)
# sc = plt.scatter(umap_df['UMAP1'], umap_df['UMAP2'], c=umap_df['Y'], cmap='coolwarm', 
#                  s=100, alpha=0.8, edgecolor='k', vmin=-30, vmax=30)

# cbar = plt.colorbar(sc)
# cbar.set_label('得票率差值 (Rep - Dem)', fontsize=12)

# # B. 标记摇摆州
# swing_states = umap_df[umap_df['Is_Swing']]
# plt.scatter(swing_states['UMAP1'], swing_states['UMAP2'], s=150, facecolors='none', 
#             edgecolors='green', linewidth=2, label='摇摆州')

# # C. 添加州名标签
# to_label = pd.concat([
#     swing_states, 
#     umap_df.nlargest(3, 'Y'), 
#     umap_df.nsmallest(3, 'Y')
# ])

# for i, row in to_label.iterrows():
#     plt.annotate(row['State'], (row['UMAP1'], row['UMAP2']), 
#                  xytext=(5, 5), textcoords='offset points', fontsize=9, alpha=0.9)

# # D. 拟合趋势线 (在 UMAP 空间中通常比 PCA 更具局部性)
# sort_idx = np.argsort(umap_df['UMAP1'])
# x_sorted = umap_df['UMAP1'].iloc[sort_idx]
# y_sorted = umap_df['UMAP2'].iloc[sort_idx]

# z_poly = np.polyfit(x_sorted, y_sorted, 3) # UMAP 可能更适合 3 阶或低阶拟合
# p_poly = np.poly1d(z_poly)
# x_curve = np.linspace(x_sorted.min(), x_sorted.max(), 300)
# plt.plot(x_curve, p_poly(x_curve), "k--", alpha=0.5, linewidth=2, label='UMAP 空间分布趋势')

# # 装饰图形
# plt.title('各州媒体消费特征 UMAP 分析', fontsize=16)
# plt.xlabel('UMAP 维度 1', fontsize=12)
# plt.ylabel('UMAP 维度 2', fontsize=12)
# plt.axhline(0, color='grey', linestyle=':', alpha=0.5)
# plt.axvline(0, color='grey', linestyle=':', alpha=0.5)
# plt.legend(loc='upper right')
# plt.grid(True, alpha=0.3)

# plt.tight_layout()

# import os # 引入os模块用于处理路径

# output_path = os.path.join(output_dir, 'State_UMAP_Analysis.png')
# plt.savefig(output_path, dpi=300)
# # plt.savefig('State_UMAP_Analysis.png', dpi=300)
# plt.show()

# # ---------------------------------------------------------
# # 5. 特征关联度分析 (替代 PCA Loading Analysis)
# # ---------------------------------------------------------
# print("\n--- 特征与 UMAP 轴的关联度 (相关系数) ---")
# # 因为 UMAP 没有 components_，我们通常计算原始特征与 UMAP 坐标的相关性来解释含义
# correlations = {}
# for col in feature_cols:
#     correlations[col] = [
#         np.corrcoef(X_scaled[:, feature_cols.index(col)], umap_df['UMAP1'])[0, 1],
#         np.corrcoef(X_scaled[:, feature_cols.index(col)], umap_df['UMAP2'])[0, 1]
#     ]

# corr_df = pd.DataFrame.from_dict(correlations, orient='index', columns=['UMAP1_Corr', 'UMAP2_Corr'])

# print("\n[与 UMAP1 相关性最高的特征]:")
# print(corr_df['UMAP1_Corr'].sort_values(ascending=False).head(5))

# print("\n[与 UMAP1 相关性最低的特征]:")
# print(corr_df['UMAP1_Corr'].sort_values(ascending=True).head(5))
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import umap
from sklearn.preprocessing import StandardScaler
import os # 引入os模块用于处理路径

# 设置中文字体支持
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans'] 
plt.rcParams['axes.unicode_minus'] = False
# 1. 数据准备
file_path = project_path('data', 'state_level_modeling/state_features.csv')
df = pd.read_csv(file_path)

# 计算政治倾向 Y
try:
    df['Y'] = df['Republican Vote Percentage'] - df['Democratic Vote Percentage']
except KeyError:
    df['Y'] = df.iloc[:, 3] - df.iloc[:, 2]

# 提取特征
feature_cols = [c for c in df.columns[4:] if 'Unnamed' not in c and c != 'Y']
X_raw = df[feature_cols].select_dtypes(include=[np.number])

# ---------------------------------------------------------
# 2. [新增] 按行进行 CLR 变换 (Centered Log-Ratio)
# ---------------------------------------------------------
EPS = 1e-6
# A. 加上极小值防止 log(0)
X_safe = X_raw + EPS

# B. 计算每一行的几何均值 (Geometric Mean)
# 先取 log，求均值，再 exp 还原回去
geom_mean = np.exp(np.log(X_safe).mean(axis=1))

# C. 执行 CLR 变换：log(x_i / g(x))
# 这会将原始数据映射到实数空间，且消除了总量差异
X_clr = np.log(X_safe.div(geom_mean, axis=0))

# D. 变换后仍建议进行标准化，确保 UMAP 对所有特征权重均衡
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_clr)

# ---------------------------------------------------------
# 3. 半监督 UMAP 降维
# ---------------------------------------------------------
y_train = df['Y'].values 

reducer = umap.UMAP(
    n_neighbors=25,           # 增加邻居数以获得更好的全局分布
    min_dist=0.15,            # 稍微增大间距，让点分布更美观
    n_components=2,
    metric='euclidean',       # CLR 之后建议使用欧氏距离
    target_metric='l2',
    target_weight=0.7,        # 增强政治倾向的引导力度
    random_state=42
)

embedding = reducer.fit_transform(X_scaled, y=y_train)

# ---------------------------------------------------------
# 4. 结果包装与绘图
# ---------------------------------------------------------
umap_df = pd.DataFrame(data=embedding, columns=['UMAP1', 'UMAP2'])
umap_df['State'] = df['State']
umap_df['Y'] = df['Y']

plt.figure(figsize=(14, 9))
sc = plt.scatter(umap_df['UMAP1'], umap_df['UMAP2'], 
                 c=umap_df['Y'], cmap='coolwarm', 
                 s=130, alpha=0.85, edgecolor='k', linewidth=0.5, vmin=-30, vmax=30)

plt.colorbar(sc, label='得票率差值 (Rep - Dem)')

# 标注摇摆州和极端州
to_label = pd.concat([
    umap_df.nlargest(5, 'Y'), 
    umap_df.nsmallest(5, 'Y'),
    umap_df[umap_df['Y'].abs() < 5] # 摇摆州
]).drop_duplicates(subset=['State'])

for i, row in to_label.iterrows():
    plt.annotate(row['State'], (row['UMAP1'], row['UMAP2']), 
                 xytext=(5, 5), textcoords='offset points', fontsize=10, fontweight='bold')

plt.title('CLR 变换 + 半监督 UMAP：各州媒体消费特征分析', fontsize=16)
plt.grid(True, alpha=0.2)
output_dir = project_path('outputs', 'state_level_modeling/embedding')
output_path = os.path.join(output_dir, 'State_UMAP_Analysis.png')
plt.savefig(output_path, dpi=1600)
plt.show()

# plt.savefig('State_UMAP_Analysis.png', dpi=300)

# 计算 CLR 变换后的特征与 UMAP 两个维度的相关性
# X_clr 是你做完 CLR 变换后的 DataFrame
correlations = {}
for col in feature_cols:
    # 计算该特征与 UMAP1 的相关性
    corr_u1 = np.corrcoef(X_clr[col], umap_df['UMAP1'])[0, 1]
    # 计算该特征与 UMAP2 的相关性
    corr_u2 = np.corrcoef(X_clr[col], umap_df['UMAP2'])[0, 1]
    correlations[col] = [corr_u1, corr_u2]

# 转换为 DataFrame 方便查看
importance_df = pd.DataFrame.from_dict(correlations, orient='index', columns=['UMAP1_Corr', 'UMAP2_Corr'])

# ---------------------------------------------------------
# 重点查看：哪些特征最能代表红蓝对立？
# ---------------------------------------------------------
# 假设 UMAP1 是区分红蓝的主要轴
print("\n--- 与 UMAP 维度 1 最相关的特征 (Top 10) ---")
# 正相关最强：可能代表随着该特征增加，州变得更“红”或更“蓝”
print(importance_df['UMAP1_Corr'].sort_values(ascending=False).head(10))

print("\n--- 与 UMAP 维度 1 负相关最强的特征 (Top 10) ---")
print(importance_df['UMAP1_Corr'].sort_values(ascending=True).head(10))