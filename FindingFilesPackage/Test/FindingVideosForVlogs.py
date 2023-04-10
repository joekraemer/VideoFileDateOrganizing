import datetime

from FindingFilesPackage import filemanager as fm

Destructive = False
targetDirectory = '/Volumes/Backup Two/Content/2022 One Second/Content'
sourceDirectory = '/Volumes/Backup Two/Content/2022 One Second/Winnie\'s Photos'
#targetDirectory = 'D:/OneSecondTesting-Destination'
#sourceDirectory = 'D:/OneSecondTesting-Source'
dictionaryFilename = 'OneSecondDictionary.pickle'

start = datetime.date(2022, 1, 1)
end = datetime.date(2022, 12, 31)
start_datetime = datetime.datetime(start.year, start.month, start.day)
end_datetime = datetime.datetime(end.year, end.month, end.day)


def main():

    ref = fm.FileManager()

    if(ref.FindExistingDictionary(targetDirectory)):
        print("Existing Dictionary Found")

    lstMod = ref.OrganizedFoldersLastTimeModified(targetDirectory)
    lstUpdated = ref.LastTimeUpdated
    if(lstMod > lstUpdated) and False:
        # Add videos to dictionary that are already in the Target Directory
        print('Target Directory Updated, rescanning...')
        ref.IndexVideosInDirectory(targetDirectory, start_datetime, end_datetime)
        ref.UpdateLastTimeUpdated(datetime.datetime.now())

    if sourceDirectory != None:
        if Destructive:
            ref.DeletePhotosInDirectory(sourceDirectory)

            # Add videos to dictionary and then copy them
            ref.CutVideosFromDirectory(sourceDirectory, targetDirectory)

        else:
            # Add videos to dictionary and then delete them
            ref.CopyVideosFromDirectory(sourceDirectory, targetDirectory, start_datetime, end_datetime)

    ref.PrintNumberOfMissingDatesPerMonth(2022)
    ref.PrintNumberOfMissingDatesPerYear(2022)

    ref.PlotHeatMap(start, end)

    ref.UpdateLastTimeUpdated(datetime.datetime.now())
    ref.SaveDictionary(targetDirectory, dictionaryFilename)

if __name__ == "__main__":
    main()
