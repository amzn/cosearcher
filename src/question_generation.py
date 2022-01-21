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
from abc import ABC, abstractmethod

import clarify_types


class QuestionGenerator(ABC):
    @abstractmethod
    def generate_question(
        self, topic: clarify_types.Topic, facet: clarify_types.Facet
    ) -> str:
        pass


class DummyQuestionGenerator(QuestionGenerator):
    def generate_question(
        self, topic: clarify_types.Topic, facet: clarify_types.Facet
    ) -> str:
        facet_subj = facet.desc.rstrip(".?")
        return f"ARE YOU LOOKING TO {facet_subj}?"
