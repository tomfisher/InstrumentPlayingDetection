#!/usr/bin/env python

import os
# import lasagne
from lasagne import layers
from jj import utils
# import jj.layers as cl
import io_tool as it
import numpy as np
import theano
import theano.tensor as T

from lasagne.layers import InputLayer
# from lasagne.layers import ReshapeLayer
from lasagne.layers import GlobalPoolLayer
# from lasagne.layers import DimshuffleLayer
# from lasagne.layers import DenseLayer
# from lasagne.layers import NonlinearityLayer
# from lasagne.layers import ExpressionLayer
# from lasagne.layers import ElemwiseMergeLayer
from lasagne.layers import DropoutLayer
from lasagne.layers import Conv2DLayer
from lasagne.layers import Pool2DLayer as PoolLayer
from lasagne.layers import LocalResponseNormalization2DLayer as NormLayer
# from lasagne.layers.dnn import Conv2DDNNLayer as ConvLayer
# from lasagne.nonlinearities import softmax, sigmoid, rectify
from lasagne.nonlinearities import sigmoid
# from lasagne.utils import floatX as to_floatX

import moviepy.editor as mpy
from moviepy.video import fx
# import cv2

ConvLayer = Conv2DLayer
floatX = theano.config.floatX


def make_structure_image(input_var, num_tags):
    mean_image = np.array([123.50936127, 115.7726059, 102.71698761])
    mean_image = mean_image.reshape((1, 3, 1, 1)).astype(floatX)

    net = {}
    input_var = input_var - mean_image  # RGB
    net['input'] = InputLayer((None, 3, None, None), input_var)
    net['conv1'] = ConvLayer(net['input'],
                             num_filters=96,
                             filter_size=7,
                             stride=2,
                             pad=3,
                             flip_filters=False)
    # caffe has alpha = alpha * pool_size
    net['norm1'] = NormLayer(net['conv1'], alpha=0.0001)
    net['pool1'] = PoolLayer(net['norm1'],
                             pool_size=3,
                             stride=2,
                             pad=(1, 1),
                             ignore_border=True)
    net['conv2'] = ConvLayer(net['pool1'],
                             num_filters=256,
                             filter_size=5,
                             stride=2,
                             pad=2,
                             flip_filters=False)
    net['pool2'] = PoolLayer(net['conv2'],
                             pool_size=3,
                             stride=2,
                             pad=(1, 1),
                             ignore_border=True)
    net['conv3'] = ConvLayer(net['pool2'],
                             num_filters=512,
                             filter_size=3,
                             pad=1,
                             flip_filters=False)
    net['conv4'] = ConvLayer(net['conv3'],
                             num_filters=512,
                             filter_size=3,
                             pad=1,
                             flip_filters=False)
    net['conv5'] = ConvLayer(net['conv4'],
                             num_filters=512,
                             filter_size=3,
                             pad=1,
                             flip_filters=False)
    net['pool5'] = PoolLayer(net['conv5'],
                             pool_size=3,
                             stride=2,
                             pad=(1, 1),
                             ignore_border=True)

    # Late conv
    net['conv6'] = ConvLayer(net['pool5'],
                             num_filters=2048,
                             filter_size=3,
                             pad=1)  # change to pad=1 when testing
    net['drop6'] = DropoutLayer(net['conv6'],
                                p=0.5)
    net['conv7'] = ConvLayer(net['drop6'],
                             num_filters=1024,
                             filter_size=1)
    net['drop7'] = DropoutLayer(net['conv7'],
                                p=0.5)
    net['conv8'] = ConvLayer(net['drop7'],
                             num_filters=num_tags,
                             filter_size=1,
                             nonlinearity=sigmoid)
    net['pooled_output'] = GlobalPoolLayer(net['conv8'],
                                           pool_function=T.max)

    return net


def make_structure_optical_flow(input_var, num_tags):

    net = {}
    net['input'] = InputLayer((None, 10, None, None), input_var)
    net['conv1'] = ConvLayer(net['input'],
                             num_filters=96,
                             filter_size=7,
                             stride=2,
                             pad=3,
                             flip_filters=False)
    # caffe has alpha = alpha * pool_size
    net['norm1'] = NormLayer(net['conv1'], alpha=0.0001)
    net['pool1'] = PoolLayer(net['norm1'],
                             pool_size=3,
                             stride=2,
                             pad=(1, 1),
                             ignore_border=True)
    net['conv2'] = ConvLayer(net['pool1'],
                             num_filters=256,
                             filter_size=5,
                             stride=2,
                             pad=2,
                             flip_filters=False)
    net['pool2'] = PoolLayer(net['conv2'],
                             pool_size=3,
                             stride=2,
                             pad=(1, 1),
                             ignore_border=True)
    net['conv3'] = ConvLayer(net['pool2'],
                             num_filters=512,
                             filter_size=3,
                             pad=1,
                             flip_filters=False)
    net['conv4'] = ConvLayer(net['conv3'],
                             num_filters=512,
                             filter_size=3,
                             pad=1,
                             flip_filters=False)
    net['conv5'] = ConvLayer(net['conv4'],
                             num_filters=512,
                             filter_size=3,
                             pad=1,
                             flip_filters=False)
    net['pool5'] = PoolLayer(net['conv5'],
                             pool_size=3,
                             stride=2,
                             pad=(1, 1),
                             ignore_border=True)

    # Late conv
    net['conv6'] = ConvLayer(net['pool5'],
                             num_filters=2048,
                             filter_size=3,
                             pad=1)  # change to pad=1 when testing
    net['drop6'] = DropoutLayer(net['conv6'],
                                p=0.5)
    net['conv7'] = ConvLayer(net['drop6'],
                             num_filters=1024,
                             filter_size=1)
    net['drop7'] = DropoutLayer(net['conv7'],
                                p=0.5)
    net['conv8'] = ConvLayer(net['drop7'],
                             num_filters=num_tags,
                             filter_size=1,
                             nonlinearity=sigmoid)
    net['pooled_output'] = GlobalPoolLayer(net['conv8'],
                                           pool_function=T.max)

    return net


def get_video_handler(video_fp, time_range=None):
    vid = mpy.VideoFileClip(video_fp)

    if time_range is not None:
        vid = vid.subclip(*time_range)

    return vid


def resize_and_pad(vid, target_size):
    # resize
    width, height = vid.size
    factor = min(target_size[0]/float(height), target_size[1]/float(width))
    new_height = round(height*factor)
    new_width = round(width*factor)

    vid = vid.resize(height=new_height, width=new_width)
    new_width, new_height = vid.size

    # pad
    pad_height, pad_width = target_size-(new_height, new_width)
    vid = fx.all.margin(vid, bottom=int(pad_height), right=int(pad_width))

    return vid


def extract_images(vid,
                   sr, hop, time_range,
                   num_frames_per_seg, target_size=None):

    # Resize and pad
    if target_size is not None:
        vid = resize_and_pad(vid, target_size)

    # Frames per second
    fps = sr/float(hop*num_frames_per_seg)

    # shape=(frames, height, width, RGB_channels)
    images = np.stack(vid.iter_frames(fps=fps))

    # shape=(frames, RGB_channels, height, width)
    images = np.transpose(images, [0, 3, 1, 2]).astype('uint8')
    return images


if __name__ == '__main__':
    time_range = (0, 60)
    fragment_unit = 5  # second
    num_fragments = (time_range[1]-time_range[0]) // fragment_unit

    phase = 'te'

    # Settings
    sr = 16000
    hop = 512
    num_tags = 9

    num_frames_per_seg = 16
    target_size = None  # (height, width)

    model_id_i = '20170319_085641'

    param_type = 'best_measure'
    # param_type = 'best_loss'

    # Dirs and fps
    base_dir = "/home/ciaua/NAS/home/data/youtube8m/"
    id_dir = os.path.join(base_dir, 'picked_id')
    video_dir = os.path.join(base_dir, 'video')
    id_dict_fp = os.path.join(id_dir, 'picked_id.{}.json'.format(phase))
    id_dict = it.read_json(id_dict_fp)

    id_list = list()
    for inst in id_dict:
        id_list += id_dict[inst]

    # Output
    base_out_dir = os.path.join(
        base_dir,
        'predictions_without_resize',
        'rgb_image.{}_{}.fragment_{}s'.format(
            time_range[0], time_range[1], fragment_unit),
        model_id_i, param_type)

    # Extract images
    # Tag
    # tag_fp = os.path.join(base_dir, 'tag_list.instrument.csv')
    # tag_list = [term[0] for term in it.read_csv(tag_fp)]

    # anno_dir = os.path.join(base_dir, )

    # fn_list = os.listdir(feat_dir)

    # Dirs and fps
    save_dir = os.path.join(base_dir, 'save.video')
    model_dir_i = os.path.join(save_dir, model_id_i)
    # model_dir_o = os.path.join(save_dir, model_id_o)

    # Model: Network structure
    print('Making network...')
    input_var_i = T.tensor4('visual_input.image')
    # input_var_o = T.tensor4('visual_input.optical_flow')

    net_dict_i = make_structure_image(input_var_i, num_tags)
    # net_dict_o = make_structure_optical_flow(input_var_o, num_tags)

    network_i = net_dict_i['conv8']
    # network_o = net_dict_o['conv8']

    # Load params
    param_fp_i = os.path.join(
        save_dir, model_id_i, 'model', 'params.{}.npz'.format(param_type))
    # param_fp_o = os.path.join(
    #     save_dir, model_id_o, 'model', 'params.{}.npz'.format(param_type))
    utils.load_model(param_fp_i, network_i)
    # utils.load_model(param_fp_o, network_o)

    # Merge two networks
    # merged_network = ElemwiseMergeLayer([network_i, network_o], T.mul)
    # network = GlobalPoolLayer(merged_network, pool_function=T.max)

    # Compute loss
    output_va_var_i = layers.get_output(network_i, deterministic=True)
    # output_va_var_o = layers.get_output(network_o, deterministic=True)

    # Make functions
    input_var_list = [input_var_i]
    func_pr = theano.function(input_var_list, output_va_var_i)

    for uu, song_id in enumerate(id_list):
        print(uu, song_id)
        # output fp
        out_dir = os.path.join(base_out_dir, song_id)
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)

        # Load video
        video_fp = os.path.join(video_dir, '{}.mp4'.format(song_id))
        vid = get_video_handler(video_fp, None)

        for ff in range(num_fragments):
            sub_time_range = (ff*fragment_unit, (ff+1)*fragment_unit)
            out_fp = os.path.join(out_dir,
                                  '{}_{}.npy'.format(*sub_time_range))
            if os.path.exists(out_fp):
                print('Done before')
                continue
            # Extract dense optical flow
            print('Extract images...')
            sub_vid = vid.subclip(*sub_time_range)
            images = extract_images(
                sub_vid, sr, hop, sub_time_range,
                num_frames_per_seg, target_size)

            # Predict
            print('Predict...')

            pred_list_i = list()
            for one_image in images:
                pred_one_i = func_pr(one_image[None, :])
                pred_list_i.append(pred_one_i)
            pred_i = np.concatenate(pred_list_i, axis=0)

            np.save(out_fp, pred_i)
