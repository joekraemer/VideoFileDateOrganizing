import os
import glob
import pytz
import datetime
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
targetDirectory = 'E:/SSD/Media/OneSecond'
sourceDirectory = 'E:/SSD/Media/OneSecond/oneplusVideos'
dictionaryFilename = 'dictionary.pickle'

class FileInformation:
    def __init__(self, lastDirFound, name, size):
        self.LastDirectoryFound = lastDirFound
        self.Name = name
        self.Size = size

class BigFileFolderInformation:
    def __init__(self, size, files):
        self.Size = size
        self.Files = files
    
    def Add(self, file):
        self.Files.append(file)


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


def FindItemsInDirectory(sourceDir, extensionList, recursive=True):
    pathList = []
    for ext in extensionList:
        if recursive:
            ext = "**/" + ext
        pathList.extend(Path(sourceDir).glob(ext))
    return pathList


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


class Files:

    def __init__(self):
        # dictionary of file locations by date
        self.files_by_date = defaultdict(list)

        self.firstDate = datetime.date(2020, 6, 15)
        self.lastDate = datetime.date(1987, 6, 15)

    # Add file directory to one of the date keys
    # TODO prevent a double add
        # probably need to document the name of the file?
    def Add(self, file, dt):
        # Update timeframe
        if dt.date() > self.lastDate:
            self.lastDate = dt.date()
        if dt.date() < self.firstDate:
            self.firstDate = dt.date()

        self.files_by_date[dt.date()].append(file)

    # Delete the entire list entry for the date key
    def DeleteEntry(self, dt):
        del self.files_by_date[dt.date()]

    # Get the list of file directories on the date key
    def GetFiles(self, date):
        return self.files_by_date[date]

    # Get the number of file directores on a date key
    def NumberOfFilesOnDate(self, date):
        obj = self.files_by_date[date]
        return len(obj)

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
            if (dateKey.year == year and dateKey.month == month and len(self.files_by_date[dateKey]) > 0):
                runningCount = runningCount + 1
        return runningCount

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

    def SaveDictionary(self, directory, fileName):
        fileDir = os.path.join(directory, fileName)
        with open(fileDir, 'wb') as handle:
            pickle.dump(self.files_by_date, handle,
                        protocol=pickle.HIGHEST_PROTOCOL)
        return

    def TestDictionary(self, depth=5):
        # Depth: is how far into the dictionary we should search before validating it
        self.ReevaluateDates()

        pathsChecked = 0
        pathsSuccessful = 0
        for entry in self.files_by_date:
            if (len(self.files_by_date[entry]) >= 0):
                pathsChecked = pathsChecked + 1
                for path in self.files_by_date[entry]:
                    if(Path.exists(path)):
                        pathsSuccessful = pathsSuccessful + 1
                    if(pathsSuccessful >= depth):
                        print("Test passed on found dictionary")
                        return True
                    if(pathsChecked > depth):
                        return False

    def LoadDictionary(self, directory, fileName):

        fileDir = os.path.join(directory, fileName)

        with open(fileDir, 'rb') as handle:
            self.files_by_date = pickle.load(handle)

        result = self.TestDictionary()
        return result
    



def main():

    ref = Files()

    pickles = FindItemsInDirectory(targetDirectory, pickleExtensions, False)

    if len(pickles) > 0:
        # found an existing directory
        ref.LoadDictionary(targetDirectory, pickles[0])
    else:
        # index the the videos that already exist in the folders
        existingVideos = FindItemsInDirectory(targetDirectory, videoExtensions)

        # add video paths to the dictionary
        for vid in existingVideos:
            dt = GetCreationDateFromVideo(vid)
            ref.Add(vid, dt)

        if Destructive:
            # find files that are photos
            photoPaths = FindItemsInDirectory(sourceDirectory, photoExtensions)

            # delete files that are photos
            for file in photoPaths:
                print("deleting file")
                file.unlink()

        # digs up the matching video extensions
        videoPaths = FindItemsInDirectory(sourceDirectory, videoExtensions)

        for file in videoPaths:
            # Get Creation Date
            dt = GetCreationDateFromVideo(file)

            # If it is the second file with that date record
            if(ref.NumberOfFilesOnDate(dt.date()) > 1):
                pathDestination = os.path.join(
                    targetDirectory, str(dt.year), str(dt.month), str(dt.day))

                # move existing file into this new date
                for files in ref.GetFiles(dt):
                    newFile = os.path.join(pathDestination, files.name)
                    Path.rename(files, newFile)

                    # update file in the dictionary
                    ref.DeleteEntry(dt)
                    ref.Add(newFile, dt)

            else:
                pathDestination = os.path.join(
                    targetDirectory, str(dt.year), str(dt.month))

            # Make folders if necessary and move files
            if not (os.path.exists(pathDestination)):
                MakeFolder(pathDestination)

            # Create the new file path
            newFile = os.path.join(pathDestination, file.name)

            # Move path
            if os.path.exists(newFile):
                if Destructive:
                    # remove video in the sourceDir
                    Path.unlink(file)
            else:
                try:
                    # If the file exists, move it
                    Path.rename(file, newFile)
                except OSError:
                    print('Exception while trying to move file: ', newFile)
                    print('Error: ', OSError)
                else:
                    print('File Moved: ', newFile)

            ref.Add(file, dt)

    ref.PrintNumberOfMissingDatesPerMonth(2019)
    ref.SaveDictionary(targetDirectory, dictionaryFilename)


if __name__ == "__main__":
    main()
