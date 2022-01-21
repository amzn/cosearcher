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


set -xe 

DEST=data/ql

mkdir -p $DEST/clueweb_stats
if [ ! -f $DEST/clueweb_stats/doc_lengths.tar.gz ]; then
    echo "Downloading doc_lengths.tar.gz"
    curl http://ciir.cs.umass.edu/downloads/qulac/data/clueweb_stats/doc_lengths.tar.gz -o $DEST/clueweb_stats/doc_lengths.tar.gz
fi
tar -xzf $DEST/clueweb_stats/doc_lengths.tar.gz -C $DEST/clueweb_stats
if [ ! -f $DEST/clueweb_stats/term_stats.krovetz.tar.gz ]; then
    curl http://ciir.cs.umass.edu/downloads/qulac/data/clueweb_stats/term_stats.krovetz.tar.gz -o $DEST/clueweb_stats/term_stats.krovetz.tar.gz
fi
tar -xzf $DEST/clueweb_stats/term_stats.krovetz.tar.gz -C $DEST/clueweb_stats

mkdir -p $DEST/topic_indexes
for i in `seq 1 200`; do
    if [ ! -f $DEST/topic_indexes/$i.tar.gz ]; then
        curl http://ciir.cs.umass.edu/downloads/qulac/data/topic_indexes/$i.tar.gz -o $DEST/topic_indexes/$i.tar.gz
    fi
    tar -xzf $DEST/topic_indexes/$i.tar.gz -C $DEST/topic_indexes
done