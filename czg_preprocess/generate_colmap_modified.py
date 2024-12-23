#
# Copyright (C) 2024, Inria
# GRAPHDECO research group, https://team.inria.fr/graphdeco
# All rights reserved.
#
# This software is free for non-commercial, research and evaluation use 
# under the terms of the LICENSE.md file.
#
# For inquiries contact  george.drettakis@inria.fr
#

import os, sys, shutil
import subprocess
import argparse
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from preprocess.read_write_model import read_images_binary, write_images_binary, Image
from generate_ego_mask import copy_and_rename_images
import time, platform

# # add a new environment variable to the os.environ
# os.environ['use_gps'] = 'False'

def replace_images_by_masks(images_file, out_file):
    """Replace images.jpg to images.png in the colmap images.bin to process masks the same way as images."""
    images_metas = read_images_binary(images_file)
    out_images_metas = {}
    for key in images_metas:
        in_image_meta = images_metas[key]
        out_images_metas[key] = Image(
            id=key,
            qvec=in_image_meta.qvec,
            tvec=in_image_meta.tvec,
            camera_id=in_image_meta.camera_id,
            name=in_image_meta.name[:-3]+"png",
            xys=in_image_meta.xys,
            point3D_ids=in_image_meta.point3D_ids,
        )
    
    write_images_binary(out_images_metas, out_file)

def setup_dirs(project_dir):
    """Create the directories that will be required."""
    if not os.path.exists(project_dir):
        print("creating project dir.")
        os.makedirs(project_dir)
    
    if not os.path.exists(os.path.join(project_dir, "camera_calibration/aligned")):
        os.makedirs(os.path.join(project_dir, "camera_calibration/aligned/sparse/0"))

    if not os.path.exists(os.path.join(project_dir, "camera_calibration/rectified")):
        os.makedirs(os.path.join(project_dir, "camera_calibration/rectified"))

    if not os.path.exists(os.path.join(project_dir, "camera_calibration/unrectified")):
        os.makedirs(os.path.join(project_dir, "camera_calibration/unrectified"))
        os.makedirs(os.path.join(project_dir, "camera_calibration/unrectified", "sparse"))

    if not os.path.exists(os.path.join(project_dir, "camera_calibration/unrectified", "sparse")):
        os.makedirs(os.path.join(project_dir, "camera_calibration/unrectified", "sparse"))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--project_dir', type=str, required=True)
    parser.add_argument('--images_dir', default="", help="Will be set to project_dir/inputs/images if not set")
    parser.add_argument('--masks_dir', default="", help="Will be set to project_dir/inputs/masks if exists and not set")
    parser.add_argument('--random_seed', type=int, default=0, help="Random seed for the feature extraction")
    # new arguments for hierarchical mapper
    parser.add_argument('--image_overlap', type=int, default=50, help="The overlap between images in the hierarchical mapper")
    parser.add_argument('--leaf_max_num_images', type=int, default=500, help="The maximum number of images in a leaf node in the hierarchical mapper")
    parser.add_argument('--max_model_overlap', type=int, default=20, help="The maximum overlap between models in the hierarchical mapper")
    parser.add_argument('--init_num_trials', type=int, default=200, help="The number of trials for the initial reconstruction in the hierarchical mapper")
    #
    parser.add_argument('--not_use_hierarchical', action='store_true', help="Use hierarchical mapper to generate the colmap")
    # temporally not change the default value of the following arguments
    parser.add_argument('--single_camera', action='store_true', help="Use one camera per folder")
    parser.add_argument('--use_seq_matcher', action='store_true', help="Use sequential matcher to generate the colmap")
    parser.add_argument('--not_use_loop', action='store_true', help="Do not use loop closure in sequential matcher")
    parser.add_argument('--use_gps', action='store_true', help="Use GPS data to form matching images")
    parser.add_argument('--not_only_unrectified', action='store_true', help="Do not only generate unrectified images")
    parser.add_argument('--not_use_ego_masks', action='store_true', help="Do not use ego masks")
    args = parser.parse_args()
    
    source_project_dir = args.project_dir
    if args.not_use_hierarchical:
        args.project_dir = source_project_dir + "_wo-hier"
    else: # use hierarchical mapper # add the hierarchical mapper arguments to the project_dir
        args.project_dir = source_project_dir + f"_imgoverlap{args.image_overlap}_leaf{args.leaf_max_num_images}_modeloverlap{args.max_model_overlap}_inittrial{args.init_num_trials}"
    
    if args.single_camera:
        args.project_dir += "_single_camera"

    if args.random_seed != 0:
        args.project_dir += f"_seed{args.random_seed}"
    
    os.makedirs(args.project_dir, exist_ok=True)

    if args.images_dir == "":
        args.images_dir = os.path.join(source_project_dir, "inputs/images")
    if args.masks_dir == "":
        args.masks_dir = os.path.join(source_project_dir, "inputs/masks")
        args.masks_dir = args.masks_dir if os.path.exists(args.masks_dir) else ""

    colmap_exe = "colmap.bat" if platform.system() == "Windows" else "colmap"
    start_time = time.time()

    print(f"Project will be built here ${args.project_dir} base images are available there ${args.images_dir}.")
    setup_dirs(args.project_dir)

    ## create ego masks for the images
    if not args.not_use_ego_masks:
        input_mask_folder = "data/a2d2_masks"  # masks path
        ego_masks_dir = copy_and_rename_images(source_project_dir, input_mask_folder)
    else:
        ego_masks_dir = ""

    ## Feature extraction, matching then mapper to generate the colmap.
    print("extracting features ...")
    colmap_feature_extractor_args = [
        colmap_exe, "feature_extractor",
        "--random_seed", f"{args.random_seed}",
        "--database_path", f"{args.project_dir}/camera_calibration/unrectified/database.db",
        "--image_path", f"{args.images_dir}",
        "--ImageReader.mask_path", f"{ego_masks_dir}",
        "--ImageReader.default_focal_length_factor", "0.5",
        "--ImageReader.camera_model", "PINHOLE", #"OPENCV",
        ]
    colmap_feature_extractor_args += ["--ImageReader.single_camera", "1",] if args.single_camera else ["--ImageReader.single_camera_per_folder", "1",]
    
    try:
        subprocess.run(colmap_feature_extractor_args, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error executing colmap feature_extractor: {e}")
        sys.exit(1)

    # remove ego masks if they were created
    if not args.not_use_ego_masks:
        shutil.rmtree(ego_masks_dir)
        print(f"remove the ego_masks folder {ego_masks_dir} to save space.")

    if args.use_seq_matcher:
        sequential_matcher_args = [
            colmap_exe, "sequential_matcher",
            "--random_seed", f"{args.random_seed}",
            "--database_path", f"{args.project_dir}/camera_calibration/unrectified/database.db"]
        if not args.not_use_loop:
            sequential_matcher_args +=["--SequentialMatching.loop_detection", "1",
                "--SequentialMatching.vocab_tree_path", "/home/yimingli/Downloads/vocab_tree_flickr100K_words256K.bin",
            ]
        try:
            subprocess.run(sequential_matcher_args, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error executing sequential_matcher: {e}")
            sys.exit(1)
    else:
        print("making custom matches...")
        make_colmap_custom_matcher_args = [
            "python", f"czg_preprocess/make_colmap_custom_matcher_modified.py",
            "--image_path", f"{args.images_dir}",
            "--output_path", f"{args.project_dir}/camera_calibration/unrectified/matching.txt",
        ]
        make_colmap_custom_matcher_args += ["--use_gps"] if args.use_gps else []

        try:
            subprocess.run(make_colmap_custom_matcher_args, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error executing make_colmap_custom_matcher: {e}")
            sys.exit(1)

        ## Feature matching
        print("matching features...")
        colmap_matches_importer_args = [
            colmap_exe, "matches_importer",
            "--random_seed", f"{args.random_seed}",
            "--database_path", f"{args.project_dir}/camera_calibration/unrectified/database.db",
            "--match_list_path", f"{args.project_dir}/camera_calibration/unrectified/matching.txt"
            ]
        try:
            subprocess.run(colmap_matches_importer_args, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error executing colmap matches_importer: {e}")
            sys.exit(1)

    ## Generate sfm pointcloud
    print("generating sfm point cloud...")
    if not args.not_use_hierarchical:
        colmap_hierarchical_mapper_args = [
            colmap_exe, "hierarchical_mapper",
            "--random_seed", f"{args.random_seed}",
            "--database_path", f"{args.project_dir}/camera_calibration/unrectified/database.db",
            "--image_path", f"{args.images_dir}",
            "--output_path", f"{args.project_dir}/camera_calibration/unrectified/sparse",
            "--image_overlap", f"{args.image_overlap}",
            "--leaf_max_num_images", f"{args.leaf_max_num_images}",
            "--Mapper.ba_global_function_tolerance", "0.000001",
            "--Mapper.max_model_overlap", f"{args.max_model_overlap}",
            "--Mapper.init_num_trials", f"{args.init_num_trials}",
            ]
        try:
            subprocess.run(colmap_hierarchical_mapper_args, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error executing colmap hierarchical_mapper: {e}")
            sys.exit(1)

        ## Simplify images so that everything takes less time (reading colmap usually takes forever)
        simplify_images_args = [
            "python", f"preprocess/simplify_images.py",
            "--base_dir", f"{args.project_dir}/camera_calibration/unrectified/sparse/0"
        ]
        try:
            subprocess.run(simplify_images_args, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error executing simplify_images: {e}")
            sys.exit(1)
    else:
        colmap_mapper_args = [
            colmap_exe, "mapper",
            "--random_seed", f"{args.random_seed}",
            "--database_path", f"{args.project_dir}/camera_calibration/unrectified/database.db",
            "--image_path", f"{args.images_dir}",
            "--output_path", f"{args.project_dir}/camera_calibration/unrectified/sparse",
            "--Mapper.ba_global_function_tolerance", "0.000001" 
            ]
        try:
            subprocess.run(colmap_mapper_args, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error executing colmap mapper: {e}")
            sys.exit(1)

    if not args.not_only_unrectified:
        end_time = time.time()
        print(f"Preprocessing the unrectified dir done in {(end_time - start_time)/60.0} minutes.")
        sys.exit()

    ## Undistort images
    print(f"undistorting images from {args.images_dir} to {args.project_dir}/camera_calibration/rectified images...")
    colmap_image_undistorter_args = [
        colmap_exe, "image_undistorter",
        "--random_seed", f"{args.random_seed}",
        "--image_path", f"{args.images_dir}",
        "--input_path", f"{args.project_dir}/camera_calibration/unrectified/sparse/0", 
        "--output_path", f"{args.project_dir}/camera_calibration/rectified/",
        "--output_type", "COLMAP",
        "--max_image_size", "2048",
        ]
    try:
        subprocess.run(colmap_image_undistorter_args, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error executing image_undistorter: {e}")
        sys.exit(1)

    if not args.masks_dir == "":
        # create a copy of colmap as txt and replace jpgs with pngs to undistort masks the same way images were distorted
        if not os.path.exists(f"{args.project_dir}/camera_calibration/unrectified/sparse/0/masks"):
            os.makedirs(f"{args.project_dir}/camera_calibration/unrectified/sparse/0/masks")

        shutil.copy(f"{args.project_dir}/camera_calibration/unrectified/sparse/0/cameras.bin", f"{args.project_dir}/camera_calibration/unrectified/sparse/0/masks/cameras.bin")
        shutil.copy(f"{args.project_dir}/camera_calibration/unrectified/sparse/0/points3D.bin", f"{args.project_dir}/camera_calibration/unrectified/sparse/0/masks/points3D.bin")
        replace_images_by_masks(f"{args.project_dir}/camera_calibration/unrectified/sparse/0/images.bin", f"{args.project_dir}/camera_calibration/unrectified/sparse/0/masks/images.bin")

        print("undistorting masks aswell...")
        colmap_image_undistorter_args = [
            colmap_exe, "image_undistorter",
            "--image_path", f"{args.masks_dir}",
            "--input_path", f"{args.project_dir}/camera_calibration/unrectified/sparse/0/masks", 
            "--output_path", f"{args.project_dir}/camera_calibration/tmp/",
            "--output_type", "COLMAP",
            "--max_image_size", "2048",
            ]
        try:
            subprocess.run(colmap_image_undistorter_args, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error executing image_undistorter: {e}")
            sys.exit(1)
        
        make_mask_uint8_args = [
            "python", f"preprocess/make_mask_uint8.py",
            "--in_dir", f"{args.project_dir}/camera_calibration/tmp/images",
            "--out_dir", f"{args.project_dir}/camera_calibration/rectified/masks"
        ]
        try:
            subprocess.run(make_mask_uint8_args, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error executing make_colmap_custom_matcher: {e}")
            sys.exit(1)

        # remove temporary dir containing undistorted masks
        shutil.rmtree(f"{args.project_dir}/camera_calibration/tmp")

    # re-orient + scale colmap
    print(f"re-orient and scaling scene to {args.project_dir}/camera_calibration/aligned/sparse/0")
    reorient_args = [
            "python", f"preprocess/auto_reorient.py",
            "--input_path", f"{args.project_dir}/camera_calibration/rectified/sparse",
            "--output_path", f"{args.project_dir}/camera_calibration/aligned/sparse/0"
        ]
    try:
        subprocess.run(reorient_args, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error executing auto_orient: {e}")
        sys.exit(1)

    end_time = time.time()
    print(f"Preprocessing done in {(end_time - start_time)/60.0} minutes.")
    