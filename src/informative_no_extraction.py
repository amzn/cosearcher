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

import re
from abc import ABC, abstractmethod


import utils


class InformativeNoExtractor(ABC):
    @abstractmethod
    def extract(self, answer: str) -> str:
        pass


class DummyInformativeNoExtractor(InformativeNoExtractor):
    pat = re.compile(r"^(no|i m|i am)", flags=re.RegexFlag.IGNORECASE)  # type: ignore

    def extract(self, answer: str) -> str:
        answer = utils.strip_punctuation(answer)
        return re.sub(self.pat, "", answer).strip()  # type: ignore
