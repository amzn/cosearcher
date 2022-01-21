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
import random
import tqdm

import clarify_types
import facet_retrieval
import facet_ranking
import question_generation
import user_simulator
import informative_no_extraction
import yes_no_detection
import ir
import utils


class Clarify:
    def __init__(
        self,
        question_generator: question_generation.QuestionGenerator,
        user_simulator: user_simulator.UserSimulator,
        yes_no_detector: yes_no_detection.YesNoDetector,
        informative_no_extractor: informative_no_extraction.InformativeNoExtractor,
        facet_ranker: facet_ranking.FacetRanker,
        facet_retriever: facet_retrieval.FacetRetriever,
        ir_system: ir.InformationRetriever,
        ir_metric_calculator: ir.MetricCalculator,
        cooperativeness_fn: tp.Callable[[int], float],
    ):
        self.user_simulator = user_simulator
        self.question_generator = question_generator
        self.user_simulator = user_simulator
        self.yes_no_detector = yes_no_detector
        self.informative_no_extractor = informative_no_extractor
        self.facet_ranker = facet_ranker
        self.facet_retriever = facet_retriever
        self.ir_system = ir_system
        self.cooperativeness_fn = cooperativeness_fn
        self.ir_metric_calculator = ir_metric_calculator

    def build_state(self, topic: clarify_types.Topic):
        facets = self.facet_retriever.facets_for_topic(topic)
        state = clarify_types.ClarifyState(topic, facets)
        state.candidate_facets_db = self.rank_facets(state)
        if len(state.candidate_facets_db) == 0:
            # facet retriever failed to find any facets for this topic
            state.state = clarify_types.ClarifyState.FAILED_STATE
        return state

    def rank_facets(self, state):
        facets = self.facet_ranker.rank_facets(state)
        facets = sorted(facets, key=lambda x: (x[1], random.random()), reverse=True)
        return facets

    def step(
        self,
        state: clarify_types.ClarifyState,
        user_simulator_state: user_simulator.UserSimulatorState,
    ) -> tp.Tuple[int, str, str, float, float]:
        assert state.state == clarify_types.ClarifyState.ONGOING_STATE
        guessed_facet, clarify_score = state.candidate_facets_db.pop(0)
        state.dead_facets_db.append((guessed_facet, clarify_score))
        question = self.question_generator.generate_question(state.topic, guessed_facet)
        user_feedback = self.user_simulator.feedback(user_simulator_state, question)
        answer = user_feedback["answer"]
        user_simulator_state = user_feedback["state"]
        user_score = user_feedback["similarity"]
        if self.yes_no_detector.stance(answer) == "yes":
            state.state = clarify_types.ClarifyState.SUCCESS_STATE
            clarify_score = 1
        else:
            informative_no = self.informative_no_extractor.extract(answer)
            if informative_no:
                state.informative_no_db.append(informative_no)
            state.candidate_facets_db = self.rank_facets(state)
            if (
                len(state.candidate_facets_db) == 0
                or user_simulator_state.ran_out_of_patience()
            ):
                state.state = clarify_types.ClarifyState.FAILED_STATE
        return {
            "state": state,
            "question": question,
            "answer": answer,
            "user_score": user_score,
            "clarify_score": clarify_score,
            "guessed_facet": guessed_facet,
        }

    def run(self, epochs: int, topics: clarify_types.Topic):
        json_out = {}
        json_out["topics"] = []
        global_metrics = defaultdict(list)
        for topic in tqdm.tqdm(topics):
            topic_out = {}
            json_out["topics"].append(topic_out)
            topic_out["topic"] = topic
            topic_out["facets"] = []
            for facet in topic.facets:
                facet_out = {}
                topic_out["facets"].append(facet_out)
                facet_out["facet_id"] = facet.id
                facet_out["dialogues"] = []
                facet_metrics = defaultdict(list)
                for _ in range(epochs):
                    dialogue_out = self.run_dialogue(topic, facet)
                    facet_metrics["turns"].append(len(dialogue_out["turns"]))
                    facet_metrics["subj_success"].append(dialogue_out["subj_success"])
                    facet_metrics["real_success"].append(dialogue_out["real_success"])
                    for metric, value in dialogue_out["metrics"].items():
                        facet_metrics[metric].append(value)
                    facet_out["dialogues"].append(dialogue_out)
                facet_out["metrics"] = utils.compute_metrics(facet_metrics)
                for metric, value in facet_out["metrics"].items():
                    global_metrics[metric].append(value["mean"])
        json_out["metrics"] = utils.compute_metrics(global_metrics)
        return json_out

    def run_dialogue(self, topic: clarify_types.Topic, facet: clarify_types.Facet):
        dialogue_out = {}
        dialogue_out["turns"] = []
        state = self.build_state(topic)
        dialogue_out["initial_candidate_facets_db"] = state.candidate_facets_db[:]
        user_sim_state = self.user_simulator.build_state(topic, facet)
        while state.state == clarify_types.ClarifyState.ONGOING_STATE:
            step_result = self.step(state, user_sim_state)
            state = step_result["state"]
            dialogue_out["turns"].append(
                {
                    "question": step_result["question"],
                    "answer": step_result["answer"],
                    "user_p": step_result["user_score"],
                    "guessed_facet_id": step_result["guessed_facet"].id,
                    "candidate_facets_db": [
                        (facet.id, score) for facet, score in state.candidate_facets_db
                    ],
                    "informative_no_db": state.informative_no_db[:],
                    "state": state.state,
                }
            )
        dialogue_out["subj_success"] = False
        dialogue_out["real_success"] = False
        if state.state == clarify_types.ClarifyState.SUCCESS_STATE:
            dialogue_out["subj_success"] = True
            guessed_facet_id = dialogue_out["turns"][-1]["guessed_facet_id"]
            if guessed_facet_id == facet.id:
                dialogue_out["real_success"] = True
            dialogue_out["query"] = [
                a_facet.desc
                for a_facet, _ in dialogue_out["initial_candidate_facets_db"]
                if a_facet.id == guessed_facet_id
            ][0]
        else:
            dialogue_out["query"] = topic.query
        dialogue_out["metrics"] = self.ir_metric_calculator.calculate_metrics(
            self.ir_system, topic, facet, dialogue_out["query"]
        )
        return dialogue_out
