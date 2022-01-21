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

import argparse
from sklearn.model_selection import cross_val_score
import pathlib
import csv
import numpy as np

import match

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True, type=pathlib.Path)
    parser.add_argument("--data", required=True, type=pathlib.Path)
    parser.add_argument("--save", required=True, type=pathlib.Path)
    args = parser.parse_args()
    matcher = match.TransformerSentenceMatcher(args.model)
    r = csv.DictReader(args.data.open(), delimiter="\t")
    w = csv.DictWriter(
        args.save.open("w"),
        fieldnames=[
            "topic_facet_id",
            "provider_facet",
            "facet",
            "q",
            "prediction",
            "label",
        ],
        delimiter="\t",
        extrasaction="ignore",
    )
    w.writeheader()
    for data in r:
        data["prediction"] = matcher.similarity(data["facet"], data["q"])
        w.writerow(data)
