import datetime
import enum

import pywintypes
import exifread
import piexif
import exiftool
from win32com.propsys import propsys, pscon


# Use this website to reference and check the exif information is correct
# https://www.apotelyt.com/camera-exif/exif-data-viewer#fullExif

# Use this website to reference the EXIF information codes
# https://exiftool.org/TagNames/Sony.html


class ReleaseMode(enum.IntEnum):
    Normal = 0
    Continuous = 2
    ExposureBracketing = 5
    WhiteBalanceBracketing = 6
    DROBracketing = 8
    Unknown = 999

    @classmethod
    def _missing_(cls, value):
        return ReleaseMode.Unknown


class ReleaseMode2(enum.IntEnum):
    Normal = 0
    Continuous = 1
    Continuous_ExposureBracketing = 2
    DRO_Bracketing = 3
    Continuous_Burst = 5
    Single_Frame_Capture_During_Move = 6
    Continuous_Sweep_Panorama = 7
    Continuous_Anti_Motion_Blur = 8
    Continuous_HDR = 9
    Continuous_Background_DeFocus = 10
    Continuous_3DSweep_Panorama = 13
    Continuous_HighResolutionSweepPanorama = 15
    Continuous_3DImage = 16
    Continuous_Burst2 = 17
    Normal_iAuto = 18
    Continuous_SpeedAdvancePriority = 19
    Continuous_MultiFrameNR = 20
    SingleFrame_ExposureBracketing = 23
    Continuous_Low = 26
    Continuous_HighSensitivity = 27
    Smile_Shutter = 28
    Continuous_TeleZoom_Advance_Priority = 29
    SingleFrame_MovieCapture = 146
    Unknown = 999

    @classmethod
    def _missing_(cls, value):
        return ReleaseMode2.Unknown


class ReleaseMode3(enum.IntEnum):
    Normal = 0
    Continuous = 1
    Bracketing = 2
    Continuous_Burst = 4
    Continuous_SpeedAdvancePriority = 5
    Normal_SelfTimer = 6
    Single_BurstShooting = 9
    Unknown = 999

    @classmethod
    def _missing_(cls, value):
        return ReleaseMode3.Unknown

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


def GetEXIF(file):
    if (file.exists()):
        with exiftool.ExifTool() as et:
            metadata = et.get_metadata(str(file))

            return metadata
    else:
        print(str(file.name) + 'File does not exist')


def GetCreationDateFromVideo(file):
    if (file.exists()):

        with exiftool.ExifTool() as et:
            metadata = et.get_metadata(str(file))
            MakerNote_ReleaseMode = metadata['MakerNotes:ReleaseMode']
            MakerNote_ReleaseMode2 = metadata['MakerNotes:ReleaseMode2']
            MakerNote_ReleaseMode3 = metadata['MakerNotes:ReleaseMode3']
            MakerNote_SequenceNumber = metadata['MakerNotes:SequenceNumber']
            MakerNote_SequenceImageNumber = metadata['MakerNotes:SequenceImageNumber']
            MakerNote_SequenceLength = metadata['MakerNotes:SequenceLength']

            mode1 = ReleaseMode(MakerNote_ReleaseMode)
            mode2 = ReleaseMode2(MakerNote_ReleaseMode2)
            mode3 = ReleaseMode3(MakerNote_ReleaseMode3)

            print("Name: " + metadata['File:FileName'])
            print("Mode1: " + str(mode1))
            print("Mode2: " + str(mode2))
            print("Mode3: " + str(mode3))
            print("SequenceNumber:" + str(MakerNote_SequenceNumber))
            print("SequenceImageNumber:" + str(MakerNote_SequenceImageNumber))
            print("SequenceLength:" + str(MakerNote_SequenceLength))
            print(" ")

        try:
            properties = propsys.SHGetPropertyStoreFromParsingName(str(file))
            dt = properties.GetValue(pscon.PKEY_Media_DateEncoded).GetValue()
            dt = ConvertToDateTime(dt)
            return dt
        except Exception:
            # print('Not able to extract date with propsys')

            try:
                mtime = datetime.datetime.fromtimestamp(file.stat().st_mtime)
                # print('Sucess with datetime')
                return mtime
            except Exception:
                # print('Not able to extract date with Path.stat()')
                pass
    else:
        print(str(file.name) + 'File does not exist')
