import os
import shutil

def copy_and_rename_images(input_folder, input_mask_folder):
    """

    Args:
    - input_folder (str): 主文件夹路径，包含 "input" 和 "masks" 子文件夹。
    - frontright_path (str): "frontright.png" 的完整路径。
    - frontleft_path (str): "frontleft.png" 的完整路径。
    """
    # 定义 input 和 masks 文件夹路径
    cameras = ['cam_front_center', 'cam_front_left', 'cam_front_right', 'cam_rear_center', 'cam_side_left', 'cam_side_right']  # 相机名称
    input_subfolder = os.path.join(input_folder, "inputs/images")
    output_masks_folder = os.path.join(input_folder, "inputs/ego_masks")
    
    input_cam_masks = os.listdir(input_mask_folder)
    # 创建 masks 文件夹（如果不存在）
    os.makedirs(output_masks_folder, exist_ok=True)
    
    for subcam_name in os.listdir(input_subfolder):
        if subcam_name not in cameras:
            raise ValueError(f"Unexpected camera name: {subcam_name}")
        subcam_mask_file = f"{subcam_name}.png"
        if subcam_mask_file not in input_cam_masks:
            print(f"{subcam_name} don't have ego mask.")
            continue

        input_cam_folder = os.path.join(input_subfolder, subcam_name)

        output_masks_camfolder = os.path.join(output_masks_folder, subcam_name)
        os.makedirs(output_masks_camfolder, exist_ok=True)

        for filename in os.listdir(input_cam_folder):
            source_path = os.path.join(input_mask_folder, subcam_mask_file)
            if filename.endswith(('.png', '.jpg', '.jpeg')):  # 判断是否是图片
                # 构造目标文件路径
                target_filename = f"{filename}.png"
                target_path = os.path.join(output_masks_camfolder, target_filename)

                # 复制并重命名文件
                shutil.copy(source_path, target_path)
                print(f"Copied {source_path} to {target_path}")
    return output_masks_folder

# # 示例使用
# input_folder = "data/Ingolstadt_3-10_7-0_downsampled5_front_left_front_right"  # 主文件夹路径
# input_mask_folder = "data/a2d2_masks"  # masks 子文件夹路径

# copy_and_rename_images(input_folder, input_mask_folder)
