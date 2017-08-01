import os
import io_tool as it


if __name__ == '__main__':
    feat_type = 'dense_optical_flow.16000_512.fill_2.16_frames_per_seg.5_flows_per_frame.h256_w256'

    time_range = (30, 60)

    base_dir = '/home/ciaua/NAS/home/data/youtube8m/'
    fold_dir = os.path.join(base_dir, 'fold.tr16804_va2100_te2100')

    audio_feat_type = 'binary_temporal_instrument.16000_2048.20170312_112549'
    anno_dir = os.path.join(
        base_dir, 'feature', 'audio.time_{}_to_{}'.format(*time_range),
        audio_feat_type
    )

    out_dir = os.path.join(base_dir, 'valid_audioanno_feats.video.optical_flow')
    if not os.path.exists(out_dir):
        os.mkdir(out_dir)

    # Audio
    feat_dir = os.path.join(
        base_dir, 'feature', 'video.time_{}_to_{}'.format(*time_range),
        feat_type
    )

    args_list = list()
    for phase in ['tr', 'va', 'te']:
        # anno_dir = anno_dir_dict[phase]
        fold_fp = os.path.join(fold_dir, 'fold.{}.txt'.format(phase))
        id_list = it.read_lines(fold_fp)

        # Output
        out_fp_fn = 'fp_list.{}.csv'.format(phase)
        out_fp_fp = os.path.join(out_dir, out_fp_fn)

        out_fp_list = list()
        out_ids_list = list()
        for _id in id_list:
            anno_fp = os.path.join(anno_dir, '{}.npy'.format(_id))

            feat_fp = os.path.join(feat_dir, '{}.npy'.format(_id))

            exist_list = map(os.path.exists, [anno_fp, feat_fp])
            all_good = all(exist_list)

            if all_good:
                # print('Valid: {}'.format(sn))
                out_fp_list.append([anno_fp, feat_fp])
            else:
                print('Invalid: {}'.format(_id))
        it.write_csv(out_fp_fp, out_fp_list)