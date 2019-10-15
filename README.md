# Data-Preprocessing-Helper
A repo that contains helper methods to make data preprocessing easier for machine learning or other applicable use cases

## Library for data preprocessing

### Functions for data manipulation

#### Dataframe
1. Slicing from column x to column y
2. Slicing from row x to row y
3. Drop column x to column y
4. Drop row x to row y
5. Insert x new columns after column y
6. Insert x new rows after row y
7. Data segmentation

#### Data Values
1. Normalize data (handles divide by 0 case)


### Functions for file manipulation
1. Concatenate multiple data files into one
2. 

### Functions for data visualization
1. Line plot for raw data / features (with and without data points)
2. Line plot for histogram

# sar_machine_learning
This directory contains code for 2 main components:
1. Data conversion (GeoTIFF to raster) before data is fed into ML models
2. Tuning and training of ML models

## Dependencies
For component 1: [rasterio](https://rasterio.readthedocs.io/en/stable/)

For component 2: mainly scikit-learn, numpy, pandas, scipy, joblib
git sta