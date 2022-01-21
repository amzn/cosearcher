#!/bin/sh

curl -L https://raw.githubusercontent.com/alexandres/lexvec/master/python/lexvec/model.py -o src/thirdparty/lexvec.py

git clone https://github.com/aliannejadi/qulac.git src/thirdparty/qulac
git checkout d175f0179cb4084067f82a5b27d423bc2d9d8656
mv src/thirdparty/qulac/src src/thirdparty/ql
rm -rf src/thirdparty/qulac
touch src/thirdparty/ql/__init__.py
pushd .
cd src/thirdparty/ql/ql_score
python3 setup.py build_ext --inplace
popd

curl -L https://raw.githubusercontent.com/huggingface/transformers/1.1.0/examples/run_glue.py -o src/thirdparty/transformer/run_glue.py
curl -L https://raw.githubusercontent.com/huggingface/transformers/1.1.0/examples/utils_glue.py -o src/thirdparty/transformer/utils_glue.py
