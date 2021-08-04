import datetime
import pywintypes
from win32com.propsys import propsys, pscon


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


def GetCreationDateFromVideo(file):
    if(file.exists()):
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
