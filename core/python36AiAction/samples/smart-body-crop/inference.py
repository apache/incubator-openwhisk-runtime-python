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
Some is based on Ildoo Kim's code (https://github.com/ildoonet/tf-openpose) and https://gist.github.com/alesolano/b073d8ec9603246f766f9f15d002f4f4
and derived from the OpenPose Library (https://github.com/CMU-Perceptual-Computing-Lab/openpose/blob/master/LICENSE)
'''

import tensorflow as tf
import numpy as np
from PIL import Image
from tensorflow.core.framework import graph_pb2
import urllib3
import certifi
import os
import shutil

from common import estimate_pose, crop_image, draw_humans

import time


def print_time(message, start):
    print(message, "{:10.4f}".format(time.time() - start))
    return time.time()


class SmartBodyCrop:
    initialized = False
    tmp_path = '/tmp/'
    tmpfs_path = '/mnt/action/'

    def __init__(self, model_url):
        self.model_url = model_url

    def read_img(self, imgpath, width, height):
        img = Image.open(imgpath)
        orig_width, orig_height = img.size
        # resize the image to match openpose's training data
        # https://github.com/ildoonet/tf-pose-estimation#inference-time
        img.thumbnail((width, height))
        thumbnail_w, thumbnail_h = img.size
        #val_img = val_img.resize((width, height))
        val_img = np.asarray(img, dtype=np.float32)
        val_img = val_img.reshape([1, thumbnail_h, thumbnail_w, 3])
        # val_img = val_img.astype(float)
        val_img = val_img * (2.0 / 255.0) - 1.0  # normalization

        return val_img, img, orig_width, orig_height

    def _download_model(self):
        # check if the model is a ref to local file path
        if type(self.model_url) is str:
            if not self.model_url.startswith('http'):
                return self.model_url

        start = time.time()
        local_model_path = SmartBodyCrop.tmp_path + 'optimized_openpose.pb'
        tmpfs_model_path = SmartBodyCrop.tmpfs_path + 'optimized_openpose.pb'

        if (os.path.isfile(local_model_path)):
            print_time("model was found in the local storage: " +
                       local_model_path, start)
            return local_model_path

        # check if this model was downloaded by another invocation in the tmpfs path
        if (os.path.isfile(tmpfs_model_path)):
            print_time("model was found in the tmpfs storage: " +
                       tmpfs_model_path, start)
            shutil.copy(tmpfs_model_path, local_model_path)
            print_time("model copied FROM tmpfs:" + tmpfs_model_path, start)
            return local_model_path

        http = urllib3.PoolManager(
            cert_reqs='CERT_REQUIRED',
            ca_certs=certifi.where(),
            headers={
                'Accept': 'application/octet-stream',
                'Content-Type': 'application/octet-stream'
            })
        urllib3.disable_warnings()

        r = http.request('GET', self.model_url,
                         preload_content=False,
                         retries=urllib3.Retry(5, redirect=5))

        with open(local_model_path, 'wb') as out:
            while True:
                data = r.read(8192)  # 64 # 8192
                if not data:
                    break
                out.write(data)

        r.release_conn()
        print_time("model downloaded in :", start)

        # copy the file to the tmpfs_model_path to be reused by other actions
        # this seems to work concurrently as per: https://stackoverflow.com/questions/35605463/why-is-concurrent-copy-of-a-file-not-failing
        if (os.path.isdir(SmartBodyCrop.tmpfs_path)):
            shutil.copy(local_model_path, tmpfs_model_path)
            print_time("model copied to tmpfs:" + tmpfs_model_path, start)

        return local_model_path

    def _download_image(self, image):
        start = time.time()
        headers = {}
        image_url = image
        local_image_path = SmartBodyCrop.tmp_path + 'image'
        if type(image) is dict:
            headers = image.get('headers')
            image_url = image.get('uri')
        # check if the image is a local file path
        if type(image) is str:
            if not image.startswith('http'):
                return image

        http = urllib3.PoolManager(
            cert_reqs='CERT_REQUIRED',
            ca_certs=certifi.where(),
            headers=headers)
        urllib3.disable_warnings()

        r = http.request('GET', image_url,
                         preload_content=False,
                         retries=urllib3.Retry(5, redirect=5))

        with open(local_image_path, 'wb') as out:
            while True:
                data = r.read(1024)  # 8192
                if not data:
                    break
                out.write(data)

        r.release_conn()
        print_time("image downloaded in :", start)
        return local_image_path

    def load_graph_def(self):
        start = time.time()

        local_model_path = self._download_model()

        tf.reset_default_graph()
        graph_def = graph_pb2.GraphDef()
        with open(local_model_path, 'rb') as f:
            graph_def.ParseFromString(f.read())
        tf.import_graph_def(graph_def, name='')

        start = print_time("model imported in :", start)
        start = time.time()

        # SmartBodyCrop.initialized = True

    def infer(self, image, upper_body, lower_body):
        start = time.time()

        imgpath = self._download_image(image)
        image, thumbnail, input_width, input_height = self.read_img(
            imgpath, 368, 368)
        start = print_time("image (" + str(input_width) +
                           "x" + str(input_height) + ") loaded in: ", start)

        if not SmartBodyCrop.initialized:
            print("Loading the model...")
            self.load_graph_def()

        with tf.Session() as sess:
            inputs = tf.get_default_graph().get_tensor_by_name('inputs:0')
            heatmaps_tensor = tf.get_default_graph().get_tensor_by_name(
                'Mconv7_stage6_L2/BiasAdd:0')
            pafs_tensor = tf.get_default_graph().get_tensor_by_name(
                'Mconv7_stage6_L1/BiasAdd:0')

            heatMat, pafMat = sess.run(
                [heatmaps_tensor, pafs_tensor], feed_dict={inputs: image})

            start = print_time("tf session executed in: ", start)

            humans = estimate_pose(heatMat[0], pafMat[0])
            start = print_time("pose estimated in: ", start)
            # send the thumbnail to render an initial crop
            img, crop_position, crop_size = crop_image(
                thumbnail, humans, upper_body, lower_body)
            # scale back the crop_coordinates to match the original picture size
            scale_factor_w = input_width / thumbnail.size[0]
            scale_factor_h = input_height / thumbnail.size[1]
            crop_coordinates = {
                'x':      crop_position[0] * scale_factor_w,
                'y':      crop_position[1] * scale_factor_h,
                'width':  crop_size[0] * scale_factor_w,
                'height': crop_size[1] * scale_factor_h
            }

            start = print_time("image cropped in: ", start)

            sess.close()
            return img, crop_coordinates, imgpath

    def detect_parts(self, image):
        start = time.time()

        imgpath = self._download_image(image)
        image, thumbnail, input_width, input_height = self.read_img(
            imgpath, 368, 368)
        start = print_time("image loaded in: ", start)

        if not SmartBodyCrop.initialized:
            print("Loading the model...")
            self.load_graph_def()

        with tf.Session() as sess:
            inputs = tf.get_default_graph().get_tensor_by_name('inputs:0')
            heatmaps_tensor = tf.get_default_graph().get_tensor_by_name(
                'Mconv7_stage6_L2/BiasAdd:0')
            pafs_tensor = tf.get_default_graph().get_tensor_by_name(
                'Mconv7_stage6_L1/BiasAdd:0')

            heatMat, pafMat = sess.run(
                [heatmaps_tensor, pafs_tensor], feed_dict={inputs: image})

            start = print_time("tf session executed in: ", start)

            humans = estimate_pose(heatMat[0], pafMat[0])
            start = print_time("pose estimated in: ", start)

            # display
            img1 = draw_humans(thumbnail, humans)
            return img1
