import datetime

from FindingFilesPackage import filemanager as fm

Destructive = False
targetDirectory = 'D:/target'
sourceDirectory = 'D:/ResolveTestingOneSecond'
dictionaryFilename = 'OneSecondDictionary.pickle'


def main():

    ref = fm.FileManager()

    if(ref.FindExistingDictionary(targetDirectory)):
        print("Existing Dictionary Found")

    lstMod = ref.OrganizedFoldersLastTimeModified(targetDirectory)
    lstUpdated = ref.LastTimeUpdated
    if(lstMod > lstUpdated):
        # Add videos to dictionary that are already in the Target Directory
        print('Target Directory Updated, rescanning...')
        ref.IndexVideosInDirectory(targetDirectory)
        ref.UpdateLastTimeUpdated(datetime.datetime.now())

    if sourceDirectory != None:
        if Destructive:
            ref.DeletePhotosInDirectory(sourceDirectory)

            # Add videos to dictionary and then copy them
            ref.CutVideosFromDirectory(sourceDirectory, targetDirectory)

        else:
            # Add videos to dictionary and then delete them
            ref.CopyVideosFromDirectory(sourceDirectory, targetDirectory)

    ref.PrintNumberOfMissingDatesPerMonth(2020)
    ref.PrintNumberOfMissingDatesPerYear(2020)

    start = datetime.date(2020, 1, 1)
    end = datetime.date(2020, 12, 31)
    ref.PlotHeatMap(start, end)

    ref.SaveDictionary(targetDirectory, dictionaryFilename)


if __name__ == "__main__":
    main()
