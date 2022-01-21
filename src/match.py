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

import numpy as np
import torch
import pathlib
import sys
import scipy
import random
from abc import ABC, abstractmethod

import utils
from thirdparty import lexvec
import transformers


class SentenceMatcher(ABC):
    def __init__(self, *args, **kwargs):
        pass

    @abstractmethod
    def similarity(self, sent1: str, sent2: str) -> float:
        pass


class RandomSentenceMatcher(SentenceMatcher):
    def similarity(self, sent1: str, sent2: str) -> float:
        return random.random()


class BOVSentenceMatcher(SentenceMatcher):
    def __init__(self, lexvec_path: pathlib.Path):
        self.lexvec = lexvec.Model(lexvec_path)

    def similarity(self, sent1: str, sent2: str) -> float:
        rep1 = self.encode(sent1)
        rep2 = self.encode(sent2)
        norm = np.linalg.norm(rep1) * np.linalg.norm(rep2)
        if norm == 0:
            return 0
        sim = (1 + np.dot(rep1, rep2) / norm) / 2
        return sim

    def encode(self, sent: str) -> np.ndarray:
        tokens = utils.strip_punctuation(sent).lower().split()
        weights = np.ones(len(tokens))
        if weights.sum():
            weights /= weights.sum()
        vectors = [
            weight * self.lexvec.word_rep(word) for word, weight in zip(tokens, weights)
        ]
        return np.sum(vectors, axis=0)


class TransformerSentenceMatcher(SentenceMatcher):
    def __init__(self, transformer_path):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = transformers.AutoModelForSequenceClassification.from_pretrained(
            transformer_path
        )
        self.model.to(self.device)
        self.tokenizer = transformers.AutoTokenizer.from_pretrained(transformer_path)

    def similarity(self, sent1: str, sent2: str) -> float:
        inputs = self.tokenizer(
            sent1, sent2, padding=False, truncation=True, return_tensors="pt"
        ).to(self.device)
        with torch.no_grad():
            outputs = self.model(**inputs)
            preds = outputs.logits.detach().cpu().numpy()
            preds = preds[:, 1]
            preds = scipy.special.expit(preds)
        return float(preds.squeeze())


class CachingSentenceMatcher(SentenceMatcher):
    def __init__(self, matcher):
        self.matcher = matcher
        self.cache = {}

    def similarity(self, sent1: str, sent2: str) -> float:
        key = (sent1, sent2)
        if key in self.cache:
            return self.cache[key]
        value = self.matcher.similarity(sent1, sent2)
        self.cache[key] = value
        return value


MATCHERS = {
    "transformer": TransformerSentenceMatcher,
    "bov": BOVSentenceMatcher,
    "random": RandomSentenceMatcher,
}
