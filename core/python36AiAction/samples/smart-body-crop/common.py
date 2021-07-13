"""Executable Python script for running Python actions.

/*
 * Licensed to the Apache Software Foundation (ASF) under one or more
 * contributor license agreements.  See the NOTICE file distributed with
 * this work for additional information regarding copyright ownership.
 * The ASF licenses this file to You under the Apache License, Version 2.0
 * (the "License"); you may not use this file except in compliance with
 * the License.  You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
"""

'''
Some code is based on Ildoo Kim's code (https://github.com/ildoonet/tf-openpose) and https://gist.github.com/alesolano/b073d8ec9603246f766f9f15d002f4f4
and derived from the OpenPose Library (https://github.com/CMU-Perceptual-Computing-Lab/openpose/blob/master/LICENSE)
'''

from collections import defaultdict
from enum import Enum
import math
import numpy as np
import itertools
from scipy.ndimage.filters import maximum_filter
from PIL import Image, ImageDraw


class CocoPart(Enum):
    Nose = 0
    Neck = 1
    RShoulder = 2
    RElbow = 3
    RWrist = 4
    LShoulder = 5
    LElbow = 6
    LWrist = 7
    RHip = 8
    RKnee = 9
    RAnkle = 10
    LHip = 11
    LKnee = 12
    LAnkle = 13
    REye = 14
    LEye = 15
    REar = 16
    LEar = 17
    Background = 18


parts_dict = {'Nose': [0], 'Neck': [1], 'Shoulders': [2, 5], 'Elbows': [3, 6], 'Wrists': [
    4, 7], 'Hips': [8, 11], 'Knees': [9, 12], 'Ankles': [10, 13], 'Eyes': [14, 15], 'Ears': [16, 17]}
# parts_if_notfound_upper={'Eyes':'Ears','Ears':'Eyes','Nose':'Ears','Neck':'Nose','Shoulders':'Neck','Elbows':'Shoulders','Wrists':'Elbows','Hips':'Wrists#','Knees':'Hips'}
# parts_if_notfound_lower=#{'Ears':'Nose','Nose':'Neck','Neck':'Shoulders','Shoulders':'Elbows','Elbows':'Wrists','Wrists':'Hips','Hips':'Knees',
#                  'Knees':'Ankles','Ankles':'Knees'}
body_parts_dict = {0: 'Eyes', 1: 'Ears', 2: 'Nose', 3: 'Neck', 4: 'Shoulders',
                   5: 'Elbows', 6: 'Wrists', 7: 'Hips', 8: 'Knees', 9: 'Ankles'}

CocoPairs = [
    (1, 2), (1, 5), (2, 3), (3, 4), (5, 6), (6,
                                             7), (1, 8), (8, 9), (9, 10), (1, 11),
    (11, 12), (12, 13), (1, 0), (0, 14), (14,
                                          16), (0, 15), (15, 17), (2, 16), (5, 17)
]   # = 19
CocoPairsRender = CocoPairs[:-2]
CocoPairsNetwork = [
    (12, 13), (20, 21), (14, 15), (16, 17), (22,
                                             23), (24, 25), (0, 1), (2, 3), (4, 5),
    (6, 7), (8, 9), (10, 11), (28, 29), (30, 31), (34,
                                                   35), (32, 33), (36, 37), (18, 19), (26, 27)
]  # = 19

CocoColors = [(255, 0, 0), (255, 85, 0), (255, 170, 0), (255, 255, 0), (170, 255, 0), (85, 255, 0), (0, 255, 0),
              (0, 255, 85), (0, 255, 170), (0, 255, 255), (0,
                                                           170, 255), (0, 85, 255), (0, 0, 255), (85, 0, 255),
              (170, 0, 255), (255, 0, 255), (255, 0, 170), (255, 0, 85)]


NMS_Threshold = 0.1
InterMinAbove_Threshold = 6
Inter_Threashold = 0.1
Min_Subset_Cnt = 4
Min_Subset_Score = 0.8
Max_Human = 96


def human_conns_to_human_parts(human_conns, heatMat):
    human_parts = defaultdict(lambda: None)
    for conn in human_conns:
        human_parts[conn['partIdx'][0]] = (
            conn['partIdx'][0],  # part index
            (conn['coord_p1'][0] / heatMat.shape[2], conn['coord_p1']
             [1] / heatMat.shape[1]),  # relative coordinates
            heatMat[conn['partIdx'][0], conn['coord_p1']
                    [1], conn['coord_p1'][0]]  # score
        )
        human_parts[conn['partIdx'][1]] = (
            conn['partIdx'][1],
            (conn['coord_p2'][0] / heatMat.shape[2],
             conn['coord_p2'][1] / heatMat.shape[1]),
            heatMat[conn['partIdx'][1], conn['coord_p2']
                    [1], conn['coord_p2'][0]]
        )
    return human_parts


def non_max_suppression(heatmap, window_size=3, threshold=NMS_Threshold):
    heatmap[heatmap < threshold] = 0  # set low values to 0
    part_candidates = heatmap * \
        (heatmap == maximum_filter(heatmap, footprint=np.ones((window_size, window_size))))
    return part_candidates


def estimate_pose(heatMat, pafMat):
    if heatMat.shape[2] == 19:
        # transform from [height, width, n_parts] to [n_parts, height, width]
        heatMat = np.rollaxis(heatMat, 2, 0)
    if pafMat.shape[2] == 38:
        # transform from [height, width, 2*n_pairs] to [2*n_pairs, height, width]
        pafMat = np.rollaxis(pafMat, 2, 0)

    # reliability issue.
    heatMat = heatMat - heatMat.min(axis=1).min(axis=1).reshape(19, 1, 1)
    heatMat = heatMat - heatMat.min(axis=2).reshape(19, heatMat.shape[1], 1)

    _NMS_Threshold = max(np.average(heatMat) * 4.0, NMS_Threshold)
    _NMS_Threshold = min(_NMS_Threshold, 0.3)

    coords = []  # for each part index, it stores coordinates of candidates
    for heatmap in heatMat[:-1]:  # remove background
        part_candidates = non_max_suppression(heatmap, 5, _NMS_Threshold)
        coords.append(np.where(part_candidates >= _NMS_Threshold))

    # all connections detected. no information about what humans they belong to
    connection_all = []
    for (idx1, idx2), (paf_x_idx, paf_y_idx) in zip(CocoPairs, CocoPairsNetwork):
        connection = estimate_pose_pair(
            coords, idx1, idx2, pafMat[paf_x_idx], pafMat[paf_y_idx])
        connection_all.extend(connection)

    conns_by_human = dict()
    for idx, c in enumerate(connection_all):
        # at first, all connections belong to different humans
        conns_by_human['human_%d' % idx] = [c]

    no_merge_cache = defaultdict(list)
    empty_set = set()
    while True:
        is_merged = False
        for h1, h2 in itertools.combinations(conns_by_human.keys(), 2):
            if h1 == h2:
                continue
            if h2 in no_merge_cache[h1]:
                continue
            for c1, c2 in itertools.product(conns_by_human[h1], conns_by_human[h2]):
                # if two humans share a part (same part idx and coordinates), merge those humans
                if set(c1['uPartIdx']) & set(c2['uPartIdx']) != empty_set:
                    is_merged = True
                    # extend human1 connectios with human2 connections
                    conns_by_human[h1].extend(conns_by_human[h2])
                    conns_by_human.pop(h2)  # delete human2
                    break
            if is_merged:
                no_merge_cache.pop(h1, None)
                break
            else:
                no_merge_cache[h1].append(h2)

        if not is_merged:  # if no more mergings are possible, then break
            break

    conns_by_human = {h: conns for (
        h, conns) in conns_by_human.items() if len(conns) >= Min_Subset_Cnt}
    conns_by_human = {h: conns for (h, conns) in conns_by_human.items() if max(
        [conn['score'] for conn in conns]) >= Min_Subset_Score}

    humans = [human_conns_to_human_parts(
        human_conns, heatMat) for human_conns in conns_by_human.values()]
    return humans


def estimate_pose_pair(coords, partIdx1, partIdx2, pafMatX, pafMatY):
    connection_temp = []  # all possible connections
    peak_coord1, peak_coord2 = coords[partIdx1], coords[partIdx2]

    for idx1, (y1, x1) in enumerate(zip(peak_coord1[0], peak_coord1[1])):
        for idx2, (y2, x2) in enumerate(zip(peak_coord2[0], peak_coord2[1])):
            score, count = get_score(x1, y1, x2, y2, pafMatX, pafMatY)
            if (partIdx1, partIdx2) in [(2, 3), (3, 4), (5, 6), (6, 7)]:  # arms
                if count < InterMinAbove_Threshold // 2 or score <= 0.0:
                    continue
            elif count < InterMinAbove_Threshold or score <= 0.0:
                continue
            connection_temp.append({
                'score': score,
                'coord_p1': (x1, y1),
                'coord_p2': (x2, y2),
                'idx': (idx1, idx2),  # connection candidate identifier
                'partIdx': (partIdx1, partIdx2),
                'uPartIdx': ('{}-{}-{}'.format(x1, y1, partIdx1), '{}-{}-{}'.format(x2, y2, partIdx2))
            })

    connection = []
    used_idx1, used_idx2 = [], []
    for conn_candidate in sorted(connection_temp, key=lambda x: x['score'], reverse=True):
        if conn_candidate['idx'][0] in used_idx1 or conn_candidate['idx'][1] in used_idx2:
            continue
        connection.append(conn_candidate)
        used_idx1.append(conn_candidate['idx'][0])
        used_idx2.append(conn_candidate['idx'][1])

    return connection


def get_score(x1, y1, x2, y2, pafMatX, pafMatY):
    num_inter = 10
    dx, dy = x2 - x1, y2 - y1
    normVec = math.sqrt(dx ** 2 + dy ** 2)

    if normVec < 1e-4:
        return 0.0, 0

    vx, vy = dx / normVec, dy / normVec

    xs = np.arange(
        x1, x2, dx / num_inter) if x1 != x2 else np.full((num_inter, ), x1)
    ys = np.arange(
        y1, y2, dy / num_inter) if y1 != y2 else np.full((num_inter, ), y1)
    xs = (xs + 0.5).astype(np.int8)
    ys = (ys + 0.5).astype(np.int8)

    # without vectorization
    pafXs = np.zeros(num_inter)
    pafYs = np.zeros(num_inter)
    for idx, (mx, my) in enumerate(zip(xs, ys)):
        pafXs[idx] = pafMatX[my][mx]
        pafYs[idx] = pafMatY[my][mx]

    local_scores = pafXs * vx + pafYs * vy
    thidxs = local_scores > Inter_Threashold

    return sum(local_scores * thidxs), sum(thidxs)


def draw_humans(img1_raw, human_list):
    img = np.asarray(img1_raw)
    img_copied = np.copy(img)
    image_h, image_w = img_copied.shape[:2]
    centers = {}
    c = 10
    for human in human_list:
        part_idxs = human.keys()

        # draw point
        draw = ImageDraw.Draw(img1_raw)
        for i in range(CocoPart.Background.value):
            if i not in part_idxs:
                continue
            part_coord = human[i][1]
            center = (int(part_coord[0] * image_w + 0.5),
                      int(part_coord[1] * image_h + 0.5))
            centers[i] = center
            bbox = (center[0] - c, center[1] - c, center[0] + c, center[1] + c)
            draw.ellipse(bbox, fill=CocoColors[i])

        # draw line
        ctr = 1
        for pair_order, pair in enumerate(CocoPairsRender):
            if pair[0] not in part_idxs or pair[1] not in part_idxs:
                continue
            draw.line((centers[pair[0]][0], centers[pair[0]][1], centers[pair[1]]
                       [0], centers[pair[1]][1]), fill=CocoColors[pair_order], width=5)
    img1_raw = np.asarray(img1_raw)
    del draw
    return img1_raw


def crop_image(img, humans_list, upper_body, lower_body):
    upper_coord = 0.0
    upper_coord_x = 0.0
    lower_coord = 0.0
    lower_coord_x = 0.0

    img = np.asarray(img)
    image_h, image_w = img.shape[:2]

    if upper_body == 'Ankles' or lower_body == 'Eyes':
        raise NameError('Body parts not consistent')

    for human in humans_list:
        parts = human.keys()
        inte = parts_dict[upper_body]  # could be [1] or [2,3]

        if upper_body == 'Nose' or upper_body == 'Neck':
            upper_coord = human[inte[0]][1][1]  # interested only in heights.
            upper_coord_x = human[inte[0]][1][0]
        else:
            upper_coord = (human[inte[0]][1][1] + human[inte[1]][1][1])/2
            upper_coord_x = (human[inte[0]][1][0] + human[inte[1]][1][0])/2

        inte = parts_dict[lower_body]
        if lower_body == 'Nose' or lower_body == 'Neck':
            lower_coord = human[inte[0]][1][1]  # interested only in heights.
            lower_coord_x = human[inte[0]][1][0]
        else:
            lower_coord = (human[inte[0]][1][1] + human[inte[1]][1][1])/2
            lower_coord_x = (human[inte[0]][1][0] + human[inte[1]][1][0])/2

    image_h_u = int(upper_coord * image_h)
    image_h_l = int(lower_coord * image_h)

    image_w_left = int(upper_coord_x * image_w)
    image_w_right = int(lower_coord_x * image_w)
    aspect_ratio = image_h / image_w
    image_w = int((image_w_left + image_w_right)/2)

    img = img[image_h_u:image_h_l]
    wid = int((img.shape[0]/aspect_ratio)/2)
    img = img.transpose(1, 0, 2)
    img = img[image_w-2*wid:image_w+2*wid]
    img = img.transpose(1, 0, 2)

    crop_position = (image_w-2*wid, image_h_u)
    crop_size = (img.shape[1], img.shape[0])

    return img, crop_position, crop_size
