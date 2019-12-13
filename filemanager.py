import enum
import basicconfig as config

''' This file handles file related operations'''


class Product(enum.Enum):
    grd = 0
    slc = 1


def get_file_paths_based_on_os(usr_system, prdt: Product):
    if usr_system == "Windows":
        parent_dir = ''
        if prdt == Product.grd:
            parent_dir = config.GRD_PARENT_DIR
        elif prdt == Product.slc:
            parent_dir = config.SLC_PARENT_DIR
        else:
            print("No directory set for this system.\nProgram exiting...")
            exit(1)
        input_dir = parent_dir + "Original\\"
        output_dir = parent_dir + "Processing\\"
        return input_dir, output_dir
    elif usr_system == "Linux":
        # For hpc
        parent_dir = "/hpctmp2/a0158174/"
        input_dir = parent_dir + "Original/"
        output_dir = input_dir + "Processing/"
        return input_dir, output_dir
    else:
        print("No directory set for this system.\nProgram exiting...")
        exit(1)
