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

import qulac
import clarify_types
import match
from answer_generation import AnswerGenerator
from yes_no_detection import YesNoDetector


class UserSimulatorState:
    def __init__(
        self,
        topic: clarify_types.Topic,
        facet: clarify_types.Facet,
        patience: int,
        cooperativeness: float,
    ):
        self.topic = topic
        self.facet = facet
        assert self.facet in self.topic.facets, "facet must belong to topic"
        self.questions = []  # type: tp.List[str]
        self.answers = []  # type: tp.List[str]
        assert (
            0 <= cooperativeness and cooperativeness <= 1
        ), "cooperativeness must be in [0, 1]"
        self.turns = 0
        self.patience = patience
        self.cooperativeness = cooperativeness

    def add_question(self, question: str) -> "UserSimulatorState":
        assert len(self.questions) == len(
            self.answers
        ), "still waiting on an answer to a previous question"
        self.questions.append(question)
        return self

    def add_answer(self, answer: str) -> "UserSimulatorState":
        assert len(self.questions) - 1 == len(self.answers), "not waiting on an answer"
        self.answers.append(answer)
        return self

    def ran_out_of_patience(self):
        return self.turns == self.patience


class UserSimulator:
    def __init__(
        self,
        matcher: match.SentenceMatcher,
        patience: int,
        cooperativeness: float,
        cooperativeness_fn: tp.Callable[[int], float],
        yes_no_detector: YesNoDetector,
        answer_generator: AnswerGenerator,
    ):
        self.matcher = matcher
        self.patience = patience
        self.cooperativeness = cooperativeness
        self.cooperativeness_fn = cooperativeness_fn
        self.yes_no_detector = yes_no_detector
        self.answer_generator = answer_generator

    def feedback(
        self, state: UserSimulatorState, question: str
    ) -> tp.Tuple[str, float]:
        if state.ran_out_of_patience():
            answer = None
            similarity = 0.0
        else:
            state.cooperativeness = self.cooperativeness_fn(state.turns)
            state.turns += 1
            similarity = self.matcher.similarity(
                state.topic.query + " . " + state.facet.desc, question
            )
            answer = self.answer_generator.generate_answer(
                state.topic, state.facet, state.cooperativeness, similarity
            )
        state.add_question(question)
        state.add_answer(answer)
        return {
            "answer": answer,
            "state": state,
            "similarity": similarity,
        }

    def build_state(
        self, topic: clarify_types.Topic, facet: clarify_types.Facet
    ) -> UserSimulatorState:
        return UserSimulatorState(topic, facet, self.patience, self.cooperativeness)


def cooperativeness_fn(which, cooperativeness):
    return {
        "constant": lambda t: cooperativeness,
        "inc": lambda t: min(
            1, cooperativeness * np.log2(t + 2)
        ),  # t = 0 when answering first question, 1 when 2nd, etc
        "dec": lambda t: cooperativeness / np.log2(t + 2),
    }[which]
