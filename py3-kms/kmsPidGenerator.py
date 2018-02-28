#!/usr/bin/env python3

import datetime
import random
import time
import uuid

APP_ID_WINDOWS = uuid.UUID("55C92734-D682-4D71-983E-D6EC3F16059F")
APP_ID_OFFICE14 = uuid.UUID("59A52881-A989-479D-AF46-F275C6370663")
APP_ID_OFFICE15 = uuid.UUID("0FF1CE15-A989-479D-AF46-F275C6370663") # also valid for Office 16 (2016). 


# KMS Host OS Type
hostOsList = {}
# Windows Server 2008 R2 SP1
hostOsList["HOST_SERVER2008R2"] = {
        "type" : 55041,
        "osBuild" : 7601
}
# Windows Server 2012 RTM
hostOsList["HOST_SERVER2012"] = {
        "type" : 5426,
        "osBuild" : 9200
}
# Windows Server 2012 R2 RTM
hostOsList["HOST_SERVER2012R2"] = {
        "type" : 6401,
        "osBuild" : 9600
}
# Windows Server 2016 RTM
hostOsList["HOST_SERVER2016"] = {
        "type" : 3612,
        "osBuild" : 14393
}


# Product Specific KeyConfig
pkeyConfigList = {}
# Windows Server KMS Host PID, actual PIDRangeMax = 191999999
pkeyConfigList["windows"] = {
        "GroupID" : 206,
        "PIDRangeMin" : 152000000,
        "PIDRangeMax" : 191999999
}
# Windows Server 2012 R2 KMS Host PID, actual PIDRangeMax = 310999999
pkeyConfigList["windows2012r2"] = {
        "GroupID" : 206,
        "PIDRangeMin" : 271000000,
        "PIDRangeMax" : 310999999
}
# Office 2010 KMSHost Class PID, actual PIDRangeMax = 217999999
pkeyConfigList["office14"] = {
        "GroupID" : 96,
        "PIDRangeMin" : 199000000,
        "PIDRangeMax" : 217999999
}
# Office 2013 KMSHost Class PID, actual PIDRangeMax = 255999999
pkeyConfigList["office15"] = {
        "GroupID" : 206,
        "PIDRangeMin" : 234000000,
        "PIDRangeMax" : 255999999
}


def epidGenerator(appId, version, lcid):
        # Generate Part 1 & 7: Host Type and KMS Server OS Build
        hostOsType = random.choice(list(hostOsList.keys()))  #*2to3*
        hostOsDict = hostOsList[hostOsType]
        
        # Generate Part 2: Group ID and Product Key ID Range
        if appId == APP_ID_OFFICE14:
                keyConfig = pkeyConfigList["office14"]
        elif appId == APP_ID_OFFICE15:
                keyConfig = pkeyConfigList["office15"]
        else:
                # Default to Windows
                if hostOsDict['osBuild'] == 14393:
                        keyConfig = pkeyConfigList["windows2012r2"]
                elif hostOsDict['osBuild'] == 9600:
                        keyConfig = pkeyConfigList["windows2012r2"]
                else:
                        keyConfig = pkeyConfigList["windows"]

        # Generate Part 3 and Part 4: Product Key ID
        productKeyID = random.randint(keyConfig["PIDRangeMin"], keyConfig["PIDRangeMax"])

        # Generate Part 5: License Channel (00=Retail, 01=Retail, 02=OEM,
        # 03=Volume(GVLK,MAK)) - always 03
        licenseChannel = 3

        # Generate Part 6: Language - use system default language
        # 1033 is en-us
        languageCode = lcid # C# CultureInfo.InstalledUICulture.LCID

        # Generate Part 8: KMS Host Activation Date
        # Get Minimum Possible Date: Newer Products first
        if hostOsType == "HOST_SERVER2016":
                # Microsoft Windows Server 2016 RTM
                minTime = datetime.date(2016, 7, 27)
        elif hostOsType == "HOST_SERVER2012R2" or version == 6:
                # Microsoft Windows Server 2012 R2 RTM (October 17, 2013)
                minTime = datetime.date(2013, 10, 17)
        elif appId == APP_ID_OFFICE15:
                # Microsoft Office 2013 RTM (October 24, 2012)
                minTime = datetime.date(2012, 10, 24)
        elif hostOsType == "HOST_SERVER2012" or version == 5:
                # Microsoft Windows Server 2012 RTM (September 4, 2012)
                minTime = datetime.date(2012, 9, 4)
        else:
                # Windows Server 2008 R2 SP1 (February 16, 2011)
                minTime = datetime.date(2011, 2, 16)

        # Generate Year and Day Number
        randomDate = datetime.date.fromtimestamp(random.randint(time.mktime(minTime.timetuple()), time.mktime(datetime.datetime.now().timetuple())))
        firstOfYear = datetime.date(randomDate.year, 1, 1)
        randomDayNumber = int((time.mktime(randomDate.timetuple()) - time.mktime(firstOfYear.timetuple())) / 86400 + 0.5)

        # generate the epid string
        result = []
        result.append(str(hostOsDict["type"]).rjust(5, "0"))
        result.append("-")
        result.append(str(keyConfig["GroupID"]).rjust(5, "0"))
        result.append("-")
        result.append(str(productKeyID // 10**6).rjust(3, "0")) #*2to3*
        result.append("-")
        result.append(str(productKeyID % 10**6).rjust(6, "0"))
        result.append("-")
        result.append(str(licenseChannel).rjust(2, "0"))
        result.append("-")
        result.append(str(languageCode))
        result.append("-")
        result.append(str(hostOsDict["osBuild"]).rjust(4, "0"))
        result.append(".0000-")
        result.append(str(randomDayNumber).rjust(3, "0"))
        result.append(str(randomDate.year).rjust(4, "0"))
        return "".join(result)
