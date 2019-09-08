import os

# Function to rename multiple files
def main():
    dir_name = 'D:\\ESA Tutorial\\Original\\'
    print('Renaming files...')
    for filename in os.listdir(dir_name):
        if '.SAFE2' in filename:
            dst = filename.replace('.SAFE2', '_2')
            src = dir_name + filename
            dst = dir_name + dst

            # rename() function will
            # rename all the files
            os.rename(src, dst)
    print('Done')

# Driver Code
if __name__ == '__main__':
    # Calling main() function
    main()