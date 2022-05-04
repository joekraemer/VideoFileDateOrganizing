import datetime

from filemanager import filemanager as fm

goodPhotoDirectory = 'C:/Users/joek/Desktop/2-22-2022 Hawaii/a6400/Narrowing'
referenceDirectory = 'E:/Content/2022/2-17-22 Hawaii - Big Island/a6400'


def main():

    ref = fm.FileManager()

    if goodPhotoDirectory is not None:
        ref.CopyRAWFilesFromDirectory(goodPhotoDirectory, referenceDirectory)


if __name__ == "__main__":
    main()
