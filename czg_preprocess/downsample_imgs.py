import os
import shutil

def sample_images_from_subfolders(source_dir, target_dir, interval=10):
    # Create the target directory if it doesn't exist
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    # Iterate over all subfolders in the source directory
    for subfolder in os.listdir(source_dir):
        subfolder_path = os.path.join(source_dir, subfolder)

        # Ensure it's a folder
        if os.path.isdir(subfolder_path):
            dst_sub_path = os.path.join(target_dir, subfolder)
            if not os.path.exists(dst_sub_path):
                os.makedirs(dst_sub_path)
            # Get all image files in the subfolder (sorted by file name)
            image_files = sorted([f for f in os.listdir(subfolder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))])
            
            # Sample every 'interval'-th image
            sampled_files = image_files[::interval]

            # Copy sampled images to the target directory
            for img_file in sampled_files:
                src_img_path = os.path.join(subfolder_path, img_file)
                dst_img_path = os.path.join(dst_sub_path, img_file)
                shutil.copy(src_img_path, dst_img_path)
                print(f"Copied {src_img_path} to {dst_img_path}")

# Example usage
source_directory = "/home/yimingli/zhuoguang/datasets/a2d2_jpg/Ingolstadt/cameras"
target_directory = "/home/yimingli/zhuoguang/datasets/a2d2_jpg/Ingolstadt_subset-5/cameras"
sample_images_from_subfolders(source_directory, target_directory, interval=5)
