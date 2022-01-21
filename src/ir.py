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

import pathlib
import tempfile
import typing as tp
import trectools
import os

import clarify_types
import thirdparty.ql.QL as QL
from abc import ABC, abstractmethod


class Document:
    def __init__(self, id: str, body: str):
        self.id = id
        self.body = body


class InformationRetriever(ABC):
    @abstractmethod
    def search(
        self, topic: clarify_types.Topic, query: str
    ) -> tp.List[tp.Tuple[Document, float]]:
        pass


class DummyInformationRetriever(InformationRetriever):
    def search(
        self, topic: clarify_types.Topic, query: str
    ) -> tp.List[tp.Tuple[Document, float]]:
        return []


class QLInformationRetriever(InformationRetriever):
    def __init__(self, ql_: QL.QL):
        self.ql = ql_

    def search(
        self, topic: clarify_types.Topic, query: str
    ) -> tp.List[tp.Tuple[Document, float]]:
        self.ql.load_topic_index(int(topic.id))
        self.ql.alpha = 0.5
        self.ql.update_query_lang_model(query=topic.query, question=query)
        df = self.ql.get_result_df(topk=1000, query_id="dummy")
        results = []
        for i, row in df.iterrows():
            results.append((Document(row[0], "dummy"), row[1]))
        return results


class MetricCalculator(ABC):
    @abstractmethod
    def calculate_metrics(
        self,
        ir_sys: InformationRetriever,
        topic: clarify_types.Topic,
        facet: clarify_types.Facet,
        query: str,
    ) -> tp.Dict[str, float]:
        pass


class TrecToolsMetricCalculator(MetricCalculator):
    def __init__(self, qrel_path: pathlib.Path):
        self.trec_qrel = trectools.TrecQrel(str(qrel_path))

    def calculate_metrics(
        self,
        ir_sys: InformationRetriever,
        topic: clarify_types.Topic,
        facet: clarify_types.Facet,
        query: str,
    ) -> tp.Dict[str, float]:
        f = tempfile.NamedTemporaryFile(mode="w", delete=False)
        ir_results = ir_sys.search(topic, query)
        for rank, r in enumerate(ir_results):
            print("%s-%s" % (topic.id, facet.id), 0, r[0].id, rank + 1, r[1], 0, file=f)
        f.close()
        trec_run = trectools.TrecRun(str(f.name))
        trec_eval = trectools.TrecEval(trec_run, self.trec_qrel)
        metrics = {}
        for v in [1, 5, 10, 20]:
            metrics[f"p@{v}"] = trec_eval.get_precision(
                depth=v, per_query=False, trec_eval=True
            )
            metrics[f"ndcg@{v}"] = trec_eval.get_ndcg(
                depth=v, per_query=False, trec_eval=True
            )
        metrics["mrr"] = trec_eval.get_reciprocal_rank(
            depth=1000, per_query=False, trec_eval=True
        )
        os.remove(f.name)
        return metrics
