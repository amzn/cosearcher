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
    def __init__(self, matcher: match.SentenceMatcher, alpha: float = 1.0):
        self.matcher = matcher
        assert 0 <= alpha <= 1
        self.alpha = alpha

    def rank_facets(
        self, state: clarify_types.ClarifyState
    ) -> tp.List[tp.Tuple[clarify_types.Facet, float]]:
        # positive context
        c_p = set(state.informative_no_db)
        # negative context
        c_n = set(facet.full_rep for facet, _ in state.dead_facets_db)
        scores = []
        for facet, _ in state.candidate_facets_db:
            if len(c_p) > 0 and self.alpha > 0:
                pos_score = np.mean(
                    [self.matcher.similarity(facet.full_rep, c) for c in c_p]
                )
            else:
                pos_score = 0
            if len(c_n) > 0 and self.alpha < 1:
                neg_score = np.mean(
                    [-self.matcher.similarity(facet.full_rep, c) for c in c_n]
                )
            else:
                neg_score = 0
            score = (1 - self.alpha) * neg_score + self.alpha * pos_score
            scores.append((facet, score))
        scores = sorted(scores, key=lambda x: x[1], reverse=True)
        return scores
