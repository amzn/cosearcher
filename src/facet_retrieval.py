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
import pathlib
import http.client, urllib.parse
import time
import string
import collections
import csv
from abc import ABC, abstractmethod
import tqdm

import qulac
import clarify_types


class FacetRetriever(ABC):
    @abstractmethod
    def facets_for_topic(
        self, topic: clarify_types.Topic
    ) -> tp.List[tp.Tuple[clarify_types.Facet, float]]:
        pass


class EnhancedFacetsFacetRetriever(FacetRetriever):
    def __init__(
        self, enhanced_reps_path: pathlib.Path, facet_retriever: FacetRetriever
    ):
        self.facet_retriever = facet_retriever
        r = csv.DictReader(enhanced_reps_path.open(errors="ignore"), delimiter="\t")
        self.enhanced_reps = {}
        for row in r:
            self.enhanced_reps[(row["topic"], row["provider_facet"])] = row[
                "provider_facet_enhanced"
            ]

    def facets_for_topic(
        self, topic: clarify_types.Topic
    ) -> tp.List[tp.Tuple[clarify_types.Facet, float]]:
        facets = self.facet_retriever.facets_for_topic(topic)
        for facet, _ in facets:
            facet.enhanced_rep = self.enhanced_reps[(topic.query, facet.desc)]
        return facets


class QulacFacetRetriever(FacetRetriever):
    def __init__(self, dataset: qulac.Qulac, enhanced_rep=False):
        self.dataset = dataset

    def facets_for_topic(
        self, topic: clarify_types.Topic
    ) -> tp.List[tp.Tuple[clarify_types.Facet, float]]:
        return [(facet, 0.0) for facet in topic.facets]


class BingFacetNode:
    def __init__(self, facet: str, depth: int):
        self.facet = facet
        self.neighbors = []  # type: tp.List[BingFacetNode]
        self.depth = depth


class BingFacetRetriever(FacetRetriever):
    def __init__(
        self,
        key: str,
        cache_path: pathlib.Path,
        max_depth: int = 1,
        endpoint: str = "api.bing.microsoft.com",
        bing_sleep: float = 3,
        chars: tp.List[str] = list(string.ascii_letters),
    ):
        assert max_depth > 0
        assert key is not None
        assert bing_sleep > 0
        self.endpoint = endpoint
        self.key = key
        self.cache_path = pathlib.Path(cache_path)
        self.max_depth = max_depth
        if self.cache_path.exists():
            with self.cache_path.open() as f:
                self.cache = json.load(f)
        else:
            self.cache = {}
        self.last_call_at = None
        self.bing_sleep = bing_sleep
        self.chars = chars

    def write_cache(self):
        with self.cache_path.open("w") as f:
            json.dump(self.cache, f)

    def expand_node(self, node: BingFacetNode):
        for character in [None] + self.chars:
            query = node.facet
            if character:
                query += " " + character
            for i, suggestion in enumerate(self._auto_suggest(query)):
                facet_desc = suggestion.strip()
                node.neighbors.append(BingFacetNode(facet_desc, node.depth + 1))

    def facets_for_topic(
        self, topic: clarify_types.Topic
    ) -> tp.List[tp.Tuple[clarify_types.Facet, float]]:
        facets = []  # type: tp.List[tp.Tuple[clarify_types.Facet, float]]
        seen = set()  # type: tp.Set[str]
        start = BingFacetNode(topic.query, 0)
        q = collections.deque([start])
        k = 0
        while q:
            node = q.popleft()
            # print("popped", node.facet, "depth", node.depth)
            if node.facet in seen:
                continue
            seen.add(node.facet)
            k += 1
            if node.facet != topic.query:
                facets.append(
                    (
                        clarify_types.Facet(
                            str(topic.id) + "_" + node.facet, node.facet, []
                        ),
                        float(k),
                    )
                )
            if node.depth < self.max_depth:
                # print("expand", node.facet, "depth", node.depth)
                self.expand_node(node)
            # print([n.facet for n in node.neighbors])
            q.extend(node.neighbors)
        return facets

    def _auto_suggest(self, query: str) -> tp.List[str]:
        if query in self.cache:
            return self.cache[query]
        if self.last_call_at:
            time.sleep(max(0, self.bing_sleep - (time.time() - self.last_call_at)))
        host = self.endpoint
        path = "/v7.0/Suggestions"
        mkt = "en-US"
        params = "?mkt=" + mkt + "&q=" + urllib.parse.quote(query)
        headers = {"Ocp-Apim-Subscription-Key": self.key}
        conn = http.client.HTTPSConnection(host)
        conn.request("GET", path + params, None, headers)
        response = conn.getresponse()
        if response.status != 200:
            raise Exception("Bing API returned status " + str(response.status))
        results = json.load(response)
        self.last_call_at = time.time()
        suggestions = []
        for i, suggestion in enumerate(
            results["suggestionGroups"][0]["searchSuggestions"]
        ):
            expanded_query = suggestion["query"]
            suggestions.append(expanded_query)
        self.cache[query] = suggestions
        self.write_cache()
        return suggestions


if __name__ == "__main__":
    dataset = qulac.Qulac(open("data/qulac.json"))
    retriever = BingFacetRetriever(YOUR_API_KEY)
    for topic in tqdm.tqdm(dataset.topics):
        facets = retriever.facets_for_topic(topic)
        print("topic:", topic.query)
        for facet, rank in facets:
            print("facet:", facet.desc)
        print("=" * 10)
