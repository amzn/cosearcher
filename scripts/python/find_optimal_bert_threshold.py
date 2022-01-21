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

import argparse
from sklearn.model_selection import cross_val_score
from sklearn.model_selection import GridSearchCV
from sklearn.base import BaseEstimator, ClassifierMixin
import sklearn.metrics
import pathlib
import csv
import numpy as np


class ThresholdEstimator(BaseEstimator, ClassifierMixin):
    def __init__(self, threshold=0.5):
        self.threshold = threshold

    def fit(self, X, y):
        return

    def predict(self, X):
        return X >= self.threshold


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--predictions", required=True, type=pathlib.Path)
    args = parser.parse_args()
    r = csv.DictReader(args.predictions.open(), delimiter="\t")
    X = []
    y = []
    for data in r:
        X.append([float(data["prediction"])])
        y.append(float(data["label"]))
    X = np.asarray(X)
    y = np.asarray(y).transpose()
    print(X.shape)
    print(y.shape)
    clf = ThresholdEstimator()
    cv = GridSearchCV(clf, {"threshold": np.linspace(0, 1, 100)}, cv=10, scoring="f1")
    cv.fit(X, y)
    # import pandas as pd
    # print(pd.DataFrame(cv.cv_results_))
    print("best score=", cv.best_score_)
    print("best params=", cv.best_params_)
    y_pred = clf.predict(X)
    print(
        "precision=",
        sklearn.metrics.precision_score(y, X[:, 0] >= cv.best_params_["threshold"]),
    )
    print(
        "recall=",
        sklearn.metrics.recall_score(y, X[:, 0] >= cv.best_params_["threshold"]),
    )
    print("f1=", sklearn.metrics.f1_score(y, X[:, 0] >= cv.best_params_["threshold"]))
    print("f1 at .5=", sklearn.metrics.f1_score(y, X[:, 0] >= 0.5))
