import os

from  metadata import GetCreationDateFromVideo, GetEXIF, ReleaseMode, ReleaseMode2, ReleaseMode3


class FileInformation:
    def __init__(self, lastDirFound):
        self.LastDirectoryFound = lastDirFound
        self.ExistsInCurrentDir = True

        # Extract name
        head_tail = os.path.split(lastDirFound)
        self.Name = head_tail[1]

        # Remove ext
        head_tail = os.path.splitext(self.Name)
        self.NameNoExt = head_tail[0]

        # Get Creation Date
        dt = GetCreationDateFromVideo(lastDirFound)
        self.DateTime = dt

        self.Size = os.path.getsize(lastDirFound)
        # Could add other relevent things like metadata or tags

        if False:
            self.EXIF = GetEXIF(lastDirFound)
            self._parse_exif()

    def _parse_exif(self):
        self.ReleaseMode = ReleaseMode(self.EXIF['MakerNotes:ReleaseMode'])
        self.ReleaseMode2 = ReleaseMode2(self.EXIF['MakerNotes:ReleaseMode2'])
        self.ReleaseMode3 = ReleaseMode3(self.EXIF['MakerNotes:ReleaseMode3'])
        self.SequenceNumber = self.EXIF['MakerNotes:SequenceNumber']
        self.SequenceImageNumber = self.EXIF['MakerNotes:SequenceImageNumber']
        self.SequenceLength = self.EXIF['MakerNotes:SequenceLength']

    def _print_exif(self):
        print("Name: " + self.EXIF['File:FileName'])
        print("Mode1: " + str(self.ReleaseMode))
        print("Mode2: " + str(self.ReleaseMode2))
        print("Mode3: " + str(self.ReleaseMode3))
        print("SequenceNumber:" + str(self.SequenceNumber))
        print("SequenceImageNumber:" + str(self.SequenceImageNumber))
        print("SequenceLength:" + str(self.SequenceLength))
        print(" ")

    def is_exposure_bracketing(self):
        if self.ReleaseMode == ReleaseMode.ExposureBracketing:
            return True
