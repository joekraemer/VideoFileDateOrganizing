#########
# Goals #
#########

# [$] Take a Path input
# [$] Discover the files inside
# [$] If the file is a video look at the date that it was taken
# [$] Document which dates are missing potential videos
# [$] Create folders for years
# [$] Create folders for months that don't exist
# [$] If more than one video exists for a given day, make a folder for that day
# [$] Organize Files by year and month according to date taken
# [$] Put the files in their appropriate month
# [ ] Highlight dates that have a high volume of clips ( most likely trip days,
#     and we can save HDD space by not reviewing those and instead reviewing the vlog)
# [ ] Analyze missing days and see if there would be available clips in the surrounding days
# [$] Delete files that are not video files  ( mostly photos .JPG .raw )
# [ ] Index the files that are all ready organized
# [$] Abstract the file handler as a class
# [ ] Handle duplicate files by deleting them

import os
import glob
import pytz
import datetime
import calendar
import pywintypes
import shutil
from collections import defaultdict
from win32com.propsys import propsys, pscon
from pathlib import Path
import datetime

current_dir_path = os.path.dirname(os.path.realpath(__file__))
videoExtensions = ["*.mp4", "*.mov", "*.MP4", "*.avi", "*.mkv", "*.m4v"]
photoExtensions = ["*.jpg", "*.heic", ".ARW", ".png", ".dng", ".jpeg"]
recursive = False
targetDirectory = 'D:/OneSecond/ToSort'


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
    print(file)
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
    def NumberOfFilesOnDate(self, dt):
        obj = self.files_by_date[dt.date()]
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
            if yr == self.lastDate.year:
                limitMonth = self.lastDate.month
            else:
                month = 1
                limitMonth = 12

            while(month <= limitMonth):
                num_days = calendar.monthrange(yr, month)[1]
                for day in range(1, num_days+1):
                    date = datetime.date(yr, month, day)
                    # start each date off with a zero
                    self.files_by_date[date] = 0
                month = month + 1
            yr = yr + 1

    # Print the dates that don't have any files
    def PrintMissingDates(self):
        self.CompleteCalendarDictionary()
        for date in self.files_by_date:
            if self.NumberOfFilesOnDate(date) == 0:
                print("Missing Video for " + str(date))
        return self


def main():

    ref = Files()

    # paths stores paths objects of files within a given directory with a given ending
    videoPaths = []
    photoPaths = []

    # find files that are photos
    for ext in photoExtensions:
        if recursive:
            ext = "**/" + ext
        photoPaths.extend(Path(targetDirectory).glob(ext))

    # delete files that are photos
    for file in photoPaths:
        print("deleting file")
        file.unlink()

    # digs up the matching video extensions
    for ext in videoExtensions:
        if recursive:
            ext = "**/" + ext
        videoPaths.extend(Path(targetDirectory).glob(ext))

    for file in videoPaths:
        # Get Creation Date
        dt = GetCreationDateFromVideo(file)

        # If it is the second file with that date record
        if(ref.NumberOfFilesOnDate(dt) > 1):
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
        Path.rename(file, newFile)

        ref.Add(file, dt)

    # CompleteCalendarDictionary(firstDate, lastDate)
    # PrintMissingDates(dateRecord)


if __name__ == "__main__":
    main()
