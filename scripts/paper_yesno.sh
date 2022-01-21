#!/bin/sh

#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License"). You may not use this file except in compliance
#  with the License. A copy of the License is located at
#
#  http://aws.amazon.com/apache2.0/
#
#  or in the "license" file accompanying this file. This file is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES
#  OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions
#  and limitations under the License.

set -xe

DEST=data/yesno_tsv_paper_qulac

mkdir -p $DEST

export PYTHONPATH="$PYTHONPATH:$(pwd)/src"

python3 scripts/python/create_yesno_tsv.py --save $DEST

python3 -m thirdparty.transformer.run_glue \
    --model_type bert \
    --model_name_or_path bert-base-uncased \
    --task_name qulac-bing \
    --do_train \
    --do_eval \
    --do_lower_case \
    --max_seq_length 128 \
    --per_gpu_eval_batch_size=8   \
    --per_gpu_train_batch_size=8   \
    --learning_rate 2e-5 \
    --num_train_epochs 3.0 \
    --save_steps 0 \
    --warmup_steps .1 \
    --overwrite_output_dir \
    --evaluate_during_training \
    --logging_steps 1000 \
    --task_name qulac-yesno --data_dir $DEST --output_dir $DEST/transformer --overwrite_cache

python3 scripts/python/create_yesno_predictions.py --model $DEST/transformer --data $DEST/valid.tsv --save $DEST/yesno_predictions_qulac.tsv

python3 scripts/python/find_optimal_bert_threshold.py --predictions $DEST/yesno_predictions_qulac.tsv

