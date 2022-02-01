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


pip3 install -r requirements.txt
python3 -c "import nltk; nltk.download('stopwords'); nltk.download('punkt')"

curl -L https://raw.githubusercontent.com/alexandres/lexvec/master/python/lexvec/model.py -o src/thirdparty/lexvec.py

git clone https://github.com/aliannejadi/qulac.git src/thirdparty/qulac
pushd .
cd src/thirdparty/qulac
git checkout d175f0179cb4084067f82a5b27d423bc2d9d8656
popd
mv src/thirdparty/qulac/src src/thirdparty/ql
rm -rf src/thirdparty/qulac
touch src/thirdparty/ql/__init__.py
pushd .
cd src/thirdparty/ql/ql_score
python3 setup.py build_ext --inplace
popd

curl -L https://raw.githubusercontent.com/huggingface/transformers/1.1.0/examples/run_glue.py -o src/thirdparty/transformer/run_glue.py
curl -L https://raw.githubusercontent.com/huggingface/transformers/1.1.0/examples/utils_glue.py -o src/thirdparty/transformer/utils_glue.py
