import os
import glob
import pytz
import calendar
import pywintypes
import shutil
import pickle
import datetime
import time
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
from collections import defaultdict
from win32com.propsys import propsys, pscon
from datetime import time as dt_time
from pathlib import Path

current_dir_path = os.path.dirname(os.path.realpath(__file__))
videoExtensions = ["*.mp4", "*.mov", "*.MP4", "*.avi", "*.mkv", "*.m4v"]
photoExtensions = ["*.jpg", "*.heic", "*.ARW", "*.png", "*.dng", "*.jpeg"]
DAYS = ['Sun.', 'Mon.', 'Tues.', 'Wed.', 'Thurs.', 'Fri.', 'Sat.']
MONTHS = ['Jan.', 'Feb.', 'Mar.', 'Apr.', 'May', 'June',
          'July', 'Aug.', 'Sept.', 'Oct.', 'Nov.', 'Dec.']
pickleExtensions = ["*.pickle"]
Destructive = False
targetDirectory = 'E:/SSD\Media/OneSecond/Organized'
sourceDirectory = None
dictionaryFilename = 'OneSecondDictionary.pickle'


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
    def __init__(self, date, path, maxOnDiskFiles=5, maxUnfolderedSize=3, maxOnDiskSizeGB=10):
        self.Size = 0
        # List of FileInformation Classes
        self.Files = []
        self.FilesExistOnDisk = False
        self.Date = date
        self.MaxOnDiskFiles = maxOnDiskFiles
        self.MaxOnDiskSizes = maxOnDiskSizeGB*(1073741824)
        self.MaxUnfolderedSize = maxOnDiskFiles

        self.Path = os.path.join(
            path, str(self.Date.year), str(self.Date.month))
        self.ClusterName = str(self.Date)

        # Name of folder when the FCM is instructed to put the files into a folder
        self.ClusterFolderName = str(self.Date.year)

    # TODO: Prevent double adding files. Instead should maybe update the
    # last known location.
    # Add files to this cluster
    def Add(self, file):
        # See if this file already exists
        for f in self.Files:
            if f.Name == file.Name:
                # file is already in the FCM list, don't add it
                if f.ExistsInCurrentDir:
                    return
                else:
                    # file is not in the cluster folder, so we should update its lastKnownLocation
                    f.LastDirectoryFound = file.LastDirectoryFound
                    # Don't add this file and just return instead
                    return
        # file doesn't exist in this FCM, add it to the list
        self.Files.append(file)
        self.FilesExistOnDisk = True
        self.Size = self.Size + file.Size
        return

    # How many files in this cluster
    def Number(self):
        return len(self.Files)

    def GetFiles(self):
        return self.Files

    # Return the Path that files for this cluster should go to
    def GetPath(self):
        # First, do a check to see if we should create a folder for this cluster
        # Should only create the folder once
        if(self.Number == self.MaxUnfolderedSize):
            self.CreateClusterFolder
            self.MoveFilesToClusterFolder

        if((self.Number == self.MaxOnDiskFiles) or (self.Size >= self.MaxOnDiskSizes)):
            return None

        return self.Path

    # Create a folder with the day
    def CreateClusterFolder(self):
        clusterFolder = os.path.join(self.Path, self.ClusterFolderName)
        # Make sure the folder doesn't already exist
        if not (os.path.isdir(clusterFolder)):
            MakeFolder(clusterFolder)
            self.Path = clusterFolder
        return

    # Move each file associated with this cluster to a new folder
    def MoveFilesToClusterFolder(self):
        for file in self.Files:
            self.MoveFileToNewFolder(file.LastDirectoryFound, self.Path)
        return

    # Move file to a new directory
    def MoveFileToNewFolder(self, file, dstDir):
        shutil.move(file, dstDir)

        # Make sure the move is complete
        historicalSize = -1
        while (historicalSize != os.path.getsize(dstDir)):
            historicalSize = os.path.getsize(dstDir)
            time.sleep(1)
        return


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

# Recursively makes folders until the path exists


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
    if(file.exists()):
        try:
            properties = propsys.SHGetPropertyStoreFromParsingName(str(file))
            dt = properties.GetValue(pscon.PKEY_Media_DateEncoded).GetValue()
            dt = ConvertToDateTime(dt)
            return dt
        except Exception:
            print('Not able to extract date with propsys')

            try:
                mtime = datetime.datetime.fromtimestamp(file.stat().st_mtime)
                print('Sucess with datetime')
                return mtime
            except Exception:
                print('Not able to extract date with Path.stat()')
                pass
    else:
        print(str(file.name) + 'File does not exist')


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


def date_heatmap(series, start=None, end=None, mean=False, ax=None, **kwargs):
    '''Plot a calendar heatmap given a datetime series.

    Arguments:
        series (pd.Series):
            A series of numeric values with a datetime index. Values occurring
            on the same day are combined by sum.
        start (Any):
            The first day to be considered in the plot. The value can be
            anything accepted by :func:`pandas.to_datetime`. The default is the
            earliest date in the data.
        end (Any):
            The last day to be considered in the plot. The value can be
            anything accepted by :func:`pandas.to_datetime`. The default is the
            latest date in the data.
        mean (bool):
            Combine values occurring on the same day by mean instead of sum.
        ax (matplotlib.Axes or None):
            The axes on which to draw the heatmap. The default is the current
            axes in the :module:`~matplotlib.pyplot` API.
        **kwargs:
            Forwarded to :meth:`~matplotlib.Axes.pcolormesh` for drawing the
            heatmap.

    Returns:
        matplotlib.collections.Axes:
            The axes on which the heatmap was drawn. This is set as the current
            axes in the `~matplotlib.pyplot` API.
    '''
    # Combine values occurring on the same day.
    dates = series.index.floor('D')
    group = series.groupby(dates)
    series = group.mean() if mean else group.sum()

    # Parse start/end, defaulting to the min/max of the index.
    start = pd.to_datetime(start or series.index.min())
    end = pd.to_datetime(end or series.index.max())

    # We use [start, end) as a half-open interval below.
    end += np.timedelta64(1, 'D')

    # Get the previous/following Sunday to start/end.
    # Pandas and numpy day-of-week conventions are Monday=0 and Sunday=6.
    start_sun = start - np.timedelta64((start.dayofweek + 1) % 7, 'D')
    end_sun = end + np.timedelta64(7 - end.dayofweek - 1, 'D')

    # Create the heatmap and track ticks.
    num_weeks = (end_sun - start_sun).days // 7
    heatmap = np.zeros((7, num_weeks))
    ticks = {}  # week number -> month name
    for week in range(num_weeks):
        for day in range(7):
            date = start_sun + np.timedelta64(7 * week + day, 'D')
            if date.day == 1:
                ticks[week] = MONTHS[date.month - 1]
            if date.dayofyear == 1:
                ticks[week] += f'\n{date.year}'
            if start <= date < end:
                heatmap[day, week] = series.get(date, 0)

    # Get the coordinates, offset by 0.5 to align the ticks.
    y = np.arange(8) - 0.5
    x = np.arange(num_weeks + 1) - 0.5

    # Plot the heatmap. Prefer pcolormesh over imshow so that the figure can be
    # vectorized when saved to a compatible format. We must invert the axis for
    # pcolormesh, but not for imshow, so that it reads top-bottom, left-right.
    ax = ax or plt.gca()
    mesh = ax.pcolormesh(x, y, heatmap, **kwargs)
    ax.invert_yaxis()

    # Set the ticks.
    ax.set_xticks(list(ticks.keys()))
    ax.set_xticklabels(list(ticks.values()))
    ax.set_yticks(np.arange(7))
    ax.set_yticklabels(DAYS)

    # Set the current image and axes in the pyplot API.
    plt.sca(ax)
    plt.sci(mesh)

    return ax


class FileManager:

    def __init__(self):
        # dictionary of file cluster managers by date
        self.files_by_date = {}

        self.firstDate = datetime.date(2020, 6, 15)
        self.lastDate = datetime.date(1987, 6, 15)
        self.LastTimeUpdated = datetime.datetime(1987, 1, 1)

        # Strictly used for graphing
        self.GraphNumberOfFiles = []
        self.GraphDates = []

    # Add file directory to one of the date keys
    # TODO prevent a double add
    # Add new FileInformation object to the dictionary

    def UpdateLastTimeUpdated(self, dt):
        self.LastTimeUpdated = dt

    def Add(self, fileInfo):

        # Check to see if there is already a key in the dictionary
        if (self.ValueExists(fileInfo.DateTime.date())):

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

    # Iterates through dates within range, defualts to first and last date of dictionary
    def DoSomethingForEverydateInRange(self, callback, firstDt=None, lastDt=None):
        # Handle parameter defaults
        if firstDt == None:
            firstDt = self.firstDate
        if lastDt == None:
            lastDt = self.lastDate

        yr = firstDt.year

        while(yr <= lastDt.year):

            # determine if we are in one of bounding years, we can't exceede the bounds
            if yr == firstDt.year:
                month = firstDt.month
            else:
                month = 1

            if yr == lastDt.year:
                limitMonth = lastDt.month
            else:
                limitMonth = 12

            while(month <= limitMonth):
                num_days = calendar.monthrange(yr, month)[1]
                for day in range(1, num_days+1):
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
        data.index = pd.date_range( startDt, endDt, freq='1D')
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
            time.sleep(1)
        return True

    # Cut videos from an existing directory and move it to a new target dir
    def CutVideosFromDirectory(self, sourceDir, targetDir):
        # Should we delete videos from the sourceDir if the FileClusterManager is not accepting any more videos

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

            if (dstPath == None):
                # Folder is full and file should not be copied

                # Add the file name to the end of the destination directory
                dstPath_File = os.path.join(dstPath, fileInfo.Name)

                if(self.CopyFileToDir(fileInfo.LastDirectoryFound, dstPath_File)):
                    # Confirm that the file has been copied
                    if(os.path.exists(dstPath_File)):
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
                # If there is no FCM, then create one
                self.Add(fileInfo)
                dstPath = self.files_by_date[fileInfo.DateTime.date(
                )].GetPath()

            if (dstPath != None):
                # Folder not is full and file should be copied

                # Add the file name to the end of the destination directory
                dstPath_File = os.path.join(dstPath, fileInfo.Name)

                # See if we can skip the copy
                if not (os.path.isfile(dstPath_File)):
                    if(self.CopyFileToDir(fileInfo.LastDirectoryFound, dstPath)):
                        # Confirm that the file has been copied
                        if(os.path.exists(dstPath_File)):
                            # Copy was successfuly, update its last known directory
                            self.UpdateLastKnownDir(fileInfo, dstPath_File)
                            progress = progress + 1
                            print(str(progress) + ' out of ' +
                                  str(len(videoPaths)) + ' files complete')
                        else:
                            print('Failed to copy file')
                            return False
                    else:
                        return False
                else:
                    print('File Already Exists')
        print(str(progress) + ' files were successfully added')
        return True

    # Last time a directory was modified
    def LastTimeModified(self, dir):

        mTime = os.path.getmtime(dir)
        dt = datetime.datetime.fromtimestamp(mTime)
        return dt

    def date_heatmap_plot(self, firstDt=None, lastDt=None):
        '''An example for `date_heatmap`.

        Most of the sizes here are chosen arbitrarily to look nice with 1yr of
        data. You may need to fiddle with the numbers to look right on other data.
        '''
        # Handle parameter defaults
        if firstDt == None:
            firstDt = self.firstDate
        if lastDt == None:
            lastDt = self.lastDate

        # Major issue will be getting my information into this data structure
        ### Create Pandas Series ###
        self.ResetPandasSeries()
        s1 = self.CreatePandasSeries(firstDt, lastDt)

        # Get some data, a series of values with datetime index.
        # array of length 365 with values from 0 - 5
        # data = np.random.randint(5, size=365)
        # data = pd.Series(data)
        # data.index = pd.date_range(
        #   start='2017-01-01', end='2017-12-31', freq='1D')

        # Create the figure. For the aspect ratio, one year is 7 days by 53 weeks.
        # We widen it further to account for the tick labels and color bar.
        figsize = plt.figaspect(7 / 56)
        fig = plt.figure(figsize=figsize)

        # Plot the heatmap with a color bar.
        ax = date_heatmap(s1, edgecolor='black')
        plt.colorbar(ticks=range(5), pad=0.02)

        # Use a discrete color map with 5 colors (the data ranges from 0 to 4).
        # Extending the color limits by 0.5 aligns the ticks in the color bar.
        cmap = mpl.cm.get_cmap('Blues', 5)
        plt.set_cmap(cmap)
        plt.clim(-0.5, 4.5)

        # Force the cells to be square. If this is set, the size of the color bar
        # may look weird compared to the size of the heatmap. That can be corrected
        # by the aspect ratio of the figure or scale of the color bar.
        ax.set_aspect('equal')

        # Save to a file. For embedding in a LaTeX doc, consider the PDF backend.
        # http://sbillaudelle.de/2015/02/23/seamlessly-embedding-matplotlib-output-into-latex.html
        fig.savefig('heatmapFiles.pdf', bbox_inches='tight')

        # The firgure must be explicitly closed if it was not shown.
        plt.close(fig)


def main():

    ref = FileManager()

    if(ref.FindExistingDictionary(targetDirectory)):
        print("Existing Dictionary Found")

    lstMod = ref.LastTimeModified(targetDirectory)
    lstUpdated = ref.LastTimeUpdated
    if(lstMod > lstUpdated):
        # Add videos to dictionary that are already in the Target Directory
        print('Target Directory Updated, rescanning...')
        # ref.IndexVideosInDirectory(targetDirectory)

    if sourceDirectory != None:
        if Destructive:
            ref.DeletePhotosInDirectory(sourceDirectory)

            # Add videos to dictionary and then copy them
            ref.CutVideosFromDirectory(sourceDirectory, targetDirectory)

        else:
            # Add videos to dictionary and then delete them
            ref.CopyVideosFromDirectory(sourceDirectory, targetDirectory)

    ref.PrintNumberOfMissingDatesPerMonth(2017)
    ref.PrintNumberOfMissingDatesPerMonth(2018)
    ref.PrintNumberOfMissingDatesPerMonth(2019)
    ref.PrintNumberOfMissingDatesPerMonth(2020)
    ref.PrintNumberOfMissingDatesPerYear()

    start = datetime.date(2017, 1, 1)
    end = datetime.date(2018, 12, 31)
    ref.date_heatmap_plot(start, end)

    ref.SaveDictionary(targetDirectory, dictionaryFilename)


if __name__ == "__main__":
    main()
