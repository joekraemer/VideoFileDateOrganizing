# Recursively makes folders until the path exists
import os


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
