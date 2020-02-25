import logging
import os
import platform
import statistics

import numpy as np
import pandas as pd
import rasterio
import seaborn as sns
from PIL import Image
from matplotlib import pyplot as plt
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import confusion_matrix, classification_report, accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

import basicconfig as config
import filemanager
from trainingdata import get_labelled_feature_as_df, extract_features_from

input_dir, output_dir = filemanager.get_file_paths_based_on_os(platform.system(), filemanager.Product.grd)
input_dir = output_dir + config.LC_PATH

ml_dir = output_dir + config.ML_DIR
classified_LC_dir = output_dir + config.LC_CLASSIFIED_DIR


# def convert_wkt_from_dd_to_m_to_polygon(wkt_in):
#     wkt = loads(wkt_in)
#     projection = partial(pyproj.transform, pyproj.Proj(init='epsg:4326'), pyproj.Proj(init='epsg:32645'))
#     return transform(projection, wkt)
#
#     # wkt = mapping(loads(wkt_in))
#     # crs_src = crs.CRS.from_epsg(4326)
#     # crs_dest = crs.CRS.from_epsg(32645)
#     # geom = warp.transform_geom(crs_src, crs_dest, wkt)
#     # return geom


def get_random_forest_model(train_x, train_y, num_estimators):
    rf = RandomForestClassifier(n_estimators=num_estimators)
    rf.fit(train_x, train_y)
    return rf


# Initialise logger
logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(name)s: %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)


def pretty_confusion_matrix(cm, title, timestamp, class_names, normalize=False, figsize=(8, 6), fontsize=15):
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
    ax.set(yticks=[-0.0, 2.0],
           xticks=[0.5, 1.5],
           )
    ttl = plt.title(f'Confusion Matrix for {title}\n{timestamp}', fontsize=18, pad=20)
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
loop_dir = input_dir
acc_list = []
for folder in os.listdir(loop_dir):
    # acc_list = []
    # feat_impt_list = []
    if folder.endswith('.data') and f'glcm_{config.POLARIZATIONS}' in folder:
            logger.info(folder)
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


            clf = get_random_forest_model(tr_x_scaled, tr_y, num_estimators=150)

            feat_list = data.columns.values.tolist()
            # feat_importances = clf.feature_importances_

            # plot_feature_importance(feat_list, feat_importances)
            # feat_impt_list.append(feat_importances)

            # feat_impt_dict = list(zip(feat_list, feat_importances))
            # logger.info(f'Feature importance: {feat_impt_dict}')

            logger.info("Classifying and evaluating test set")
            test_y_pred = clf.predict(test_x_scaled)

            confusion_mtx = confusion_matrix(test_y, test_y_pred)
            timestamp = folder.split("_")[4]
            # c_mtx = pretty_confusion_matrix(confusion_mtx, "Land-water classification", timestamp, ['Land', 'Water'])
            # c_mtx.savefig(ml_dir + "cm.jpg")
            # c_mtx.show()
            acc_list.append(accuracy_score(test_y, test_y_pred))
            print(classification_report(test_y, test_y_pred))

            tn, fp, fn, tp = confusion_mtx.ravel()
            logger.debug("(tn: {}, fp: {}, fn: {}, tp: {}):".format(tn, fp, fn, tp))

            logger.info("Classifying whole image...")
            prdt = rasterio.open(loop_dir + '\\' + folder + '\\' + f'Sigma0_{config.POLARIZATIONS}_GLCMMean.img')
            to_predict = extract_features_from(input_dir + folder)
            to_predict_scaled = scaler.transform(to_predict)
            predicted_flatten = clf.predict(to_predict_scaled)
            logger.info("Done predicting")

            # visualize the prediction in black and white image
            predicted_flatten[predicted_flatten == config.LAND] = config.WHITE
            predicted_flatten[predicted_flatten == config.WATER] = config.BLACK
            predicted = np.reshape(predicted_flatten, (-1, prdt.width))
            predicted = predicted.astype('uint8')
            img = Image.fromarray(predicted)
            # img.show()

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

print(f"Mean accuracy: {statistics.mean(acc_list) * 100}%")
# mean_acc = np.mean(np.array(acc_list))
# print(mean_acc)
# mean_impt = np.mean(np.array(feat_impt_list), axis=0)
# print(mean_impt)
# plot_feature_importance(feat_list, mean_impt)
