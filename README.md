# Data-Preprocessing-Helper

This repository contains the code for my final year project: Machine Learning Applied to Radar Remote Sensing: A case study of Lam Chae Reservoir.
Details about each directory is listed below.

## datacleaning
- Remove temporary water bodies from binary images (outputs from machine learning models)
- Checks for anomalies like corrupted files (which will turn up blank)

## preprocessing
Preprocesses Sentinel-1 GRD and SLC products

## sar_machine_learning
- Compares different machine learning models
- Experiment with different types of filters and threhsolding methods
- Prepares training data
- Performs land-water classification to obtain images of water and land in black and white

## snappy_tools
Contains snappy configurations and operators

## volumedata
Makes API calls to thaiwater.net to fetch reservoir storage, inflow and climate data
