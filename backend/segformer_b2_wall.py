# SegFormer-B2 Wall Segmentation Config
# 2 classes: 0=background, 1=wall
#
# 使用前需要先执行以下步骤:
#
# 1. 重命名 mask 文件，使文件名与图像一致:
#    python rename_masks.py
#
# 2. 生成 list 文件:
#    python gen_lists.py
#
# 目录结构:
#   data/cubicasa5k/high_quality_architectural/22/F1_original.png  (图像)
#   wall_masks/train/high_quality_architectural/22/F1_original.png  (mask)
#   seg_lists/train_list.txt  (每行: high_quality_architectural/22)

norm_cfg = dict(type='BN', requires_grad=True)

data_preprocessor = dict(
    type='SegDataPreProcessor',
    mean=[123.675, 116.28, 103.53],
    std=[58.395, 57.12, 57.375],
    bgr_to_rgb=True,
    pad_val=0,
    seg_pad_val=255,
    size=(512, 512))

model = dict(
    type='EncoderDecoder',
    data_preprocessor=data_preprocessor,
    backbone=dict(
        type='MixVisionTransformer',
        in_channels=3,
        embed_dims=64,
        num_stages=4,
        num_layers=[3, 4, 6, 3],
        num_heads=[1, 2, 5, 8],
        patch_sizes=[7, 3, 3, 3],
        sr_ratios=[8, 4, 2, 1],
        out_indices=(0, 1, 2, 3),
        mlp_ratio=4,
        qkv_bias=True,
        drop_rate=0.0,
        attn_drop_rate=0.0,
        drop_path_rate=0.1,
        init_cfg=dict(
            type='Pretrained',
            checkpoint='https://download.openmmlab.com/mmsegmentation/v0.5/pretrain/segformer/mit_b2_20220624-66e8bf70.pth')),
    decode_head=dict(
        type='SegformerHead',
        in_channels=[64, 128, 320, 512],
        in_index=[0, 1, 2, 3],
        channels=256,
        dropout_ratio=0.1,
        num_classes=2,
        norm_cfg=norm_cfg,
        align_corners=False,
        ignore_index=255,
        loss_decode=[
            dict(
                type='CrossEntropyLoss',
                use_sigmoid=False,
                loss_weight=1.0),
            dict(
                type='DiceLoss',
                loss_weight=3.0,
                naive_dice=True)
        ]),
    train_cfg=dict(),
    test_cfg=dict(mode='whole'))

# ── Pipelines ────────────────────────────────────────────────────────────────
train_pipeline = [
    dict(type='LoadImageFromFile'),
    dict(type='LoadAnnotations', reduce_zero_label=False),
    dict(type='RandomResize', scale=(640, 640), ratio_range=(0.5, 2.0), keep_ratio=True),
    dict(type='Pad', size=(512, 512), pad_val=dict(img=0, seg=255)),
    dict(type='RandomCrop', crop_size=(512, 512), cat_max_ratio=0.75),
    dict(type='RandomFlip', prob=0.5),
    dict(type='PhotoMetricDistortion'),
    dict(type='PackSegInputs')
]

test_pipeline = [
    dict(type='LoadImageFromFile'),
    dict(type='Resize', scale=(512, 512), keep_ratio=True),
    dict(type='LoadAnnotations', reduce_zero_label=False),
    dict(type='PackSegInputs')
]

# ── Dataset ───────────────────────────────────────────────────────────────────
# BaseSegDataset 要求:
#   ann_file 每行只写子目录相对路径，例如: high_quality_architectural/22
#   data_prefix.img_path  + 行内容 + img_suffix  = 完整图像路径
#   data_prefix.seg_map_path + 行内容 + seg_map_suffix = 完整 mask 路径
#
# 示例:
#   img:  data/cubicasa5k / high_quality_architectural/22 / F1_original.png
#   mask: wall_masks/train / high_quality_architectural/22 / F1_original.png

dataset_meta = dict(
    classes=['background', 'wall'],
    palette=[[0, 0, 0], [255, 255, 255]])

train_dataloader = dict(
    batch_size=4,
    num_workers=4,
    persistent_workers=True,
    sampler=dict(type='InfiniteSampler', shuffle=True),
    dataset=dict(
        type='BaseSegDataset',
        data_prefix=dict(
            img_path='data/cubicasa5k',
            seg_map_path='wall_masks/train'),
        ann_file='seg_lists/train_list.txt',
        img_suffix='/F1_original.png',
        seg_map_suffix='/F1_original.png',
        metainfo=dataset_meta,
        reduce_zero_label=False,
        pipeline=train_pipeline))

val_dataloader = dict(
    batch_size=1,
    num_workers=4,
    persistent_workers=True,
    sampler=dict(type='DefaultSampler', shuffle=False),
    dataset=dict(
        type='BaseSegDataset',
        data_prefix=dict(
            img_path='data/cubicasa5k',
            seg_map_path='wall_masks/val'),
        ann_file='seg_lists/val_list.txt',
        img_suffix='/F1_original.png',
        seg_map_suffix='/F1_original.png',
        metainfo=dataset_meta,
        reduce_zero_label=False,
        pipeline=test_pipeline))

test_dataloader = val_dataloader

val_evaluator  = dict(type='IoUMetric', iou_metrics=['mIoU'])
test_evaluator = val_evaluator

# ── Optimizer ─────────────────────────────────────────────────────────────────
optim_wrapper = dict(
    type='OptimWrapper',
    optimizer=dict(type='AdamW', lr=6e-5, betas=(0.9, 0.999), weight_decay=0.01),
    paramwise_cfg=dict(
        custom_keys={
            'pos_block': dict(decay_mult=0.),
            'norm':      dict(decay_mult=0.),
            'head':      dict(lr_mult=10.)}))

param_scheduler = [
    dict(type='LinearLR', start_factor=1e-6, by_epoch=False, begin=0,    end=1500),
    dict(type='PolyLR',   power=1.0,         by_epoch=False, begin=1500, end=40000,
         eta_min=0.0)
]

# ── Training loop ──────────────────────────────────────────────────────────────
train_cfg = dict(type='IterBasedTrainLoop', max_iters=40000, val_interval=4000)
val_cfg   = dict(type='ValLoop')
test_cfg  = dict(type='TestLoop')

# ── Hooks ──────────────────────────────────────────────────────────────────────
default_hooks = dict(
    timer=dict(type='IterTimerHook'),
    logger=dict(type='LoggerHook', interval=50, log_metric_by_epoch=False),
    param_scheduler=dict(type='ParamSchedulerHook'),
    checkpoint=dict(type='CheckpointHook', by_epoch=False,
                    interval=4000, save_best='mIoU'),
    sampler_seed=dict(type='DistSamplerSeedHook'),
    visualization=dict(type='SegVisualizationHook'))

# ── Runtime ────────────────────────────────────────────────────────────────────
default_scope = 'mmseg'
log_level     = 'INFO'
log_processor = dict(by_epoch=False)
load_from     = None
resume        = False
randomness    = dict(seed=42)

env_cfg = dict(
    cudnn_benchmark=True,
    mp_cfg=dict(mp_start_method='fork', opencv_num_threads=0),
    dist_cfg=dict(backend='nccl'))

visualizer = dict(
    type='SegLocalVisualizer',
    vis_backends=[dict(type='LocalVisBackend')],
    name='visualizer')