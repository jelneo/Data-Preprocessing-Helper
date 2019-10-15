import os

import numpy as np
import rasterio
import pandas as pd
from PIL import Image
from rasterio import mask
from shapely.wkt import loads
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import confusion_matrix, classification_report
from matplotlib import pyplot as plt
import seaborn as sns
import logging


BLACK = 0
WHITE = 255

LAND = 0
WATER = 1

LAND_POLYGON = "POLYGON ((102.21785910153146 14.378422767262887, 102.22278950110362 14.378422767262887, 102.22278950110362 14.373215201807398, 102.21785910153146 14.373215201807398, 102.21785910153146 14.378422767262887))"
WATER_POLYGON = "POLYGON ((102.2436310763137 14.417078332943644, 102.24857826349643 14.417078332943644, 102.24857826349643 14.412000956624544, 102.2436310763137 14.412000956624544, 102.2436310763137 14.417078332943644))"

parent_dir = "E:\\GRD\\"
input_dir = parent_dir + "Original\\"
output_dir = parent_dir + "Processing\\"
mask_dir = output_dir + "LC_Mask\\"
ml_dir = parent_dir + "ML\\LC\\"


def convert_wkt_to_polygon(wkt_in):
    return loads(wkt_in)


def read_product(src_path):
    prdt = rasterio.open(src_path)
    prdt_arr = prdt.read(1)
    print("(width, height): ({}, {})".format(prdt.width, prdt.height))
    # rows: height, columns: width
    return prdt_arr, (prdt.width, prdt.height)


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
clean = "E:\\GRD\\Processing\\LC\\S1A_IW_GRDH_1SDV_20190107T112034_20190107T112059_025371_02CF15_BACB_db_wgs84.dim"
clean_dim_dir = "E:\\GRD\Processing\\LC\\S1A_IW_GRDH_1SDV_20190107T112034_20190107T112059_025371_02CF15_BACB_glcm.data\\"
noisy = "E:\\GRD\\Processing\\LC\\S1A_IW_GRDH_1SDV_20190204T230053_20190204T230118_025786_02DE30_4711_db.tif"


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


def create_labels(land_len, water_len):
    land_labels = np.full(land_len, LAND)
    water_labels = np.full(water_len, WATER)
    target_labels = np.concatenate((land_labels, water_labels))
    return pd.DataFrame(target_labels, columns=['label'])


def get_labelled_dataset(class_1, class_2):
    target_labels = create_labels(class_1.shape, class_2.shape)
    land_flat = class_1.flatten()
    water_flat = class_2.flatten()
    dataset = np.concatenate((land_flat, water_flat))
    dataset = dataset[:, np.newaxis]
    return dataset, target_labels


# Get water and land mask to extract ground truths
def extract_features_from(path):
    features = []
    for file in os.listdir(path):
        if file.endswith('.img'):
            p = rasterio.open(path + file)
            prdt_arr = p.read(1)
            df = pd.DataFrame(prdt_arr.flatten(), columns=[p.descriptions[0]])
            features.append(df)
    return pd.concat(features, axis=1, sort=False)


def get_labelled_feature_as_df(file):
    global land_shape, water_shape
    p = rasterio.open(file)
    # print(p.crs)
    # print({i: dtype for i, dtype in zip(p.indexes, p.dtypes)})
    [land_arr], land_xy = mask.mask(dataset=p, shapes=[land_polygon], all_touched=True, crop=True)
    [water_arr], water_xy = mask.mask(dataset=p, shapes=[water_polygon], all_touched=True, crop=True)
    # plt.imshow(water_arr)
    # plt.show()
    # plt.imshow(p.read(1))
    # plt.show()
    if land_shape < 0:
        land_shape = land_arr.shape[0] * land_arr.shape[1]
    if water_shape < 0:
        water_shape = water_arr.shape[0] * water_arr.shape[1]
    # logger.info(land_arr.shape)
    # logger.info(water_arr.shape)
    # logger.info(p.crs)
    land_water_arr = np.concatenate((land_arr.flatten(), water_arr.flatten()))
    df = pd.DataFrame(land_water_arr, columns=[p.descriptions[0]])
    return df


def get_labelled_data(path):
    feature_bands = [get_labelled_feature_as_df(path + f) for f in os.listdir(path) if f.endswith('.img')]
    feature_bands.append(create_labels(land_shape, water_shape))
    return pd.concat(feature_bands, axis=1, sort=False)


# Get dataset
land_shape = -1
water_shape = -1
land_polygon = convert_wkt_to_polygon(LAND_POLYGON)
water_polygon = convert_wkt_to_polygon(WATER_POLYGON)
feature_df = get_labelled_data(clean_dim_dir)
data = feature_df.iloc[:, :-1]
labels = feature_df.iloc[:, -1:]
logger.info(f'Labelled set (Total): num of land pixels: {land_shape}, num of water pixels: {water_shape}')
tr_x, test_x, tr_y, test_y = train_test_split(data, labels, train_size=0.7, stratify=labels)
scaler = StandardScaler()
tr_x_scaled = scaler.fit_transform(tr_x)
test_x_scaled = scaler.transform(test_x)
tr_y = np.array(tr_y).flatten()
test_y = np.array(test_y).flatten()

logger.info(f"train_x shape: {tr_x.shape}")
logger.info(f"test_x shape: {test_x.shape}")
num_land_test = test_y[test_y == LAND]
logger.info(f"num of land test pixels: {num_land_test.shape}")
num_water_test = test_y[test_y == WATER]
logger.info(f"num of water test pixels: {num_water_test.shape}")

logger.info("Fitting model...")
cls = get_random_forest_model(tr_x_scaled, tr_y, num_estimators=50)
# cls = get_k_nn_model(tr_x, tr_y, 8)

logger.info("Classifying and evaluating test set")
test_y_pred = cls.predict(test_x_scaled)
confusion_mtx = confusion_matrix(test_y, test_y_pred)
c_mtx = pretty_confusion_matrix(confusion_mtx, "Land-water classification", ['Land', 'Water'])
# c_mtx.savefig(parent_dir + "cm.jpg")
c_mtx.show()
print(classification_report(test_y, test_y_pred))

tn, fp, fn, tp = confusion_mtx.ravel()
logger.info("(tn: {}, fp: {}, fn: {}, tp: {}):" .format(tn, fp, fn, tp))

logger.info("Classifying whole image...")
prdt = rasterio.open(clean_dim_dir + 'Sigma0_VV_db.img')
to_predict = extract_features_from(clean_dim_dir)
to_predict_scaled = scaler.transform(to_predict)
predicted_flatten = cls.predict(to_predict_scaled)
logger.info("Done predicting")

predicted_flatten[predicted_flatten == LAND] = WHITE
predicted_flatten[predicted_flatten == WATER] = BLACK
predicted = np.reshape(predicted_flatten, (-1, prdt.width))
predicted = predicted.astype('uint8')
img = Image.fromarray(predicted)
img.show()
img.save(parent_dir + "land_water_mask.tif", format="TIFF")
