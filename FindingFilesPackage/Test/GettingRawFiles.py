import datetime

from FindingFilesPackage import filemanager as fm

referenceDirectory = 'E:/Content/2021/8-22-21 Orcas Islands Whale Watching'
sourceDirectory = 'F:/Partially Sorted Orcas'


def main():

    ref = fm.FileManager()

    if sourceDirectory is not None:
        ref.CopyRAWFilesFromDirectory(sourceDirectory, referenceDirectory)


if __name__ == "__main__":
    main()
