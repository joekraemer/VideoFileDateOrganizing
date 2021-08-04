import datetime

from FindingFilesPackage import filemanager as fm

referenceDirectory = 'E:/Content/2021/7-28-21 Breckenridge Bachelor Party/A6300'
sourceDirectory = 'C:/Users/joek/Desktop/Best Photos/Photos to add to lightroom for the boys'


def main():

    ref = fm.FileManager()

    if sourceDirectory is not None:
        ref.CopyRAWFilesFromDirectory(sourceDirectory, referenceDirectory)


if __name__ == "__main__":
    main()
