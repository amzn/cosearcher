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
import json
import collections
import pathlib
import csv

import clarify_types


class Qulac:
    def __init__(self, file_obj: tp.TextIO):
        j = json.load(file_obj)
        l = list(j["answer"].keys())
        topics = collections.defaultdict(
            lambda: {}
        )  # type: tp.Dict[str, tp.Dict[str, tp.List[tp.Tuple[str, str]]]]
        topics_desc = {}
        topics_ids = {}
        facets_ids = collections.defaultdict(
            lambda: {}
        )  # type: tp.Dict[str, tp.Dict[str, tp.List[tp.Tuple[str, str]]]]
        for k in l:
            topic = j["topic"][k]
            topics_desc[topic] = j["topic_desc"][k]
            facet = j["facet_desc"][k]
            if facet not in topics[topic]:
                topics[topic][facet] = []
            topics[topic][facet].append((j["question"][k], j["answer"][k]))
            topics_ids[topic] = j["topic_id"][k]
            facets_ids[topic][facet] = j["facet_id"][k]

        self.topics = []  # type: tp.List[clarify_types.Topic]
        self.topic_query2obj = {}  # type: tp.Dict[str,clarify_types.Topic]
        for topic_desc, v in topics.items():
            facets = []  # type: tp.List[clarify_types.Facet]
            for facet_desc, questions in v.items():
                questions_answers = []  # type: tp.List[tp.Tuple[str, str]]
                for i, t in enumerate(sorted(questions, key=lambda x: x[0])):
                    q, a = t
                    if not q:
                        continue
                    questions_answers.append((q, a))
                facet = clarify_types.Facet(
                    facets_ids[topic_desc][facet_desc], facet_desc, questions_answers
                )
                facets.append(facet)
            topic = clarify_types.Topic(topics_ids[topic_desc], topic_desc, facets)
            self.topics.append(topic)
            self.topic_query2obj[topic.query] = topic

    def get_topic_by_query(self, query: str) -> clarify_types.Topic:
        return self.topic_query2obj[query]

    def get_topic_by_id(self, id: str) -> clarify_types.Topic:
        return [topic for topic in self.topics if topic.id == int(id)][0]


if __name__ == "__main__":
    import scipy.special

    d = Qulac(open("data/qulac.json"))
    cnt = 0
    H = 3
    for topic in d.topics:
        for facet in topic.facets:
            print("topic:", topic.query)
            print("facet:", facet.desc)
            for q, a in facet.questions_answers:
                print("q:", q)
                print("a:", a)
            Q = len(set([x[0] for x in facet.questions_answers]))
            # Q = len(facet.questions_answers)
            print("Q=", Q)
            print("#facets", len(topic.facets))
            for h in range(1, min(Q, H) + 1):  # for Q=4 H=3, -> h = 1, 2, 3
                cnt += scipy.special.comb(Q, H)
    print("topics=", len(d.topics), "facets=", sum(len(t.facets) for t in d.topics))
    print("total number of converations=", cnt)
