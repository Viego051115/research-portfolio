"""
合并 18 个 Label Studio 导出的 project，
按 7:1.5:1.5 划分 train/val/test
"""
import os
import shutil
from urllib.parse import unquote
from sklearn.model_selection import train_test_split

# 路径配置
SRC_DIR = r".\正式训练数据集"
DST_DIR = r".\dataset"

# 创建目标目录
for subset in ['train', 'val', 'test']:
    os.makedirs(os.path.join(DST_DIR, 'images', subset), exist_ok=True)
    os.makedirs(os.path.join(DST_DIR, 'labels', subset), exist_ok=True)

# 收集所有图片和对应标注
pairs = []  # [(img_path, label_path, project_name)]

for proj_name in os.listdir(SRC_DIR):
    proj_path = os.path.join(SRC_DIR, proj_name)
    if not os.path.isdir(proj_path):
        continue

    img_dir = os.path.join(proj_path, 'images')
    lbl_dir = os.path.join(proj_path, 'labels')

    if not os.path.exists(img_dir):
        continue

    for img_file in os.listdir(img_dir):
        if not img_file.lower().endswith(('.png', '.jpg', '.jpeg')):
            continue

        img_path = os.path.join(img_dir, img_file)

        # 图片文件名可能有空格，标注文件被 URL 编码了（空格 → %20）
        # 尝试匹配：直接名、URL编码名
        base = os.path.splitext(img_file)[0]
        candidates = [
            base + '.txt',                    # 直接匹配
            base.replace(' ', '%20') + '.txt', # URL编码
        ]

        label_path = None
        for c in candidates:
            candidate_path = os.path.join(lbl_dir, c)
            if os.path.exists(candidate_path):
                label_path = candidate_path
                break

        if label_path:
            pairs.append((img_path, label_path, proj_name))
        else:
            print(f"[WARN] No label: {img_file} in {proj_name}")

print(f"\n总计找到 {len(pairs)} 个图片-标注对")

# 划分：70% train, 15% val, 15% test
train_pairs, temp_pairs = train_test_split(pairs, test_size=0.3, random_state=42)
val_pairs, test_pairs = train_test_split(temp_pairs, test_size=0.5, random_state=42)

print(f"训练集: {len(train_pairs)} 张")
print(f"验证集: {len(val_pairs)} 张")
print(f"测试集: {len(test_pairs)} 张")

# 复制文件（标签文件名做 URL 解码，确保和图片名一致）
def copy_files(pair_list, subset):
    for i, (img_path, lbl_path, proj) in enumerate(pair_list):
        img_name = os.path.basename(img_path)
        # URL 解码标注文件名（%20 → 空格），保证和图片名匹配
        lbl_name = unquote(os.path.basename(lbl_path))

        shutil.copy2(img_path, os.path.join(DST_DIR, 'images', subset, img_name))
        shutil.copy2(lbl_path, os.path.join(DST_DIR, 'labels', subset, lbl_name))

        if (i + 1) % 500 == 0:
            print(f"  {subset}: {i+1}/{len(pair_list)} 完成")

    print(f"  [OK] {subset}: {len(pair_list)} done")

copy_files(train_pairs, 'train')
copy_files(val_pairs, 'val')
copy_files(test_pairs, 'test')

print(f"\n[DONE] Dataset preparation complete!")
print(f"Output: {DST_DIR}")
print(f"结构: images/{{train,val,test}}  +  labels/{{train,val,test}}")
