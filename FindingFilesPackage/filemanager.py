import datetime
import time
import calendar
import pywintypes
import shutil
import os
import pickle
from pathlib import Path
import pandas as pd

from .fileclustermanager import FileClusterManager
from .fileinformation import FileInformation
from .folderfunctions import MakeFoldersForMonths, MakeFolder
from .plotfiles import date_heatmap_plot


class FileManager:

    def __init__(self, vidExt=["*.mp4", "*.mov", "*.MP4", "*.avi", "*.mkv", "*.m4v"],
                 photoExt=["*.jpg", "*.heic", "*.ARW", "*.png", "*.dng", "*.jpeg"],
                 rawPhotoExt=["*.ARW", "*.dng"]):
        # dictionary of file cluster managers by date
        self.files_by_date = {}

        self.firstDate = datetime.date(2020, 6, 15)
        self.lastDate = datetime.date(1987, 6, 15)
        self.LastTimeUpdated = datetime.datetime(1987, 1, 1)

        self.videoExtensions = vidExt
        self.photoExtensions = photoExt
        self.rawPhotoExtensions = rawPhotoExt
        self.pickleExtensions = ["*.pickle"]

        # Strictly used for graphing
        self.GraphNumberOfFiles = []
        self.GraphDates = []

    # Add file directory to one of the date keys
    # TODO prevent a double add
    # Add new FileInformation object to the dictionary

    def UpdateLastTimeUpdated(self, dt):
        self.LastTimeUpdated = dt

    def Add(self, fileInfo, targetDir):

        # Check to see if there is already a key in the dictionary
        if (self.ValueExists(fileInfo.DateTime.date())):

            self.files_by_date[fileInfo.DateTime.date()].Add(fileInfo)
        else:
            # Create a new File Cluster Manager
            fcm = FileClusterManager(fileInfo.DateTime.date(), targetDir)
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
        if (self.ValueExists(fileInfo.DateTime.date())):
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

    def FindDifferentFormatFilesInDirectory(self, srcDir, fileName, extensionList, recursive=True):
        """Used to find files with the same name but different extensions"""
        name_list = []
        for ext in extensionList:
            new_format = fileName + ext
            name_list.append(new_format)
        return self.FindItemsInDirectory(srcDir, name_list, recursive)

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

        while (yr <= self.lastDate.year):

            # determine if we are in one of bounding years, we can't exceede the bounds
            if yr == self.firstDate.year:
                month = self.firstDate.month
            else:
                month = 1

            if yr == self.lastDate.year:
                limitMonth = self.lastDate.month
            else:
                limitMonth = 12

            while (month <= limitMonth):
                num_days = calendar.monthrange(yr, month)[1]
                for day in range(1, num_days + 1):
                    date = datetime.date(yr, month, day)
                    # start each date off with a zero
                    self.files_by_date[date]
                month = month + 1
            yr = yr + 1

    # Iterates through dates within range, defualts to first and last date of dictionary
    def DoSomethingForEverydateInRange(self, callback, firstDt=None, lastDt=None):
        # Handle parameter defaults
        if firstDt == None:
            firstDt = self.firstDate
        if lastDt == None:
            lastDt = self.lastDate

        yr = firstDt.year

        while (yr <= lastDt.year):

            # determine if we are in one of bounding years, we can't exceede the bounds
            if yr == firstDt.year:
                month = firstDt.month
            else:
                month = 1

            if yr == lastDt.year:
                limitMonth = lastDt.month
            else:
                limitMonth = 12

            while (month <= limitMonth):
                num_days = calendar.monthrange(yr, month)[1]
                for day in range(1, num_days + 1):
                    date = datetime.date(yr, month, day)
                    # Give the callback the date
                    callback(date)

                month = month + 1
            yr = yr + 1

    # create a two lists for Pandas Series given a range
    def CreatePandasSeries(self, startDt, endDt):
        self.DoSomethingForEverydateInRange(
            self.AppendPandasSeries, startDt, endDt)
        data = pd.Series(self.GraphNumberOfFiles)
        data.index = pd.date_range(startDt, endDt, freq='1D')
        return data

    def AppendPandasSeries(self, dt):
        # Unfortunately I have to append this to a class global variable
        # TODO Find a more elegant way to have this callback access function level data

        if (self.ValueExists(dt)):
            self.GraphNumberOfFiles.append(self.files_by_date[dt].Number())
        else:
            self.GraphNumberOfFiles.append(0)

        self.GraphDates.append(dt)

    def ResetPandasSeries(self):
        self.GraphNumberOfFiles.clear()
        self.GraphDates.clear()

    # Print the dates that don't have any files
    def PrintMissingDates(self):
        self.CompleteCalendarDictionary()
        for date in self.files_by_date:
            if self.NumberOfFilesOnDate(date) == 0:
                print("Missing Video for " + str(date))
        return

    def PrintNumberOfMissingDatesPerYear(self, year=0):
        # maybe I should make a function that is an iterator because this requires something similar to the CompleteCalendarFuncation
        # in the example the guy + 1 to the last date, but I'm not sure
        if year == 0:
            for year in range(self.firstDate.year, self.lastDate.year):
                daysWithFiles = self.GetNumberOfDaysThatHaveFilesInAGivenYear(
                    year)
                daysMissing = 365 - daysWithFiles
                print(str(year) + " has " + str(daysWithFiles) +
                      " days with files. Missing " + str(daysMissing) + " days")
            return
        else:
            daysWithFiles = self.GetNumberOfDaysThatHaveFilesInAGivenYear(
                year)
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
        if (os.path.exists(fileDir)):
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
                        if (Path.exists(path)):
                            pathsSuccessful = pathsSuccessful + 1
                        if (pathsSuccessful >= depth):
                            print("Test passed on found dictionary")
                            return True
                        if (pathsChecked > depth):
                            return False

    def SaveDictionary(self, directory, fileName):
        self.SavePickleFile(directory, fileName)

    def LoadDictionary(self, directory, fileName):
        return self.LoadPickleFile(directory, fileName, self.TestDictionary)

    def FindExistingDictionary(self, directory):
        pickles = self.FindItemsInDirectory(
            directory, self.pickleExtensions, False)

        if len(pickles) > 0:
            # found an existing directory, only use the first one found
            self.LoadDictionary(directory, pickles[0])
            return True

        else:
            return False

    def IndexVideosInDirectory(self, directory):
        # find videos in the directory
        existingVideos = self.FindItemsInDirectory(
            directory, self.videoExtensions)

        # add video file to the dictionary
        for vid in existingVideos:
            fileInfo = FileInformation(vid)
            self.Add(fileInfo, directory)

    def DeletePhotosInDirectory(self, directory):
        # find files that are photos
        photoPaths = self.FindItemsInDirectory(directory, self.photoExtensions)

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
            time.sleep(1)
        return True

    # A blocking file cut function
    def CutFileToDir(self, srcDir, dstDir):
        if (self.CopyFileToDir(srcDir, dstDir)):
            # Confirm that the file has been copied
            if (os.path.exists(dstDir)):
                # Copy was successfuly, remove it from its past directory
                os.remove(srcDir)
                return True
            else:
                print('Failed to copy file')
                return False
        else:
            return False
    # Cut videos from an existing directory and move it to a new target dir
    def CutVideosFromDirectory(self, sourceDir, targetDir):
        # Should we delete videos from the sourceDir if the FileClusterManager is not accepting any more videos

        # Find all the videos in the sourceDir
        videoPaths = self.FindItemsInDirectory(sourceDir, self.videoExtensions)
        progress = 0

        for filePath in videoPaths:

            # Create a new FileInformation object given the path
            fileInfo = FileInformation(filePath)

            # Get the destination path from the FileClusterManager
            if (self.ValueExists(fileInfo.DateTime.date())):
                dstPath = self.files_by_date[fileInfo.DateTime.date(
                )].GetPath()
            else:
                self.Add(fileInfo, targetDir)
                dstPath = self.files_by_date[fileInfo.DateTime.date(
                )].GetPath()

            if (dstPath == None):
                # Folder is full and file should not be copied

                # Add the file name to the end of the destination directory
                dstPath_File = os.path.join(dstPath, fileInfo.Name)

                if (self.CopyFileToDir(fileInfo.LastDirectoryFound, dstPath_File)):
                    # Confirm that the file has been copied
                    if (os.path.exists(dstPath_File)):
                        # Copy was successfuly, update its last known directory
                        self.UpdateLastKnownDir(fileInfo, dstPath_File)
                        progress = progress + 1
                        print(str(progress) + ' out of ' +
                              str(len(videoPaths)) + ' files complete')
                    else:
                        print('Failed to copy file')
                        return False

                    # Now that it is added to the dictionary, we can delete it from the old directory
                    os.remove(sourceDir)
                else:
                    return False
        print(str(progress) + 'files were successfully added')
        return True

    # Copy videos from an existing directory and paste it to a new target dir
    def CopyVideosFromDirectory(self, sourceDir, targetDir):

        # Find all the videos in the sourceDir
        videoPaths = self.FindItemsInDirectory(sourceDir, self.videoExtensions)
        progress = 0
        copied = 0
        failedToCopy = []
        addedButNotMoved = 0
        for filePath in videoPaths:

            # Create a new FileInformation object given the path
            fileInfo = FileInformation(filePath)

            # Get the destination path from the FileClusterManager
            if (self.ValueExists(fileInfo.DateTime.date())):
                dstPath = self.files_by_date[fileInfo.DateTime.date(
                )].GetPath()
            else:
                # If there is no FCM, then create one
                self.Add(fileInfo, targetDir)
                dstPath = self.files_by_date[fileInfo.DateTime.date(
                )].GetPath()

            # GetPath returns None if the folder is full
            if (dstPath != None):
                # Folder not is full and file should be copied

                # Add the file name to the end of the destination directory
                dstPath_File = os.path.join(dstPath, fileInfo.Name)

                # See if we can skip the copy
                if not (os.path.isfile(dstPath_File)):
                    if (self.CopyFileToDir(fileInfo.LastDirectoryFound, dstPath)):
                        # Confirm that the file has been copied
                        if (os.path.exists(dstPath_File)):
                            # Copy was successfuly, update its last known directory
                            self.UpdateLastKnownDir(fileInfo, dstPath_File)
                            copied = copied + 1
                            print(str(progress) + ' out of ' +
                                  str(len(videoPaths)) + ' files complete')
                        else:
                            failedToCopy.append(fileInfo.Name)
                            print('Failed to copy file')
                            return False
                    else:
                        failedToCopy.append(fileInfo.Name)
                        print('Failed to copy file')
                        return False
                else:
                    print('File Already Exists')
            else:
                addedButNotMoved = addedButNotMoved + 1

            progress = progress + 1

        print(str(progress) + ' files processed')
        print(str(copied) + ' files copied')
        print(str(addedButNotMoved) + ' files added but not moved')
        print(str(len(failedToCopy)) + ' files failed to copy')
        return True

    def _getMinMaxTimestamp(self, list_of_files):
        """Returns a tuple of the min and max timestamp of a list of files"""


        if len(list_of_files)>0:
            earliest = list_of_files[-1].DateTime
            latest = list_of_files[-1].DateTime

            for file in list_of_files:
                if file.DateTime > latest:
                    latest = file.DateTime
                if file.DateTime < earliest:
                    earliest = file.DateTime

            return earliest, latest
        else:
            return None

    def _withinTimeRange(self, min, max, time, time_range_milliseconds):
        min_buffer = min - datetime.timedelta(milliseconds=time_range_milliseconds)
        max_buffer = max + datetime.timedelta(milliseconds=time_range_milliseconds)

        if time > min_buffer and time < max_buffer:
            return True
        else:
            return False

    # Find corresponding raw files for the jpgs in a folder
    def CopyRAWFilesFromDirectory(self, goodPhotoDir, referenceDir):

        # Find all the videos in the sourceDir
        photoPaths = self.FindItemsInDirectory(goodPhotoDir, self.photoExtensions)
        progress = 0
        copied = 0
        failedToCopy = []
        addedButNotMoved = 0
        for filePath in photoPaths:
            # Create a new FileInformation object given the path
            fileInfo = FileInformation(filePath)

            # Create a new folder in the goodPhotoDir
            dstPath = os.path.join(goodPhotoDir, 'RAWs')

            if (dstPath != None):

                # First find an associated raw files to the good photo
                rawFiles = self.FindDifferentFormatFilesInDirectory(referenceDir, fileInfo.NameNoExt,
                                                                    self.rawPhotoExtensions)

                for raw in rawFiles:

                    rawInfo = FileInformation(raw)

                    # Add the file name to the end of the destination directory
                    dstPath_File = os.path.join(dstPath, rawInfo.Name)

                    # See if we can skip the copy
                    if not (os.path.isfile(dstPath_File)):
                        if self.CopyFileToDir(rawInfo.LastDirectoryFound, dstPath):
                            # Confirm that the file has been copied
                            if os.path.exists(dstPath_File):
                                # Copy was successfully, update its last known directory
                                self.UpdateLastKnownDir(fileInfo, dstPath_File)
                                copied = copied + 1
                                print(str(progress) + ' out of ' +
                                      str(len(photoPaths)) + ' files complete')
                            else:
                                failedToCopy.append(fileInfo.Name)
                                print('Failed to copy file')
                                return False
                        else:
                            failedToCopy.append(fileInfo.Name)
                            print('Failed to copy file')
                            return False
                    else:
                        print('File Already Exists')
            else:
                addedButNotMoved = addedButNotMoved + 1

            progress = progress + 1

        print(str(progress) + ' files processed')
        print(str(copied) + ' files copied')
        print(str(addedButNotMoved) + ' files added but not moved')
        print(str(len(failedToCopy)) + ' files failed to copy')
        return True

    def GroupBurstPhotosInDirectory(self, dir, time_range=500, photo_extensions=["*.jpeg", "*.jpg"]):

        # Find all the photos in the directory
        photoPaths = self.FindItemsInDirectory(dir, photo_extensions)

        file_photo = []
        for filePath in photoPaths:
            # Create a new FileInformation object given the path
            fileInfo = FileInformation(filePath)
            file_photo.append(fileInfo)

        progress = 0
        copied = 0
        failedToCopy = []


        # First Move photos that are from continuous bracket shots
        # for continuous burst, we know how many photos will be in the set
        folder_creation = []
        photos_already_grouped = []
        last_burst_photo_sequence_number = None
        for photo in file_photo:
            if photo.Name not in photos_already_grouped:
                if photo.is_exposure_bracketing():

                    # first of a new sequence (if the last burst was just one photo)
                    if not last_burst_photo_sequence_number or (last_burst_photo_sequence_number == photo.SequenceNumber) or (last_burst_photo_sequence_number > photo.SequenceNumber):
                        folder_creation.append([photo])

                    # next photo in the sequence
                    else:
                        folder_creation[-1].append(photo)

                    last_burst_photo_sequence_number = photo.SequenceNumber
                    photos_already_grouped.append(photo.Name)

                else:
                    # skip this photo for now
                    last_burst_photo_sequence_number = None

        # here I will make a list of lists where each list is
        for photo in file_photo:
            if photo.Name not in photos_already_grouped:
                match_found = False
                # Find if there is a matching list
                for fldr in folder_creation:
                    # protect against zero-length
                    if len(fldr) > 0:
                        # see if the file would fit in the folder
                        min, max = self._getMinMaxTimestamp(fldr)
                        if self._withinTimeRange(min, max, photo.DateTime, time_range):
                            # append photo to the matching list and then continue to the next photo
                            fldr.append(photo)
                            photos_already_grouped.append(photo)
                            match_found = True
                            break

                if not match_found:
                # if no matching folders are found, create a new "folder" ( in this case a list )
                    photos_already_grouped.append(photo.Name)
                    folder_creation.append([photo])

        # create new directories for each of the stacks
        for fldr in folder_creation:
            # don't want to make folders unless there is more than one photo
            if len(fldr) > 1:
                # Create a new folder
                dstPath = os.path.join(dir, str(fldr[-1].NameNoExt))

                # Destructively move the files to the new folder
                for photo in fldr:
                    # Add the file name to the end of the destination directory
                    dstPath_File = os.path.join(dstPath, photo.Name)

                    # See if we can skip the copy
                    if not (os.path.isfile(dstPath_File)):
                        if self.CutFileToDir(photo.LastDirectoryFound, dstPath):
                            # Copy was successfully, update its last known directory
                            self.UpdateLastKnownDir(photo, dstPath_File)
                            copied = copied + 1
                            print(str(progress) + ' out of ' +
                                  str(len(photoPaths)) + ' files complete')
                        else:
                            failedToCopy.append(photo.Name)
                            print('Failed to copy file')
                            return False
                    else:
                        print('File Already Exists')

                    progress = progress + 1

        print(str(progress) + ' files processed')
        print(str(copied) + ' files copied')
        print(str(len(failedToCopy)) + ' files failed to copy')
        return True

    # Last time a directory was modified
    def LastTimeModified(self, dir):

        mTime = os.path.getmtime(dir)
        dt = datetime.datetime.fromtimestamp(mTime)
        return dt

    # Returns the lastest time any one of the highest level folders in a dir were modified
    def OrganizedFoldersLastTimeModified(self, dir):
        dir_list = [f.path for f in os.scandir(dir) if f.is_dir()]

        mostRecent = datetime.datetime(1990, 1, 1)

        for dir in dir_list:
            lastMod = self.LastTimeModified(dir)
            if lastMod > mostRecent:
                mostRecent = lastMod

        return mostRecent

    def PlotHeatMap(self, firstDt=None, lastDt=None):
        # Handle parameter defaults
        if firstDt == None:
            firstDt = self.firstDate
        if lastDt == None:
            lastDt = self.lastDate
        ### Create Pandas Series ###
        self.ResetPandasSeries()
        s1 = self.CreatePandasSeries(firstDt, lastDt)

        date_heatmap_plot(firstDt, lastDt, s1)
        return
