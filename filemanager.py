''' This file handles file related operations'''

manifest_extension = "\\manifest.safe"


def get_file_paths_based_on_os(usr_system):
    if usr_system == "Windows":
        parent_dir = "D:\\FYP_IW\\"
        # input_dir = parent_dir + "Original\\"
        # output_dir = parent_dir + "Processing\\"
        input_dir = parent_dir + "Test\\"
        output_dir = parent_dir + "TestProc\\"
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
