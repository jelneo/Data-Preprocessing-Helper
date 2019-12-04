import os

import numpy as np
import rasterio
import pandas as pd
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
from rasterio import mask, warp, crs
from shapely.wkt import loads
import pyproj
from functools import partial
from shapely.ops import transform
from skimage.filters.rank import autolevel, mean_bilateral, enhance_contrast_percentile, minimum, maximum
from skimage.morphology import disk, diameter_opening, diameter_closing, area_closing, area_opening, erosion
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import StandardScaler, normalize
from sklearn.metrics import confusion_matrix, classification_report, accuracy_score
from sklearn.model_selection import cross_val_score
from sklearn.svm import SVC
from skimage.restoration import (denoise_tv_chambolle, denoise_bilateral,
                                 denoise_wavelet, estimate_sigma)
from skimage.filters import threshold_otsu, threshold_local, gaussian, threshold_multiotsu, rank, sobel, scharr, \
    prewitt, roberts, sobel_h, try_all_threshold, threshold_yen, threshold_mean
from scipy import ndimage as ndi, ndimage
from skimage import exposure, feature
from matplotlib import pyplot as plt
import seaborn as sns
import logging
import basicconfig as config
from trainingdata import get_labelled_feature_as_df, extract_features_from


parent_dir = "E:\\GRD\\"
input_dir = parent_dir + "Original\\"
processing_dir = parent_dir + "Processing\\"
processing_dir_LC = processing_dir + "LC\\"
mask_dir = processing_dir + "LC_Mask\\"
ml_dir = parent_dir + "ML\\LC\\"
classified_LC_dir = processing_dir + "LC_classification\\"


def convert_wkt_from_dd_to_m_to_polygon(wkt_in):
    wkt = loads(wkt_in)
    projection = partial(pyproj.transform, pyproj.Proj(init='epsg:4326'), pyproj.Proj(init='epsg:32645'))
    return transform(projection, wkt)

    # wkt = mapping(loads(wkt_in))
    # crs_src = crs.CRS.from_epsg(4326)
    # crs_dest = crs.CRS.from_epsg(32645)
    # geom = warp.transform_geom(crs_src, crs_dest, wkt)
    # return geom


def get_random_forest_model(train_x, train_y, num_estimators):
    rf = RandomForestClassifier(n_estimators=num_estimators)
    rf.fit(train_x, train_y)
    return rf


def get_k_means_model(train_x, num_clusters):
    k_means = KMeans(n_clusters=num_clusters)
    k_means.fit(train_x)
    return k_means


def get_k_nn_model(train_x, train_y, num_neighbors):
    k_nn = KNeighborsClassifier(n_neighbors=num_neighbors)
    k_nn.fit(train_x, train_y)
    return k_nn


# Initialise logger
logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(name)s: %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)


# for folder in os.listdir(output_dir):
def pretty_confusion_matrix(cm, title, class_names, normalize=False, figsize=(10, 7), fontsize=15):
    df_cm = pd.DataFrame(cm, index=class_names, columns=class_names)
    fig, ax = plt.subplots(figsize=figsize)
    try:
        if normalize:
            df_cm = df_cm.astype('float') / df_cm.sum(axis=1)[:, np.newaxis]
        ax = sns.heatmap(df_cm, annot=True, fmt="d", annot_kws={"size": 16}, cmap='Blues')
    except ValueError:
        raise ValueError("Confusion matrix values must be integers.")
    ax.yaxis.set_ticklabels(ax.yaxis.get_ticklabels(), rotation=0, ha='right', fontsize=fontsize)
    ax.xaxis.set_ticklabels(ax.xaxis.get_ticklabels(), rotation=45, ha='right', fontsize=fontsize)
    plt.ylabel('True label', fontsize=15)
    plt.xlabel('Predicted label', fontsize=15)
    ttl = plt.title(f'Confusion Matrix for {title}', fontsize=18)
    ttl.set_position([.5, 1.35])
    return fig


def plot_feature_importance(feature_names, importances):
    plt.figure()
    plt.title("Feature importances")
    plt.bar(feature_names, importances)
    # plt.xticks(range(X.shape[1]), indices)
    # plt.xlim([-1, X.shape[1]])
    plt.xticks(rotation='90')
    plt.tight_layout()
    plt.show()


# Get dataset
# TODO: currently works for one prdt, loop over directories to classify all prdts
loop_dir = processing_dir_LC
for folder in os.listdir(loop_dir):
    # acc_list = []
    # feat_impt_list = []
    logger.info(folder)
    if folder.endswith('.data') and f'glcm_{config.POLARIZATIONS}' in folder and ('S1B_IW_GRDH_1SDV_20190101T111959_20190101T112024_014300_01A9AA_8AF3_glcm_VV' in folder \
                                                                                  or "S1A_IW_GRDH_1SDV_20190107T112034_20190107T112059_025371_02CF15_BACB_glcm_VV" in folder):
        # for a in range(100):
            # feature_df = get_labelled_data(loop_dir + '\\' + folder)
            feature_df = get_labelled_feature_as_df(loop_dir + folder)
            # print(feature_df)
            logger.info(feature_df.dtypes)
            data = feature_df.iloc[:, :-1]
            labels = feature_df.iloc[:, -1:]
            # logger.info(f'Labelled set (Total): num of land pixels: {land_shape}, num of water pixels: {water_shape}')
            tr_x, test_x, tr_y, test_y = train_test_split(data, labels, train_size=0.7, stratify=labels)
            scaler = StandardScaler()
            tr_x_scaled = scaler.fit_transform(tr_x)
            test_x_scaled = scaler.transform(test_x)
            tr_y = np.array(tr_y).flatten()
            test_y = np.array(test_y).flatten()

            logger.info(f"train_x shape: {tr_x.shape}")
            logger.info(f"test_x shape: {test_x.shape}")
            num_land_test = test_y[test_y == config.LAND]
            logger.info(f"num of land test pixels: {num_land_test.shape}")
            num_water_test = test_y[test_y == config.WATER]
            logger.info(f"num of water test pixels: {num_water_test.shape}")

            logger.info("Fitting model...")
            clf = get_random_forest_model(tr_x_scaled, tr_y, num_estimators=50)
            feat_list = data.columns.values.tolist()
            feat_importances = clf.feature_importances_
            plot_feature_importance(feat_list, feat_importances)
            # feat_impt_list.append(feat_importances)
            feat_impt_dict = list(zip(feat_list, feat_importances))
            logger.info(f'Feature importance: {feat_impt_dict}')
            # cls = get_k_means_model(tr_x_scaled, num_clusters=2)
            # cls = get_k_nn_model(tr_x_scaled, tr_y, 8)

            logger.info("Classifying and evaluating test set")
            test_y_pred = clf.predict(test_x_scaled)
            # scores = cross_val_score(clf, )

            # accuracy = accuracy_score(test_y, test_y_pred)
            # acc_list.append(accuracy)
            confusion_mtx = confusion_matrix(test_y, test_y_pred)
            c_mtx = pretty_confusion_matrix(confusion_mtx, "Land-water classification", ['Land', 'Water'])
            c_mtx.savefig(parent_dir + "cm.jpg")
            c_mtx.show()
            print(classification_report(test_y, test_y_pred))

            tn, fp, fn, tp = confusion_mtx.ravel()
            logger.debug("(tn: {}, fp: {}, fn: {}, tp: {}):".format(tn, fp, fn, tp))

            logger.info("Classifying whole image...")
            prdt = rasterio.open(loop_dir + '\\' + folder + '\\' + f'Sigma0_{config.POLARIZATIONS}_db_GLCMMean.img')
            to_predict = extract_features_from(processing_dir_LC + folder)
            to_predict_scaled = scaler.transform(to_predict)
            predicted_flatten = clf.predict(to_predict_scaled)
            logger.info("Done predicting")

            predicted_flatten[predicted_flatten == config.LAND] = config.WHITE
            predicted_flatten[predicted_flatten == config.WATER] = config.BLACK
            predicted = np.reshape(predicted_flatten, (-1, prdt.width))
            predicted = predicted.astype('uint8')
            img = Image.fromarray(predicted)
            img.show()

            timestamp = folder.split("_")[4]
            with rasterio.open(
                    classified_LC_dir + f"land_water_mask_rf_{timestamp}_{config.POLARIZATIONS}.tif",
                    'w',
                    driver='GTiff',
                    height=prdt.height,
                    width=prdt.width,
                    count=1,
                    dtype=np.uint8,
                    crs=prdt.crs,
                    transform=prdt.transform,
            ) as dst:
                dst.write(predicted, 1)
        # mean_acc = np.mean(np.array(acc_list))
        # print(mean_acc)
        # mean_impt = np.mean(np.array(feat_impt_list), axis=0)
        # print(mean_impt)
        # plot_feature_importance(feat_list, mean_impt)
