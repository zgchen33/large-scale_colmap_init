import os
import shutil
from PIL import Image
from tqdm import tqdm

def convert_png_to_jpg(source_folder, target_folder):
    # 确保目标文件夹存在
    if not os.path.exists(target_folder):
        os.makedirs(target_folder)

    # 获取源文件夹中所有 PNG 文件
    png_files = [f for f in os.listdir(source_folder) if f.endswith('.png')]
    
    # 使用 tqdm 添加进度条
    for filename in tqdm(png_files, desc="Converting PNG to JPG", unit="file"):
        # 获取 PNG 文件的完整路径
        png_path = os.path.join(source_folder, filename)
        
        # 打开 PNG 图片
        with Image.open(png_path) as img:
            # 转换为 RGB 模式
            rgb_img = img.convert('RGB')
            
            # 构造 JPG 文件的完整路径
            jpg_filename = f"{os.path.splitext(filename)[0]}.jpg"
            jpg_path = os.path.join(target_folder, jpg_filename)
            
            # 保存为 JPG 格式
            rgb_img.save(jpg_path, 'JPEG')
        
        # only remove the png
        os.remove(png_path)

    # 删除整个源文件夹及其内容
    # shutil.rmtree(source_folder)

# 示例：指定源文件夹和目标文件夹
source_folder = '/home/yimingli/zhuoguang/datasets/a2d2/Ingolstadt/cam_front_center'  # 替换为你的源文件夹路径
target_folder = '/home/yimingli/zhuoguang/datasets/a2d2_jpg/Ingolstadt/cam_front_center'  # 替换为你的目标文件夹路径

# 调用转换函数
convert_png_to_jpg(source_folder, target_folder)

print(0)
