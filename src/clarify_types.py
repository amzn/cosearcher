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


class Facet:
    def __init__(
        self, id: str, desc: str, questions_answers: tp.List[tp.Tuple[str, str]]
    ):
        self.id = id
        self.desc = desc
        self.questions_answers = questions_answers
        self._enhanced_rep = ""

    @property
    def enhanced_rep(self):
        return " ".join(self._enhanced_rep.replace("...", ". ").split(" ")[:512])

    @enhanced_rep.setter
    def enhanced_rep(self, value):
        self._enhanced_rep = value

    def __repr__(self):
        return self.desc

    def to_json(self):
        return {"id": self.id, "desc": self.desc, "_enhanced_rep": self._enhanced_rep}


class Topic:
    def __init__(self, id: str, query: str, facets: tp.List[Facet]):
        self.id = id
        self.query = query
        self.facets = facets

    def __repr__(self):
        return self.query

    def to_json(self):
        return {
            "id": self.id,
            "query": self.query,
            "facets": [facet.to_json() for facet in self.facets],
        }


class ClarifyState:
    ONGOING_STATE = 0
    SUCCESS_STATE = 1
    FAILED_STATE = 2

    def __init__(
        self,
        topic: Topic,
        candidate_facets_db: tp.List[tp.Tuple[Facet, float]],
        max_turns: int = 0,
    ):
        self.topic = topic
        self.candidate_facets_db = candidate_facets_db
        self.informative_no_db: tp.List[str] = []
        self.dead_facets_db = []  # type: tp.List[tp.Tuple[Facet, float]]
        self.state = self.ONGOING_STATE  # type: int
        self.max_turns = max_turns
        self.turns_left = max_turns
