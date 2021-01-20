import os

from .metadata import GetCreationDateFromVideo


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
