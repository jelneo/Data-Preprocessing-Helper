import os
import rasterio
import numpy as np

parent_dir = "E:\\GRD\\"
input_dir = parent_dir + "Original\\"
output_dir = parent_dir + "Processing\\"

f = open(output_dir + "outliers.txt", 'w+')
for folder in os.listdir(output_dir):
    if folder.endswith('.tif'):
        print("Current folder: " + folder)
        data = rasterio.open(output_dir + folder)
        data_arr = data.read(1)
        std_dev = np.std(data_arr)
        if std_dev == 0:
            f.write(folder[:50] + "\n")
f.close()
