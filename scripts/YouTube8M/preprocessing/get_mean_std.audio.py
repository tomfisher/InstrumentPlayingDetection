#!/usr/bin/env python

# from __future__ import print_function

import os
import numpy as np
import io_tool as it

from sklearn import preprocessing as pp


def fit(feat, scaler):
    scaler.partial_fit(feat)


if __name__ == '__main__':
    # Load the dataset
    print("Loading data...")
    feat_type = 'logmelspec10000.16000_2048_512_128.0.raw'

    time_range = (30, 60)

    # Base dirs
    base_dir = '/home/ciaua/NAS/home/data/youtube8m/'
    in_data_dir = os.path.join(
        base_dir,
        'exp_data.audio.time_{}_to_{}'.format(*time_range),
        feat_type
    )
    print(in_data_dir)

    # scaler output
    feat_tr_fp = os.path.join(in_data_dir, 'feat.tr.npy')

    scaler_fp = os.path.join(in_data_dir, 'scaler.pkl')

    mean_fp = os.path.join(in_data_dir, 'mean.csv')
    std_fp = os.path.join(in_data_dir, 'std.csv')

    # Make scaler
    scaler = pp.StandardScaler()

    # Fit
    print('Fit...')
    in_fp = feat_tr_fp
    feat = np.load(in_fp)
    k = feat.shape[-1]
    feat = feat.reshape((-1, k))
    fit(feat, scaler)

    it.pickle(scaler_fp, scaler)
    it.write_csv(mean_fp, [scaler.mean_.tolist()])
    it.write_csv(std_fp, [scaler.scale_.tolist()])
