#!/bin/bash

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


mkdir -p data
if [ ! -f data/qulac.json ]; then
    curl https://raw.githubusercontent.com/aliannejadi/qulac/master/data/qulac/qulac.json -o data/qulac.json
    curl https://raw.githubusercontent.com/aliannejadi/qulac/master/data/qulac/faceted.qrel -o data/faceted.qrel
fi

mkdir -p data/embeddings
if [ ! -f data/embeddings/lexvec.commoncrawl.ngramsubwords.300d.W.pos.bin ]; then
    curl -L https://www.dropbox.com/s/buix0deqlks4312/lexvec.commoncrawl.ngramsubwords.300d.W.pos.bin.gz?dl=1 -o data/embeddings/lexvec.commoncrawl.ngramsubwords.300d.W.pos.bin.gz
    gunzip data/embeddings/lexvec.commoncrawl.ngramsubwords.300d.W.pos.bin.gz
fi

scripts/download_ql_data.sh