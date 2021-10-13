import datetime

'''This Script will parse a folder of photos and move photos that were taken close 
together ( implying they were bursts, stacks or brackets ) into folders. 

These files are moved to folders in the reference directory
'''

from FindingFilesPackage import filemanager as fm

referenceDirectory = 'E:/Content/2021/10-12-21 Chen Fam at Gas Works - Copy/jpgs'


def main():

    ref = fm.FileManager()

    if referenceDirectory is not None:
        ref.GroupBurstPhotosInDirectory(referenceDirectory)


if __name__ == "__main__":
    main()
