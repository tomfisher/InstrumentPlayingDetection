import os
import numpy as np
import io_tool as it

if __name__ == '__main__':
    num_frames = 313
    clip_limit = 5000

    # Base dirs
    base_dir = '/home/ciaua/NAS/home/data/AudioSet/'

    # Data fold
    fold_dir = '/home/ciaua/NAS/home/data/AudioSet/song_list.instrument/'

    # Annotation
    base_anno_dir = os.path.join(base_dir, 'annotation.instrument')

    # Feature
    base_feat_dir = os.path.join(
        base_dir, 'feature', 'audio.target_time')
    feat_type = 'logmelspec10000.16000_2048_512_128.0.raw'
    # feat_type = 'logmelspec10000.16000_512_512_128.0.raw'
    # feat_type = 'logmelspec10000.16000_8192_512_128.0.raw'
    # feat_type = 'cqt.16000_512_A0_24_176.0.raw'

    in_feat_dir = os.path.join(base_feat_dir, feat_type)

    # Output dirs and fps
    out_dir = os.path.join(
        base_dir, 'exp_data.audio.target_time.cliplimit_{}'.format(clip_limit),
        feat_type)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    in_anno_dir_dict = {
        'tr': os.path.join(base_anno_dir, 'tr'),
        'va': os.path.join(base_anno_dir, 'va'),
    }
    fold_fn_dict = {
        'tr': os.path.join(
            fold_dir, 'unbalanced_train_segments.{}.csv'.format(clip_limit)),
        'va': os.path.join(fold_dir, 'eval_segments.all.csv'),
    }

    # main
    for phase in ['va', 'tr']:
        print(phase)
        fold_fp = fold_fn_dict[phase]
        fold = [term[0] for term in it.read_csv(fold_fp)]

        in_anno_dir = in_anno_dir_dict[phase]

        out_feat_fp = os.path.join(out_dir, 'feat.{}.npy'.format(phase))
        out_anno_fp = os.path.join(out_dir, 'target.{}.npy'.format(phase))
        out_fn_fp = os.path.join(out_dir, 'fn.{}.txt'.format(phase))

        out_anno_list = list()
        out_feat_list = list()
        out_fn_list = list()
        for fn in fold:
            in_feat_fp = os.path.join(in_feat_dir, '{}.npy'.format(fn))
            in_anno_fp = os.path.join(in_anno_dir, '{}.npy'.format(fn))

            try:
                in_anno = np.load(in_anno_fp)
                in_feat = np.load(in_feat_fp)
            except Exception as e:
                print('Fail loading data: {}. {}'.format(fn, repr(e)))
                continue

            if in_feat.shape[0] == num_frames:
                in_anno = in_anno[None, :].astype('float32')
                in_feat = in_feat[None, None, :].astype('float32')

                out_anno_list.append(in_anno)
                out_feat_list.append(in_feat)
                out_fn_list.append(fn)
                print('Done: {}'.format(fn))
            else:
                print('Incorrect frame number: {}. '.format(
                    in_feat.shape[0])
                )

        out_anno = np.concatenate(out_anno_list, axis=0).astype('float32')
        out_feat = np.concatenate(out_feat_list, axis=0).astype('float32')

        np.save(out_anno_fp, out_anno)
        np.save(out_feat_fp, out_feat)
        it.write_lines(out_fn_fp, out_fn_list)