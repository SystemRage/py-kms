#!/usr/bin/env python

import datetime
import random
import time
import uuid
from ast import literal_eval

from kmsDB2Dict import kmsDB2Dict


def epidGenerator(kmsId, version, lcid):
        kmsdb = kmsDB2Dict()
        winbuilds, csvlkitems, appitems = kmsdb[0], kmsdb[1], kmsdb[2]
        hosts, pkeys = [ [] for _ in range(2) ]

        # Product Specific Detection (Get all CSVLK GroupID and PIDRange good for EPID generation), then
        # Generate Part 2: Group ID and Product Key ID Range
        for csvlkitem in csvlkitems:
                try:
                        if kmsId in [ uuid.UUID(kmsitem) for kmsitem in csvlkitem['Activate'] ]:
                                pkeys.append( (csvlkitem['GroupId'], csvlkitem['MinKeyId'], csvlkitem['MaxKeyId'], csvlkitem['InvalidWinBuild']) )
                except IndexError:
                        # fallback to Windows Server 2019 parameters.
                        GroupId, MinKeyId, MaxKeyId, Invalid = 206, 551000000, 570999999, [0,1,2]
        
        pkey = random.choice(pkeys)
        GroupId, MinKeyId, MaxKeyId, Invalid = int(pkey[0]), int(pkey[1]), int(pkey[2]), literal_eval(pkey[3])

        # Get all KMS Server Host Builds good for EPID generation, then
        # Generate Part 1 & 7: Host Type and KMS Server OS Build
        # https://www.itprotoday.com/windows-78/volume-activation-server-2008
        # https://docs.microsoft.com/en-us/windows-server/get-started-19/activation-19
        # https://docs.microsoft.com/en-us/windows-server/get-started/windows-server-release-info
        # https://support.microsoft.com/en-us/help/13853/windows-lifecycle-fact-sheet
        for winbuild in winbuilds:
                try:
                        # Check versus "InvalidWinBuild".
                        if int(winbuild['WinBuildIndex']) not in Invalid:
                                # Re-check versus "version" protocol.
                                if ((version == 4 and int(winbuild['BuildNumber']) >= 7601) or
                                    (version == 5 and int(winbuild['BuildNumber']) >= 9200) or
                                    (version == 6 and int(winbuild['BuildNumber']) >= 9600)):
                                        hosts.append(winbuild)
                except KeyError:
                        # fallback to Windows Server 2019 parameters.
                        BuildNumber, PlatformId, MinDate = '17763', '3612', '02/10/2018'
                        
        host = random.choice(hosts)
        BuildNumber, PlatformId, MinDate = host['BuildNumber'], host['PlatformId'], host['MinDate']

        # Generate Part 3 and Part 4: Product Key ID
        productKeyID = random.randint(MinKeyId, MaxKeyId)

        # Generate Part 5: License Channel (00=Retail, 01=Retail, 02=OEM, 03=Volume(GVLK,MAK)) - always 03
        licenseChannel = 3

        # Generate Part 6: Language - use system default language, 1033 is en-us
        languageCode = lcid  # (C# CultureInfo.InstalledUICulture.LCID)

        # Generate Part 8: KMS Host Activation Date
        d = datetime.datetime.strptime(MinDate, "%d/%m/%Y")
        minTime = datetime.date(d.year, d.month, d.day)       

        # Generate Year and Day Number
        randomDate = datetime.date.fromtimestamp(random.randint(time.mktime(minTime.timetuple()), time.mktime(datetime.datetime.now().timetuple())))
        firstOfYear = datetime.date(randomDate.year, 1, 1)
        randomDayNumber = int((time.mktime(randomDate.timetuple()) - time.mktime(firstOfYear.timetuple())) / 86400 + 0.5)

        # Generate the EPID string
        result = []
        result.append(str(PlatformId).rjust(5, "0"))
        result.append("-")
        result.append(str(GroupId).rjust(5, "0"))
        result.append("-")
        result.append(str(productKeyID / 1000000).rjust(3, "0"))
        result.append("-")
        result.append(str(productKeyID % 1000000).rjust(6, "0"))
        result.append("-")
        result.append(str(licenseChannel).rjust(2, "0"))
        result.append("-")
        result.append(str(languageCode))
        result.append("-")
        result.append(str(BuildNumber).rjust(4, "0"))
        result.append(".0000-")
        result.append(str(randomDayNumber).rjust(3, "0"))
        result.append(str(randomDate.year).rjust(4, "0"))
        
        return "".join(result)
