import os
import time
import shutil

from fileinformation import FileInformation
from folderfunctions import MakeFolder


class FileClusterManager:
    def __init__(self, date, path, maxOnDiskFiles=13, maxOnDiskSizeGB=4):
        self.Size = 0
        # List of FileInformation Classes
        self.Files = []
        self.FilesExistOffDisk = False
        self.Date = date
        self.MaxOnDiskFiles = maxOnDiskFiles
        self.MaxOnDiskSizes = maxOnDiskSizeGB*(1073741824)

        self.Path = os.path.join(
            path, str(self.Date.year), str(self.Date.month), str(self.Date.day))
        self.ClusterName = str(self.Date)

        # Name of folder when the FCM is instructed to put the files into a folder
        self.ClusterFolderName = str(self.Date.year)

    # TODO: Prevent double adding files. Instead should maybe update the last known location.
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
        self.Size = self.Size + file.Size
        return

    # How many files in this cluster
    def Number(self):
        return len(self.Files)

    def GetFiles(self):
        return self.Files

    # Return the Path that files for this cluster should go to
    def GetPath(self):
        if (self.Number() >= self.MaxOnDiskFiles) or (self.Size >= self.MaxOnDiskSizes):
            self.FilesExistOffDisk = True
            return None

        return self.Path

    # Create a folder with the day
    def CreateClusterFolder(self):
        clusterFolder = os.path.join(self.Path)
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
        shutil.move(str(file), dstDir)

        # Make sure the move is complete
        historicalSize = -1
        while (historicalSize != os.path.getsize(dstDir)):
            historicalSize = os.path.getsize(dstDir)
            time.sleep(1)
        return
