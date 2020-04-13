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
from sklearn.cluster import KMeans
from sklearn.metrics import accuracy_score
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt

import basicconfig as config
import filemanager
from trainingdata import get_labelled_features_as_df


# Initialise logger
logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(name)s: %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)


input_dir, output_dir = filemanager.get_file_paths_based_on_os(platform.system(), filemanager.Product.grd)
loop_dir = output_dir + config.LC_PATH
ml_dir = output_dir + config.ML_DIR
classified_LC_dir = output_dir + config.LC_CLASSIFIED_DIR

num_trees = 50
num_neigh = 3
c_val = 1.0
for i in range(11):
    clf_names = [f"RF (num trees = {num_trees})", f"K-NN (k = {num_neigh})", f"SVM with regularization , C = {c_val}", "KMeans (cluster=2)"]
    results = [[] for j in range(len(clf_names))]
    count = 0
    for folder in os.listdir(loop_dir):
        if folder.endswith('.data') and f'glcm_{config.POLARIZATIONS}' in folder:
            count += 1
            logger.info(folder)
            feature_df = get_labelled_features_as_df(loop_dir + folder)
            dataset = feature_df.iloc[:, :-1]
            labels = feature_df.iloc[:, -1:]
            y = np.array(labels).flatten()

            rf_clf = RandomForestClassifier(n_estimators=num_trees)
            scaler = StandardScaler()
            pipeline = Pipeline([('transformer', scaler), ('estimator', rf_clf)])
            result = cross_val_score(pipeline, dataset, y, cv=10)
            results[0].append(result.tolist())

            knn_clf = KNeighborsClassifier(n_neighbors=num_neigh)
            scaler = StandardScaler()
            pipeline = Pipeline([('transformer', scaler), ('estimator', knn_clf)])
            result = cross_val_score(pipeline, dataset, y, cv=10)
            results[1].append(result.tolist())

            svm_rbf_clf = SVC(gamma='auto', C=c_val)
            scaler = StandardScaler()
            pipeline = Pipeline([('transformer', scaler), ('estimator', svm_rbf_clf)])
            result = cross_val_score(pipeline, dataset, y, cv=10)
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
    clf_results.append("\n\n")
    out = open(output_dir + "comparison_ML.txt", 'a')
    out.writelines(clf_results)
    out.close()

results = []


def visualize_clusters(data):
    reduced_data = PCA(n_components=2).fit_transform(data)
    kmeans = KMeans(init='k-means++', n_clusters=2, n_init=10)
    kmeans.fit(reduced_data)
    # Step size of the mesh. Decrease to increase the quality of the VQ.
    h = .02  # point in the mesh [x_min, x_max]x[y_min, y_max].
    # Plot the decision boundary. For that, we will assign a color to each
    x_min, x_max = reduced_data[:, 0].min() - 1, reduced_data[:, 0].max() + 1
    y_min, y_max = reduced_data[:, 1].min() - 1, reduced_data[:, 1].max() + 1
    xx, yy = np.meshgrid(np.arange(x_min, x_max, h), np.arange(y_min, y_max, h))
    # Obtain labels for each point in mesh. Use last trained model.
    Z = kmeans.predict(np.c_[xx.ravel(), yy.ravel()])
    # Put the result into a color plot
    Z = Z.reshape(xx.shape)
    plt.figure(1)
    plt.clf()
    plt.imshow(Z, interpolation='nearest',
               extent=(xx.min(), xx.max(), yy.min(), yy.max()),
               cmap=plt.cm.Paired,
               aspect='auto', origin='lower')
    plt.plot(reduced_data[:, 0], reduced_data[:, 1], 'k.', markersize=2)
    # Plot the centroids as a white X
    centroids = kmeans.cluster_centers_
    plt.scatter(centroids[:, 0], centroids[:, 1],
                marker='x', s=169, linewidths=3,
                color='w', zorder=10)
    plt.title('K-means clustering for one of the iterations on the Lam Chae\n reservoir dataset (PCA-reduced data)\n'
              'Centroids are marked with white cross')
    plt.xlim(x_min, x_max)
    plt.ylim(y_min, y_max)
    plt.xticks(())
    plt.yticks(())
    plt.show()


for folder in os.listdir(loop_dir):
    if folder.endswith('.data') and f'glcm_{config.POLARIZATIONS}' in folder:
        logger.info(folder)
        feature_df = get_labelled_features_as_df(loop_dir + folder)
        scaler = StandardScaler()
        dataset = feature_df.iloc[:, :-1]
        dataset = scaler.fit_transform(dataset)
        labels = feature_df.iloc[:, -1:]
        y = np.array(labels).flatten()
        pca = PCA(n_components=2).fit(dataset)
        # kmeans_clf = KMeans(n_clusters=2, init=pca.components_, n_init=1, max_iter=1000)
        kmeans_clf = KMeans(n_clusters=2, init='random', n_init=25, max_iter=1000)
        kmeans_clf.fit(dataset)
        predicted = kmeans_clf.predict(dataset)
        results.append(accuracy_score(y, predicted))

        visualize_clusters(dataset)

results = np.array(results)
print('K-means clustering:')
print("Accuracy: %.3f%% (%.3f%%)\n" % (results.mean() * 100.0, results.std() * 100.0))
