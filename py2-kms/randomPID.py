#!/usr/bin/env python

import uuid

import kmsPidGenerator

# Variables.
# 1033 (english) is en-us
# 1034 (spanish) is es-es
# 1041 (japanese) is ja
lcid = 1033 

applicationId = uuid.UUID("55C92734-D682-4D71-983E-D6EC3F16059F")  # Windows
applicationId2 = uuid.UUID("0FF1CE15-A989-479D-AF46-F275C6370663") # Office 15 (2013) and Office 16 (2016)
applicationId3 = uuid.UUID("59A52881-A989-479D-AF46-F275C6370663") # Office 14 (2010)

# KMS Version.
# 6 for date starting October 17, 2013
# 5 for date starting September 4, 2012
# 4 for date starting February 16, 2011
versionMajor = 6

# Responses.
response = kmsPidGenerator.epidGenerator(applicationId, versionMajor, lcid)
response2 = kmsPidGenerator.epidGenerator(applicationId2, versionMajor, lcid)
response3 = kmsPidGenerator.epidGenerator(applicationId3, versionMajor, lcid)

print "\nFor Windows:            ", response
print "\nFor Office 2013/2016:   ", response2
print "\nFor Office 2010:        ", response3

#-----------------------------------------------------------------------------
# HWID Section.
import uuid
key = uuid.uuid4().hex
print "\nRandom hwid:            ", key[:16]
print "\n"
