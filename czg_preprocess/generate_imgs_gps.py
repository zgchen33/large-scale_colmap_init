import os
import numpy as np
import argparse
import json
import bisect

def find_neighbors(t, time_list):
    # Assuming time_list is already sorted in ascending order
    # Find the largest time smaller than t
    left_index = bisect.bisect_left(time_list, t)  # Find the position of the first element >= t
    max_time_before_t = time_list[left_index - 1] if left_index > 0 else None  # Get the largest time smaller than t

    # Find the smallest time larger than t
    right_index = bisect.bisect_right(time_list, t)  # Find the position of the first element > t
    min_time_after_t = time_list[right_index] if right_index < len(time_list) else None  # Get the smallest time larger than t

    return max_time_before_t, min_time_after_t

# write a function using interpolation to get the gps info
def interpolate_gps_info(t, t1, t2, gps_info1, gps_info2):
    # t1 < t < t2
    t_diff = t2 - t1
    t1_diff = t - t1
    t2_diff = t2 - t
    # consider the gps info is [latitude, lat_ref, longitude, long_ref]
    assert gps_info1[1] == gps_info2[1] and gps_info1[3] == gps_info2[3],\
    'The reference is not the same.'

    lat = (t2_diff * gps_info1[0] + t1_diff * gps_info2[0]) / t_diff
    long = (t2_diff * gps_info1[2] + t1_diff * gps_info2[2]) / t_diff
    return [lat, gps_info1[1], long, gps_info1[3]]



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--images_meta_path', default='/home/yimingli/zhuoguang/datasets/a2d2_jpg/Munich/meta_infos')#required=True)
    parser.add_argument('--bus_signal_path', default='/home/yimingli/zhuoguang/datasets/a2d2_jpg/Munich/20190401121727_bus_signals.json')#required=True)
    parser.add_argument('--output_path', default='/home/yimingli/zhuoguang/datasets/a2d2_jpg/Munich/')#required=True)
    args = parser.parse_args()

    city_name = args.images_meta_path.split('/')[-2]

    bus_gps_infos = dict() # timestamp: [latitude, lat_ref, longitude, long_ref]
    # open the bus signal json file
    with open(args.bus_signal_path, 'r') as f:
        bus_signal = json.load(f)

        lat_degs = bus_signal['latitude_degree']['values']
        lat_refs = bus_signal['latitude_direction']['values']
        long_degs = bus_signal['longitude_degree']['values']
        long_refs = bus_signal['longitude_direction']['values']

    # evalute the length of gps is same.
    assert len(lat_degs) == len(lat_refs) == len(long_degs) == len(long_refs),\
    'The length of latitude and longitude is not the same.'
    # assemble to bus_gps_infos
    for idx, info in enumerate(lat_degs):
        # info: [timestamp, value]
        tstamp = info[0]
        lat_deg = info[1]
        lat_ref = 'N' if lat_refs[idx][1] == 0 else 'S'
        long_deg = long_degs[idx][1]
        long_ref = 'E' if long_refs[idx][1] == 0 else 'W'
        bus_gps_infos[tstamp] = [lat_deg, lat_ref, long_deg, long_ref]

    # get the time_list of bus_gps_infos
    bus_time_list = list(bus_gps_infos.keys())

    # open the image meta dir, and get the cam_dirs, don't contain files
    cam_dirs = [d for d in os.listdir(args.images_meta_path) if os.path.isdir(os.path.join(args.images_meta_path, d))]
    img_gps_data = dict()
    for cam_dir in cam_dirs:
        # get the images meta files
        meta_files = [f for f in os.listdir(os.path.join(args.images_meta_path, cam_dir)) if f.endswith('.json')]
        for meta_file in meta_files:
            with open(os.path.join(args.images_meta_path, cam_dir, meta_file), 'r') as f:
                meta_info = json.load(f)
                # get the timestamp
                tstamp = meta_info['cam_tstamp']
            max_time_before_t, min_time_after_t = find_neighbors(tstamp, bus_time_list)
            if max_time_before_t is None or min_time_after_t is None:
                print(f'Cannot find the gps info for {meta_file}')
                continue

            img_gps = interpolate_gps_info(tstamp, max_time_before_t, min_time_after_t, bus_gps_infos[max_time_before_t], bus_gps_infos[min_time_after_t])
            # extract the name of meta_file
            img_name = os.path.splitext(meta_file)[0]
            img_gps_data[img_name] = img_gps   

    img_gps_infos = dict()
    img_gps_infos['data_description'] = ['latitude_degree', 'latitude_reference', 'longitude_degree', 'longitude_reference'] 
    img_gps_infos['data'] = img_gps_data  

    # save the img_gps_data
    with open(os.path.join(args.output_path, f'{city_name}_imgs_gps.json'), 'w') as f:
        json.dump(img_gps_infos, f, indent=4)

    print(0)