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
import math
import scipy.stats
import numpy as np
import pathlib
import random
from abc import ABC, abstractmethod


import clarify_types
import match


class FacetRanker(ABC):
    @abstractmethod
    def rank_facets(
        self, state: clarify_types.ClarifyState
    ) -> tp.List[tp.Tuple[clarify_types.Facet, float]]:
        pass


class RandomFacetRanker(FacetRanker):
    def rank_facets(
        self, state: clarify_types.ClarifyState
    ) -> tp.List[tp.Tuple[clarify_types.Facet, float]]:
        return sorted(
            [(facet, random.random()) for facet, _ in state.candidate_facets_db],
            key=lambda x: x[1],
            reverse=True,
        )


class SimilarityFacetRanker(FacetRanker):
    def __init__(self, matcher: match.SentenceMatcher):
        self.matcher = matcher

    def rank_facets(
        self, state: clarify_types.ClarifyState
    ) -> tp.List[tp.Tuple[clarify_types.Facet, float]]:
        # positive context
        if len(state.informative_no_db) == 0:
            return state.candidate_facets_db
        scores = []
        for facet, _ in state.candidate_facets_db:
            score = sum(
                [
                    self.matcher.similarity(facet.desc + "\n" + facet.enhanced_rep, s2)
                    for s2 in state.informative_no_db
                ]
            )
            scores.append((facet, score))
        scores = sorted(scores, key=lambda x: x[1], reverse=True)
        return scores
