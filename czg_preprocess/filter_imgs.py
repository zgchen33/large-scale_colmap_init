import os
from datetime import timedelta
import shutil

# 输入参数
city = 'Ingolstadt' # Ingolstadt, Munich, or Gaimersheim
start_time = timedelta(minutes=3, seconds=10)
end_time = timedelta(minutes=7, seconds=0)

cameras = ['cam_front_left', 'cam_front_right', 'cam_front_center']  # 相机名称
ds_rate = 5  # 降采样帧数

# input dir
input_dir = "/home/yimingli/zhuoguang/datasets/a2d2_jpg/"
input_city_dir = os.path.join(input_dir, city, 'cameras')

output_path = './data'

output_dir_name = f"{city}_{start_time.seconds//60}-{start_time.seconds%60}_{end_time.seconds//60}-{end_time.seconds%60}_downsampled{ds_rate}"
# add the cameras to the output dir name
for camera in cameras:
    output_dir_name += f"_{camera[4:]}"
output_dir = os.path.join(output_path, output_dir_name)
output_dir = os.path.join(output_dir, 'inputs/images')

# 确保输出目录存在
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# 计算帧编号范围
Video_FPS = 30  # 帧率
start_frame = int(start_time.total_seconds() * Video_FPS)
end_frame = int(end_time.total_seconds() * Video_FPS)


# 降采样函数
def downsample_images(camera, start_frame, end_frame, ds_rate, output_dir):
    frame_count = 0
    skip = ds_rate - 1  # 跳过ds_rate-1帧
    input_camera_dir = os.path.join(input_city_dir, camera)

    output_camera_dir = os.path.join(output_dir, camera)
    if not os.path.exists(output_camera_dir):
        os.makedirs(output_camera_dir)
    # get all images and sort them
    images_list = os.listdir(input_camera_dir)
    images_list.sort()
    for frame_idx in range(start_frame, end_frame + 1, skip):
        # 构建图片文件名
        filename = images_list[frame_idx]
        # 读取图片
        image_path = os.path.join(input_camera_dir, filename)
        # use cp instead of mv to keep original images
        if os.path.exists(image_path):
            shutil.copy(image_path, os.path.join(output_camera_dir, filename))
            frame_count += 1
        
        else:
            print(f"File {image_path} does not exist.")
    # print the sentence about the city, the ds_rate, the time span of the downsampled frames, the camera and the number of frames
    print(f"{city} downsampled at {ds_rate}x from {start_time} to {end_time} for camera {camera} with {frame_count} frames.")


# 主函数
def main():
    input_cameras = os.listdir(input_city_dir)
    for camera in cameras:
        if camera not in input_cameras:
            print(f"Camera {camera} not found in {input_city_dir}.")
            raise FileNotFoundError

        downsample_images(camera, start_frame, end_frame, ds_rate, output_dir)

if __name__ == "__main__":
    main()