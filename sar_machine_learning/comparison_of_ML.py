import logging
import os
import platform

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

import basicconfig as config
import filemanager
from trainingdata import get_labelled_feature_as_df

input_dir, output_dir = filemanager.get_file_paths_based_on_os(platform.system(), filemanager.Product.grd)
input_dir = output_dir + config.LC_PATH

ml_dir = output_dir + config.ML_DIR
classified_LC_dir = output_dir + config.LC_CLASSIFIED_DIR

# Initialise logger
logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(name)s: %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)


input_dir, output_dir = filemanager.get_file_paths_based_on_os(platform.system(), filemanager.Product.grd)
loop_dir = output_dir + config.LC_PATH

num_trees = 50
num_neigh = 3
c_val = 1.0
for i in range(10):
    clf_names = [f"RF (num trees = {num_trees})", f"K-NN (k = {num_neigh})", f"SVM with regularization , C = {c_val}"]
    results = [[] for j in range(len(clf_names))]
    count = 0
    for folder in os.listdir(loop_dir):
        if folder.endswith('.data') and f'glcm_{config.POLARIZATIONS}' in folder:
            count += 1
            logger.info(folder)
            feature_df = get_labelled_feature_as_df(loop_dir + folder)
            X = feature_df.iloc[:, :-1]
            labels = feature_df.iloc[:, -1:]
            y = np.array(labels).flatten()

            rf_clf = RandomForestClassifier(n_estimators=num_trees)
            scaler = StandardScaler()
            pipeline = Pipeline([('transformer', scaler), ('estimator', rf_clf)])
            result = cross_val_score(pipeline, X, y, cv=10)
            results[0].append(result.tolist())

            knn_clf = KNeighborsClassifier(n_neighbors=num_neigh)
            scaler = StandardScaler()
            pipeline = Pipeline([('transformer', scaler), ('estimator', knn_clf)])
            result = cross_val_score(pipeline, X, y, cv=10)
            results[1].append(result.tolist())

            svm_rbf_clf = SVC(gamma='auto', C=c_val)
            scaler = StandardScaler()
            pipeline = Pipeline([('transformer', scaler), ('estimator', svm_rbf_clf)])
            result = cross_val_score(pipeline, X, y, cv=10)
            results[2].append(result.tolist())

            if count == 20:
                break
    c_val += 0.1
    num_neigh += 2
    num_trees += 10

    clf_results = []
    for k in range(len(clf_names)):
        curr_result = np.array(results[k])
        clf_results.append(f"{clf_names[k]} - Accuracy: %.3f%% (%.3f%%)\n" % (curr_result.mean() * 100.0, curr_result.std() * 100.0))
    clf_results.append("\n")
    out = open(output_dir + "comparison_ML.txt", 'a')
    out.writelines(clf_results)
    out.close()
