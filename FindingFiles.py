import os
import glob
import pytz
import datetime
import time
import calendar
import pywintypes
import shutil
import pickle
from collections import defaultdict
from win32com.propsys import propsys, pscon
from pathlib import Path
import datetime

current_dir_path = os.path.dirname(os.path.realpath(__file__))
videoExtensions = ["*.mp4", "*.mov", "*.MP4", "*.avi", "*.mkv", "*.m4v"]
photoExtensions = ["*.jpg", "*.heic", "*.ARW", "*.png", "*.dng", "*.jpeg"]
pickleExtensions = ["*.pickle"]
Destructive = False
largeDateNumberLimit = 10
targetDirectory = 'D:/OneSecond/Testing/Destination'
sourceDirectory = 'D:/OneSecond/Testing/Source'
dictionaryFilename = 'dictionary.pickle'


class FileInformation:
    def __init__(self, lastDirFound):
        self.LastDirectoryFound = lastDirFound
        self.ExistsInCurrentDir = True

        # Extract name
        head_tail = os.path.split(lastDirFound)
        self.Name = head_tail[1]

        # Get Creation Date
        dt = GetCreationDateFromVideo(lastDirFound)
        self.DateTime = dt

        self.Size = os.path.getsize(lastDirFound)
        # Could add other relevent things like metadata or tags

# Used when a cluster of files is large so that we can leave the files else where, but still track essential information about them


class FileClusterManager:
    def __init__(self, date, path):
        self.Size = 0
        # List of FileInformation Classes
        self.Files = []
        self.FilesExistOnDisk = False
        self.Date = date

        self.Path = os.path.join(
            path, str(self.Date.year), str(self.Date.month))

    # Add files to this cluster
    def Add(self, file):
        self.Files.append(file)
        self.FilesExistOnDisk = True

        # Here we should make the call to move the file to the cluster
        # to create a folder and move existing files
        return

    # How many files in this cluster
    def Number(self):
        return len(self.Files)

    def GetFiles(self):
        return self.Files

    # Return the Path that files for this cluster should go to
    def GetPath(self):
        return self.Path

    # TODO
    # Finding Existing files in cluster and moving them to a
    # new folder because there are now too many to just free roam
    def IsSecondFile(self):
        # move existing file into this new date folder
        for files in self.GetFiles(dt):
            newFile = os.path.join(pathDestination, files.name)
            Path.rename(files, newFile)

            # update file in the dictionary
            self.DeleteEntry(dt)
            self.Add(newFile, dt)


def ConvertToDateTime(pywintime):
    now_datetime = datetime.datetime(
        year=pywintime.year,
        month=pywintime.month,
        day=pywintime.day,
        hour=pywintime.hour,
        minute=pywintime.minute,
        second=pywintime.second
    )
    return now_datetime


def MakeFolder(path):
    print(path)

    if os.path.exists(path):
        print('Path already exists')
        return

    head = os.path.split(path)[0]
    if not os.path.exists(head):
        MakeFolder(head)

    # Create the directory
    try:
        os.mkdir(path)
        print('Created folder: ', path)
    except OSError as error:
        print(error)


def GetCreationDateFromVideo(file):
    properties = propsys.SHGetPropertyStoreFromParsingName(str(file))
    dt = properties.GetValue(pscon.PKEY_Media_DateEncoded).GetValue()
    dt = ConvertToDateTime(dt)
    return dt


def MakeFoldersForMonths(dir, earliestDate, latestDate):

    # get the first year folder
    year = earliestDate.year

    while year <= latestDate.year:
        # Make a folder for the year
        path = os.path.join(dir, str(year))
        MakeFolder(path)

        if year == earliestDate.year:
            month = earliestDate.month
        else:
            month = 1

        if year == latestDate.year:
            lastMonth = latestDate.month
        else:
            lastMonth = 12

        while(month <= lastMonth):
            path = os.path.join(dir, str(year), str(month))
            MakeFolder(path)
            month = month + 1

        year = year + 1


class FileManager:

    def __init__(self):
        # dictionary of file cluster managers by date
        self.files_by_date = {}

        self.firstDate = datetime.date(2020, 6, 15)
        self.lastDate = datetime.date(1987, 6, 15)

    # Add file directory to one of the date keys
    # TODO prevent a double add
    # Add new FileInformation object to the dictionary
    def Add(self, fileInfo):

        # Check to see if there is already a key in the dictionary
        if (self.ValueExists(fileInfo.DateTime.date())):
            # Add to existing FileClusterManager
            self.files_by_date[fileInfo.DateTime.date()].Add(fileInfo)
        else:
            # Create a new File Cluster Manager
            fcm = FileClusterManager(fileInfo.DateTime.date(), targetDirectory)
            # Add file info to the fcm
            fcm.Add(fileInfo)
            # Add fcm to the dictionary
            self.files_by_date[fileInfo.DateTime.date()] = fcm

        # Update timeframe
        if fileInfo.DateTime.date() > self.lastDate:
            self.lastDate = fileInfo.DateTime.date()
        if fileInfo.DateTime.date() < self.firstDate:
            self.firstDate = fileInfo.DateTime.date()

    # Returns the value associated with a key in the files_by_date dictionary
    def ValueExists(self, date):
        if date in self.files_by_date:
            return self.files_by_date[date]

    # Find File in dictionary and update its last know directory
    def UpdateLastKnownDir(self, fileInfo, newDir):
        if(self.ValueExists(fileInfo.DateTime.date())):
            files = self.files_by_date[fileInfo.DateTime.date()].GetFiles()
            for f in files:
                if f.Name == fileInfo.Name:
                    f.LastDirectoryFound = newDir

    # Delete the entire FileInformationManager entry for the date key
    def DeleteEntry(self, dt):
        del self.files_by_date[dt.date()]

    def FindItemsInDirectory(self, srcDir, extensionList, recursive=True):
        pathList = []
        for ext in extensionList:
            if recursive:
                ext = "**/" + ext
            pathList.extend(Path(srcDir).glob(ext))
        return pathList

    # Get the list of file Information objects on the date key
    def GetFiles(self, date):
        return self.files_by_date[date].GetFiles()

    # Get the number of file directores on a date key
    def NumberOfFilesOnDate(self, date):
        self.files_by_date[date].GetNumber()

    # Get the oldest date key in the dictionary
    def OldestFile(self):
        return self.lastDate

    # Get the first date key in the dictionary
    def NewestFile(self):
        return self.firstDate

    # Add dictionary keys for the rest of the dates in the sequence
    def CompleteCalendarDictionary(self):
        yr = self.firstDate.year

        while(yr <= self.lastDate.year):

            # determine if we are in one of bounding years, we can't exceede the bounds
            if yr == self.firstDate.year:
                month = self.firstDate.month
            else:
                month = 1

            if yr == self.lastDate.year:
                limitMonth = self.lastDate.month
            else:
                limitMonth = 12

            while(month <= limitMonth):
                num_days = calendar.monthrange(yr, month)[1]
                for day in range(1, num_days+1):
                    date = datetime.date(yr, month, day)
                    # start each date off with a zero
                    self.files_by_date[date]
                month = month + 1
            yr = yr + 1

    # Print the dates that don't have any files
    def PrintMissingDates(self):
        self.CompleteCalendarDictionary()
        for date in self.files_by_date:
            if self.NumberOfFilesOnDate(date) == 0:
                print("Missing Video for " + str(date))
        return

    def PrintNumberOfMissingDatesPerYear(self):
        # maybe I should make a function that is an iterator because this requires something similar to the CompleteCalendarFuncation
        # in the example the guy + 1 to the last date, but I'm not sure
        for year in range(self.firstDate.year, self.lastDate.year):
            daysWithFiles = self.GetNumberOfDaysThatHaveFilesInAGivenYear(year)
            daysMissing = 365 - daysWithFiles
            print(str(year) + " has " + str(daysWithFiles) +
                  " days with files. Missing " + str(daysMissing) + " days")
        return

    def PrintNumberOfMissingDatesPerMonth(self, year):
        month = 1
        while month <= 12:
            daysWithFiles = self.GetNumberOfDaysThatHaveFilesInAMonth(
                month, year)

            daysMissing = calendar.monthrange(year, month)[1] - daysWithFiles
            print(str(year) + '-' + str(month) + " has " + str(daysWithFiles) +
                  " days with files. Missing " + str(daysMissing) + " days")
            month = month + 1

        return

    def GetNumberOfDaysThatHaveFilesInAGivenYear(self, year):
        month = 1
        runningCount = 0
        while month <= 12:
            # increment the count
            runningCount = runningCount + \
                self.GetNumberOfDaysThatHaveFilesInAMonth(month, year)
            month = month + 1
        return runningCount

    def GetNumberOfDaysThatHaveFilesInAMonth(self, month, year):
        runningCount = 0
        for dateKey in self.files_by_date:
            if (dateKey.year == year and dateKey.month == month and (self.files_by_date[dateKey].Number()) > 0):
                runningCount = runningCount + 1
        return runningCount

    # TODO
    def TripDetector(self):
        # Analyze missing days and see if there would be available clips in the surrounding days
        return

    def ReevaluateDates(self):
        for entry in self.files_by_date:
            # Update timeframe
            if entry > self.lastDate:
                self.lastDate = entry
            if entry < self.firstDate:
                self.firstDate = entry

    def SavePickleFile(self, directory, fileName):
        fileDir = os.path.join(directory, fileName)
        with open(fileDir, 'wb') as handle:
            pickle.dump(self.files_by_date, handle,
                        protocol=pickle.HIGHEST_PROTOCOL)
        if(os.path.exists(fileDir)):
            print('Dictionary Saved')
        return

    def LoadPickleFile(self, directory, fileName, testFunc):

        fileDir = os.path.join(directory, fileName)

        with open(fileDir, 'rb') as handle:
            self.files_by_date = pickle.load(handle)

        result = testFunc

        return result

    def TestDictionary(self, depth=5):
        # Depth: is how far into the dictionary we should search before validating it
        self.ReevaluateDates()

        pathsChecked = 0
        pathsSuccessful = 0
        for entry in self.files_by_date:
            if (len(self.files_by_date[entry]) >= 0):
                pathsChecked = pathsChecked + 1
                for fileInfo in self.files_by_date[entry].GetFiles():
                    # Make sure that we actually moved the file onto the disk
                    if fileInfo.ExistsInCurrentDir:
                        path = fileInfo.File
                        if(Path.exists(path)):
                            pathsSuccessful = pathsSuccessful + 1
                        if(pathsSuccessful >= depth):
                            print("Test passed on found dictionary")
                            return True
                        if(pathsChecked > depth):
                            return False

    def SaveDictionary(self, directory, fileName):
        self.SavePickleFile(directory, fileName)

    def LoadDictionary(self, directory, fileName):
        return self.LoadPickleFile(directory, fileName, self.TestDictionary)

    def FindExistingDictionary(self, directory):
        pickles = self.FindItemsInDirectory(directory, pickleExtensions, False)

        if len(pickles) > 0:
            # found an existing directory, only use the first one found
            self.LoadDictionary(directory, pickles[0])
            return True

        else:
            return False

    def IndexVideosInDirectory(self, directory):
        # find videos in the directory
        existingVideos = self.FindItemsInDirectory(directory, videoExtensions)

        # add video file to the dictionary
        for vid in existingVideos:
            fileInfo = FileInformation(vid)
            self.Add(fileInfo)

    def DeletePhotosInDirectory(self, directory):
        # find files that are photos
        photoPaths = self.FindItemsInDirectory(directory, photoExtensions)

        # delete files that are photos
        for file in photoPaths:
            print("deleting file")
            file.unlink()

    # A blocking file copy function
    def CopyFileToDir(self, srcDir, dstDir):

        # Make folders if necessary and move files
        if not (os.path.exists(dstDir)):
            MakeFolder(dstDir)

        # copy 2 can have dst to be a directory
        shutil.copy2(srcDir, dstDir)

        historicalSize = -1
        while (historicalSize != os.path.getsize(dstDir)):
            historicalSize = os.path.getsize(dstDir)
            time.sleep(3)
        return True

    # Cut videos from an existing directory and move it to a new target dir
    def CutVideosFromDirectory(self, sourceDir, targetDir):
        # Should we delete videos from the sourceDir if the FileClusterManager is not accepting any more videos

        # Find all the videos in the sourceDir
        videoPaths = self.FindItemsInDirectory(sourceDir, videoExtensions)

        for filePath in videoPaths:

            # Create a new FileInformation object given the path
            fileInfo = FileInformation(filePath)

            # Get the destination path from the FileClusterManager
            if (self.ValueExists(fileInfo.DateTime.date())):
                dstPath = self.files_by_date[fileInfo.DateTime.date(
                )].GetPath()
            else:
                self.Add(fileInfo)
                dstPath = self.files_by_date[fileInfo.DateTime.date(
                )].GetPath()

            # Add the file name to the end of the destination directory
            dstPath_File = os.path.join(dstPath, fileInfo.Name)

            if(self.CopyFileToDir(fileInfo.LastDirectoryFound, dstPath_File)):
               # Confirm that the file has been copied
                if(os.path.exists(dstPath_File)):
                    # Copy was successfuly, update its last known directory
                    self.UpdateLastKnownDir(fileInfo, dstPath_File)
                else:
                    print('Failed to copy file')
                    return False

                # Now that it is added to the dictionary, we can delete it from the old directory
                os.remove(sourceDir)
            else:
                return False
        return True

    # Copy videos from an existing directory and paste it to a new target dir
    def CopyVideosFromDirectory(self, sourceDir, targetDir):
        # Find all the videos in the sourceDir
        videoPaths = self.FindItemsInDirectory(sourceDir, videoExtensions)
        progress = 0
        for filePath in videoPaths:

            # Create a new FileInformation object given the path
            fileInfo = FileInformation(filePath)

            # Get the destination path from the FileClusterManager
            if (self.ValueExists(fileInfo.DateTime.date())):
                dstPath = self.files_by_date[fileInfo.DateTime.date(
                )].GetPath()
            else:
                self.Add(fileInfo)
                dstPath = self.files_by_date[fileInfo.DateTime.date(
                )].GetPath()

            # Add the file name to the end of the destination directory
            dstPath_File = os.path.join(dstPath, fileInfo.Name)

            if(self.CopyFileToDir(fileInfo.LastDirectoryFound, dstPath)):
                # Confirm that the file has been copied
                if(os.path.exists(dstPath_File)):
                    # Copy was successfuly, update its last known directory
                    self.UpdateLastKnownDir(fileInfo, dstPath_File)
                    progress = progress + 1
                    print(str(progress) + ' out of ' + str(len(videoPaths)) + ' files complete')
                else:
                    print('Failed to copy file')
                    return False
            else:
                return False
        return True


def main():

    ref = FileManager()

    if(ref.FindExistingDictionary(targetDirectory)):
        print("Existing Dictionary Found")

        # TODO Decide if we need to update the dictionary by looking at the
        # file modified times of the highest level folders vs the pickle file

    else:

        # Add videos to dictionary that are already in the Target Directory
        ref.IndexVideosInDirectory(targetDirectory)

        if Destructive:
            ref.DeletePhotosInDirectory(sourceDirectory)

            # Add videos to dictionary and then copy them
            ref.CutVideosFromDirectory(sourceDirectory, targetDirectory)

        else:
            # Add videos to dictionary and then delete them
            ref.CopyVideosFromDirectory(sourceDirectory, targetDirectory)

    ref.PrintNumberOfMissingDatesPerMonth(2019)
    ref.SaveDictionary(targetDirectory, dictionaryFilename)


if __name__ == "__main__":
    main()
