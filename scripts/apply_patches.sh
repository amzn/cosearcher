#!/bin/sh

patch src/thirdparty/lexvec.py < patches/lexvec.patch
patch src/thirdparty/ql/QL.py < patches/ql_QL.patch
patch src/thirdparty/ql/utils/utils.py < patches/ql_utils.patch
patch src/thirdparty/transformer/run_glue.py < patches/transformer_run_glue.patch
patch src/thirdparty/transformer/utils_glue.py < patches/transformer_utils_glue.patch