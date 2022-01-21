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

import typing as tp
import numpy as np
import random
import argparse
import pathlib
import json
import csv

import utils
import qulac
import clarify_types
import yes_no_detection


def get_data(topics: tp.List[clarify_types.Topic], enhanced=False):
    data = []
    yes_no_detector = yes_no_detection.DummyYesNoDetector()
    for topic in topics:
        for facet in topic.facets:
            for q, a in facet.questions_answers:
                answer = utils.strip_punctuation(a)
                stance = yes_no_detector.stance(answer)
                if stance == "yes":
                    label = 1
                elif stance == "no":
                    label = 0
                else:
                    continue
                rep = topic.query + " . " + facet.desc
                if enhanced:
                    rep += "\n" + facet.enhanced_rep
                if label is not None:
                    data.append(
                        {
                            "topic_facet_id": "%d-%d" % (topic.id, facet.id),
                            "topic": topic.query,
                            "provider_facet": facet.desc,
                            "facet": rep,
                            "q": q,
                            "a": a,
                            "label": label,
                        }
                    )
    random.shuffle(data)
    return data


if __name__ == "__main__":
    random.seed(42)
    np.random.seed(42)
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=str, default="data/qulac.json")
    parser.add_argument("--save", type=pathlib.Path, default="data/yesno_tsv_paper")
    parser.add_argument("--enhanced", action="store_true")
    args = parser.parse_args()
    print(args)
    dataset = qulac.Qulac(open(args.dataset))
    topics = dataset.topics
    random.shuffle(topics)
    n = len(topics)
    train_size = 100
    valid_size = 25
    test_size = n - train_size - valid_size
    print("train_data", train_size, "valid_data", valid_size, "test_size", test_size)
    train_topics, valid_topics, test_topics = (
        topics[:train_size],
        topics[train_size : train_size + valid_size],
        topics[-test_size:],
    )
    train_data = get_data(train_topics, enhanced=args.enhanced)
    valid_data = get_data(valid_topics, enhanced=args.enhanced)
    test_data = get_data(test_topics, enhanced=args.enhanced)
    files = zip(
        ["train.tsv", "valid.tsv", "test.tsv"], [train_data, valid_data, test_data]
    )
    args.save.mkdir(exist_ok=True, parents=True)
    for filename, data in files:
        f = (args.save / filename).open("w")
        w = csv.DictWriter(f, data[0].keys(), delimiter="\t")
        w.writeheader()
        w.writerows(data)
    files = zip(
        ["data/qulac.train.json", "data/qulac.valid.json", "data/qulac.test.json"],
        [train_topics, valid_topics, test_topics],
    )
    for filename, data in files:
        d = {
            "topic": {},
            "topic_desc": {},
            "answer": {},
            "facet_desc": {},
            "question": {},
            "facet_id": {},
            "topic_id": {},
        }
        i = 0
        for topic in data:
            for facet in topic.facets:
                for q, a in facet.questions_answers:
                    d["topic"][i] = topic.query
                    d["topic_id"][i] = topic.id
                    d["facet_id"][i] = facet.id
                    d["facet_desc"][i] = facet.desc
                    d["topic_desc"][i] = topic.query
                    d["question"][i] = q
                    d["answer"][i] = a
                    i += 1
        with open(filename, "w") as f:
            json.dump(d, f)
