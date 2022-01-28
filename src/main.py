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
import numpy as np
import pathlib
import random
import json
import sys

import clarify
import qulac
import facet_retrieval
import facet_ranking
import question_generation
import answer_generation
import user_simulator
import informative_no_extraction
import yes_no_detection
import match
import ir
import thirdparty.ql as ql

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--qrel", default="data/faceted.qrel")
    parser.add_argument("--dataset", type=pathlib.Path, default="data/qulac.test.json")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--epochs", type=int, default=10)

    # facet provider
    parser.add_argument(
        "--facet", type=str, default="qulac", choices=["qulac", "bing", "graph-bing"]
    )
    parser.add_argument("--bing-key", type=str)
    parser.add_argument("--bing-endpoint", type=str, default="api.bing.microsoft.com")
    parser.add_argument("--bing-sleep", type=float, default=3)
    parser.add_argument(
        "--bing-cache", type=pathlib.Path, default="data/bing_cache.json"
    )

    # facet ranking
    parser.add_argument(
        "--facet-ranker",
        type=str,
        default="similarity",
        choices=["random", "similarity"],
    )
    parser.add_argument("--facet-ranker-alpha", type=float, default=1.0)
    parser.add_argument("--enhanced-rep", action="store_true")
    parser.add_argument(
        "--enhanced-rep-path", type=pathlib.Path, default="data/enhanced_reps_qulac.tsv"
    )
    parser.add_argument(
        "--matcher-clarify", type=str, default="bov", choices=match.MATCHERS.keys()
    )
    parser.add_argument(
        "--matcher-path-clarify",
        type=pathlib.Path,
        default="data/embeddings/lexvec.commoncrawl.ngramsubwords.300d.W.pos.bin",
    )

    # cosearcher
    parser.add_argument(
        "--matcher-user", type=str, default="transformer", choices=match.MATCHERS.keys()
    )
    parser.add_argument(
        "--matcher-path-user",
        type=pathlib.Path,
        default="data/yesno_tsv_paper_qulac/transformer",
    )
    parser.add_argument(
        "--cooperativeness-fn",
        type=str,
        default="constant",
        choices=["constant", "inc", "dec"],
    )
    parser.add_argument("--threshold-user", type=float, default=0.5)
    parser.add_argument("--patience", type=int, default=3)
    parser.add_argument("--cooperativeness", type=float, default=1)
    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)
        np.random.seed(args.seed)

    dataset = qulac.Qulac(args.dataset.open())

    matcher = {}
    for which in ["user", "clarify"]:
        which_matcher = vars(args)["matcher_%s" % which]
        which_matcher_path = vars(args)["matcher_path_%s" % which]
        this_matcher = match.MATCHERS[which_matcher](which_matcher_path)
        matcher[which] = match.CachingSentenceMatcher(this_matcher)

    # user simulator
    cooperativeness_fn = user_simulator.cooperativeness_fn(
        args.cooperativeness_fn, args.cooperativeness
    )
    yes_no_detector = yes_no_detection.DummyYesNoDetector()
    answer_generator = answer_generation.QulacAnswerGenerator(
        yes_no_detector, perfect_match_threshold=args.threshold_user
    )
    user_sim = user_simulator.UserSimulator(
        matcher=matcher["user"],
        patience=args.patience,
        cooperativeness=args.cooperativeness,
        cooperativeness_fn=cooperativeness_fn,
        yes_no_detector=yes_no_detector,
        answer_generator=answer_generator,
    )

    # agent
    question_generator = question_generation.DummyQuestionGenerator()
    informative_no_extractor = informative_no_extraction.DummyInformativeNoExtractor()
    if args.facet_ranker == "similarity":
        facet_ranker = facet_ranking.SimilarityFacetRanker(
            matcher["clarify"], alpha=args.facet_ranker_alpha
        )
    elif args.facet_ranker == "random":
        facet_ranker = facet_ranking.RandomFacetRanker()
    else:
        raise Exception("invalid ranker")

    facet_retriever = {
        "qulac": lambda: facet_retrieval.QulacFacetRetriever(dataset),
        "bing": lambda: facet_retrieval.BingFacetRetriever(
            args.bing_key,
            args.bing_cache,
            max_depth=1,
            chars=[],
            bing_sleep=args.bing_sleep,
            endpoint=args.bing_endpoint,
        ),
        "graph-bing": lambda: facet_retrieval.BingFacetRetriever(
            args.bing_key,
            args.bing_cache,
            max_depth=1,
            bing_sleep=args.bing_sleep,
            endpoint=args.bing_endpoint,
        ),
    }[args.facet]()
    if args.enhanced_rep:
        facet_retriever = facet_retrieval.EnhancedFacetsFacetRetriever(
            args.enhanced_rep_path, facet_retriever
        )

    ir_system = ir.QLInformationRetriever(ql.QL.QL(True, True, "data/ql/"))
    ir_metric_calculator = ir.TrecToolsMetricCalculator(args.qrel)

    clarif = clarify.Clarify(
        question_generator=question_generator,
        user_simulator=user_sim,
        yes_no_detector=yes_no_detector,
        informative_no_extractor=informative_no_extractor,
        facet_ranker=facet_ranker,
        facet_retriever=facet_retriever,
        ir_system=ir_system,
        ir_metric_calculator=ir_metric_calculator,
        cooperativeness_fn=cooperativeness_fn,
    )

    json_out = clarif.run(args.epochs, dataset.topics)

    def dumper(obj):
        try:
            return obj.to_json()
        except AttributeError:
            return str(obj)

    json_out["args"] = vars(args)
    json.dump(json_out, sys.stdout, default=dumper, indent=4)
