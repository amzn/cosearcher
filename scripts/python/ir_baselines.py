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

from collections import defaultdict
import typing as tp
import numpy as np
import random
import argparse
import pathlib
import json
import csv
import tqdm

import utils
import qulac
import clarify_types
import ir
import thirdparty.ql as ql

if __name__ == "__main__":
    random.seed(42)
    np.random.seed(42)
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=str, default="data/qulac.test.json")
    args = parser.parse_args()
    dataset = qulac.Qulac(open(args.dataset))
    ir_metric_calculator = ir.TrecToolsMetricCalculator("data/faceted.qrel")
    ir_system = ir.QLInformationRetriever(ql.QL.QL(True, True, "data/ql/"))
    # topic-only is equivalent to no intent refinement (use only user's initial query)
    # facet is an upper bound where the correct intent is always identified
    for name, query in (
        ("topic-only", lambda topic, facet: topic.query),
        ("facet", lambda topic, facet: facet.desc),
    ):
        metrics = defaultdict(list)
        for topic in tqdm.tqdm(dataset.topics):
            for facet in topic.facets:
                for metric, value in ir_metric_calculator.calculate_metrics(
                    ir_system, topic, facet, query(topic, facet)
                ).items():
                    metrics[metric].append(value)
        total = utils.compute_metrics(metrics)
        print(name)
        for i, v in total.items():
            print(i, v["mean"])
        print("=" * 10)
