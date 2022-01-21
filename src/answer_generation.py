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
import random
import typing as tp
from abc import ABC, abstractmethod

import clarify_types
from yes_no_detection import YesNoDetector


class AnswerGenerator(ABC):
    @abstractmethod
    def generate_answer(
        self,
        topic: clarify_types.Topic,
        facet: clarify_types.Facet,
        cooperativeness: float,
        similarity: float,
    ) -> str:
        pass


class QulacAnswerGenerator(AnswerGenerator):
    def __init__(
        self,
        yes_no_detector: YesNoDetector,
        perfect_match_threshold: float,
        yes_answer: str = "yes",
        no_answer: str = "no",
    ):
        self.yes_no_detector = yes_no_detector
        self.perfect_match_threshold = perfect_match_threshold
        self.yes_answer = yes_answer
        self.no_answer = no_answer

    def generate_answer(
        self,
        topic: clarify_types.Topic,
        facet: clarify_types.Facet,
        cooperativeness: float,
        similarity: float,
    ) -> str:
        answers = self.parse_answers(facet)
        if similarity >= self.perfect_match_threshold:
            if answers["yes"]:
                return random.choice(answers["yes"])
            else:
                return self.yes_answer
        elif random.random() < cooperativeness and answers["no"]:
            return random.choice(answers["no"])
        return self.no_answer

    def parse_answers(self, facet: clarify_types.Facet) -> tp.Dict[str, tp.List[str]]:
        answers = defaultdict(list)
        for q, a in facet.questions_answers:
            answers[self.yes_no_detector.stance(a)].append(a)
        return answers
