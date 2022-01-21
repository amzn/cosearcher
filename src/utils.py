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

import re
import string
import numpy as np

regex = re.compile("[%s]" % re.escape(string.punctuation))


def strip_punctuation(s: str) -> str:
    return regex.sub(" ", s)


def remove_prefix(text: str, prefix: str) -> str:
    if text.startswith(prefix):
        return text[len(prefix) :]
    return text


def compute_metrics(metrics_per_run):
    metrics = {}
    for metric, values in metrics_per_run.items():
        metrics[metric] = {}
        for name, fn in [("mean", np.mean), ("median", np.median), ("std", np.std)]:
            metrics[metric][name] = fn(values)
    return metrics
