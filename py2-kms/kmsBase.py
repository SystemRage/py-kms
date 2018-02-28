#!/usr/bin/env python

import binascii
import logging
import datetime
import os
import struct
import sys
import time
import uuid

from structure import Structure
import kmsPidGenerator
import filetimes
from formatText import justify, shell_message

# sqlite3 is optional
try:
	import sqlite3
except:
	pass


class UUID(Structure):
	commonHdr = ()
	structure = (
		('raw', '16s'),
	)

	def get(self):
		return uuid.UUID(bytes_le=str(self))

class kmsBase:
	class kmsRequestStruct(Structure):
		commonHdr = ()
		structure = (
			('versionMinor',            '<H'),
			('versionMajor',            '<H'),
			('isClientVm',              '<I'),
			('licenseStatus',           '<I'),
			('graceTime',               '<I'),
			('applicationId',           ':', UUID),
			('skuId',                   ':', UUID),
			('kmsCountedId' ,           ':', UUID),
			('clientMachineId',         ':', UUID),
			('requiredClientCount',     '<I'),
			('requestTime',             '<Q'),
			('previousClientMachineId', ':', UUID),
			('machineName',             'u'),
			('_mnPad',                  '_-mnPad', '126-len(machineName)'),
			('mnPad',                   ':'),
		)

		def getMachineName(self):
			return self['machineName'].decode('utf-16le')

		def getLicenseStatus(self):
			return kmsBase.licenseStates[self['licenseStatus']] or "Unknown"

	class kmsResponseStruct(Structure):
		commonHdr = ()
		structure = (
			('versionMinor',         '<H'),
			('versionMajor',         '<H'),
			('epidLen',              '<I=len(kmsEpid)+2'),
			('kmsEpid',              'u'),
			('clientMachineId',      ':', UUID),
			('responseTime',         '<Q'),
			('currentClientCount',   '<I'),
			('vLActivationInterval', '<I'),
			('vLRenewalInterval',    '<I'),
		)

	class GenericRequestHeader(Structure):
		commonHdr = ()
		structure = (
			('bodyLength1',  '<I'),
			('bodyLength2',  '<I'),
			('versionMinor', '<H'),
			('versionMajor', '<H'),
			('remainder',    '_'),
		)

	appIds = {
                uuid.UUID("55C92734-D682-4D71-983E-D6EC3F16059F") : "Windows",
                uuid.UUID("59A52881-A989-479D-AF46-F275C6370663") : "Office 14 (2010)",
                uuid.UUID("0FF1CE15-A989-479D-AF46-F275C6370663") : "Office 15 (2013) / Office 16 (2016)"
        }

	skuIds = {
                #########################
                ## Windows Server 2016 ##
                #########################
                uuid.UUID("21c56779-b449-4d20-adfc-eece0e1ad74b") : "Windows Server 2016 Datacenter",
                uuid.UUID("8c1c5410-9f39-4805-8c9d-63a07706358f") : "Windows Server 2016 Standard",
                uuid.UUID("2b5a1b0f-a5ab-4c54-ac2f-a6d94824a283") : "Windows Server 2016 Essentials",
                uuid.UUID("7b4433f4-b1e7-4788-895a-c45378d38253") : "Windows Server 2016 Cloud Storage",
                uuid.UUID("3dbf341b-5f6c-4fa7-b936-699dce9e263f") : "Windows Server 2016 Azure Core",
                ################
                ## Windows 10 ##
                ################
                uuid.UUID("2de67392-b7a7-462a-b1ca-108dd189f588") : "Windows 10 Professional",
                uuid.UUID("a80b5abf-76ad-428b-b05d-a47d2dffeebf") : "Windows 10 Professional N",
                uuid.UUID("3f1afc82-f8ac-4f6c-8005-1d233e606eee") : "Windows 10 Professional Education",
                uuid.UUID("5300b18c-2e33-4dc2-8291-47ffcec746dd") : "Windows 10 Professional Education N",
                uuid.UUID("e0c42288-980c-4788-a014-c080d2e1926e") : "Windows 10 Education",
                uuid.UUID("3c102355-d027-42c6-ad23-2e7ef8a02585") : "Windows 10 Education N",
                uuid.UUID("73111121-5638-40f6-bc11-f1d7b0d64300") : "Windows 10 Enterprise",
                uuid.UUID("e272e3e2-732f-4c65-a8f0-484747d0d947") : "Windows 10 Enterprise N",
                uuid.UUID("7b51a46c-0c04-4e8f-9af4-8496cca90d5e") : "Windows 10 Enterprise 2015 LTSB",
                uuid.UUID("87b838b7-41b6-4590-8318-5797951d8529") : "Windows 10 Enterprise 2015 LTSB N",
                uuid.UUID("2d5a5a60-3040-48bf-beb0-fcd770c20ce0") : "Windows 10 Enterprise 2016 LTSB",
                uuid.UUID("9f776d83-7156-45b2-8a5c-359b9c9f22a3") : "Windows 10 Enterprise 2016 LTSB N", 
                uuid.UUID("58e97c99-f377-4ef1-81d5-4ad5522b5fd8") : "Windows 10 Home / Core",
                uuid.UUID("7b9e1751-a8da-4f75-9560-5fadfe3d8e38") : "Windows 10 Home / Core N",
                uuid.UUID("cd918a57-a41b-4c82-8dce-1a538e221a83") : "Windows 10 Home / Core Single Language",
                uuid.UUID("a9107544-f4a0-4053-a96a-1479abdef912") : "Windows 10 Home / Core Country Specific",
                ############################
                ## Windows Server 2012 R2 ##
                ############################
                uuid.UUID("b3ca044e-a358-4d68-9883-aaa2941aca99") : "Windows Server 2012 R2 Standard",
                uuid.UUID("00091344-1ea4-4f37-b789-01750ba6988c") : "Windows Server 2012 R2 Datacenter",
                uuid.UUID("21db6ba4-9a7b-4a14-9e29-64a60c59301d") : "Windows Server 2012 R2 Essentials",
                uuid.UUID("b743a2be-68d4-4dd3-af32-92425b7bb623") : "Windows Server 2012 R2 Cloud Storage",
                #################
                ## Windows 8.1 ##
                #################
                uuid.UUID("c06b6981-d7fd-4a35-b7b4-054742b7af67") : "Windows 8.1 Professional",
                uuid.UUID("7476d79f-8e48-49b4-ab63-4d0b813a16e4") : "Windows 8.1 Professional N",
                uuid.UUID("096ce63d-4fac-48a9-82a9-61ae9e800e5f") : "Windows 8.1 Professional WMC",
                uuid.UUID("81671aaf-79d1-4eb1-b004-8cbbe173afea") : "Windows 8.1 Enterprise",
                uuid.UUID("113e705c-fa49-48a4-beea-7dd879b46b14") : "Windows 8.1 Enterprise N",
                uuid.UUID("f7e88590-dfc7-4c78-bccb-6f3865b99d1a") : "Windows 8.1 Embedded Industry Automotive",
                uuid.UUID("cd4e2d9f-5059-4a50-a92d-05d5bb1267c7") : "Windows 8.1 Embedded Industry Enterprise",
                uuid.UUID("0ab82d54-47f4-4acb-818c-cc5bf0ecb649") : "Windows 8.1 Embedded Industry Professional",
                uuid.UUID("fe1c3238-432a-43a1-8e25-97e7d1ef10f3") : "Windows 8.1 Core",
                uuid.UUID("78558a64-dc19-43fe-a0d0-8075b2a370a3") : "Windows 8.1 Core N",
                uuid.UUID("c72c6a1d-f252-4e7e-bdd1-3fca342acb35") : "Windows 8.1 Core Single Language",
                uuid.UUID("db78b74f-ef1c-4892-abfe-1e66b8231df6") : "Windows 8.1 Core Country Specific",
                uuid.UUID("ffee456a-cd87-4390-8e07-16146c672fd0") : "Windows 8.1 Core ARM",
                uuid.UUID("e9942b32-2e55-4197-b0bd-5ff58cba8860") : "Windows 8.1 Core Connected",
                uuid.UUID("c6ddecd6-2354-4c19-909b-306a3058484e") : "Windows 8.1 Core Connected N",
                uuid.UUID("ba998212-460a-44db-bfb5-71bf09d1c68b") : "Windows 8.1 Core Connected Country Specific",
                uuid.UUID("b8f5e3a3-ed33-4608-81e1-37d6c9dcfd9c") : "Windows 8.1 Core Connected Single Language",
                uuid.UUID("e58d87b5-8126-4580-80fb-861b22f79296") : "Windows 8.1 Professional Student",
                uuid.UUID("cab491c7-a918-4f60-b502-dab75e334f40") : "Windows 8.1 Professional Student N",
		#########################
                ## Windows Server 2012 ##
                #########################
                uuid.UUID("c04ed6bf-55c8-4b47-9f8e-5a1f31ceee60") : "Windows Server 2012 / Windows 8 Core",
                uuid.UUID("197390a0-65f6-4a95-bdc4-55d58a3b0253") : "Windows Server 2012 N / Windows 8 Core N",
                uuid.UUID("8860fcd4-a77b-4a20-9045-a150ff11d609") : "Windows Server 2012 Single Language / Windows 8 Core Single Language",
                uuid.UUID("9d5584a2-2d85-419a-982c-a00888bb9ddf") : "Windows Server 2012 Country Specific / Windows 8 Core Country Specific",
                uuid.UUID("f0f5ec41-0d55-4732-af02-440a44a3cf0f") : "Windows Server 2012 Standard",
                uuid.UUID("7d5486c7-e120-4771-b7f1-7b56c6d3170c") : "Windows Server 2012 MultiPoint Standard",
                uuid.UUID("95fd1c83-7df5-494a-be8b-1300e1c9d1cd") : "Windows Server 2012 MultiPoint Premium",
                uuid.UUID("d3643d60-0c42-412d-a7d6-52e6635327f6") : "Windows Server 2012 Datacenter",
                #########################
                ## Windows Server 2010 ##
                #########################
                uuid.UUID("f772515c-0e87-48d5-a676-e6962c3e1195") : "Windows MultiPoint Server 2010",
                ###############
                ## Windows 8 ##
                ###############
                uuid.UUID("a98bcd6d-5343-4603-8afe-5908e4611112") : "Windows 8 Professional",
                uuid.UUID("ebf245c1-29a8-4daf-9cb1-38dfc608a8c8") : "Windows 8 Professional N",
                uuid.UUID("a00018a3-f20f-4632-bf7c-8daa5351c914") : "Windows 8 Professional WMC",
                uuid.UUID("458e1bec-837a-45f6-b9d5-925ed5d299de") : "Windows 8 Enterprise",
                uuid.UUID("e14997e7-800a-4cf7-ad10-de4b45b578db") : "Windows 8 Enterprise N",
                uuid.UUID("10018baf-ce21-4060-80bd-47fe74ed4dab") : "Windows 8 Embedded Industry Professional",
                uuid.UUID("18db1848-12e0-4167-b9d7-da7fcda507db") : "Windows 8 Embedded Industry Enterprise",
                uuid.UUID("af35d7b7-5035-4b63-8972-f0b747b9f4dc") : "Windows 8 Core ARM",
                ############################
                ## Windows Server 2008 R2 ##
                ############################
                uuid.UUID("a78b8bd9-8017-4df5-b86a-09f756affa7c") : "Windows Server 2008 R2 Web",
                uuid.UUID("cda18cf3-c196-46ad-b289-60c072869994") : "Windows Server 2008 R2 HPC Edition (Compute Cluster)",
                uuid.UUID("68531fb9-5511-4989-97be-d11a0f55633f") : "Windows Server 2008 R2 Standard",
                uuid.UUID("620e2b3d-09e7-42fd-802a-17a13652fe7a") : "Windows Server 2008 R2 Enterprise",
                uuid.UUID("7482e61b-c589-4b7f-8ecc-46d455ac3b87") : "Windows Server 2008 R2 Datacenter",
                uuid.UUID("8a26851c-1c7e-48d3-a687-fbca9b9ac16b") : "Windows Server 2008 R2 for Itanium-based Systems",
                ###############
                ## Windows 7 ##
                ###############
                uuid.UUID("b92e9980-b9d5-4821-9c94-140f632f6312") : "Windows 7 Professional",
                uuid.UUID("54a09a0d-d57b-4c10-8b69-a842d6590ad5") : "Windows 7 Professional N",
                uuid.UUID("5a041529-fef8-4d07-b06f-b59b573b32d2") : "Windows 7 Professional E",
                uuid.UUID("ae2ee509-1b34-41c0-acb7-6d4650168915") : "Windows 7 Enterprise",
                uuid.UUID("1cb6d605-11b3-4e14-bb30-da91c8e3983a") : "Windows 7 Enterprise N",
                uuid.UUID("46bbed08-9c7b-48fc-a614-95250573f4ea") : "Windows 7 Enterprise E",
                uuid.UUID("db537896-376f-48ae-a492-53d0547773d0") : "Windows 7 Embedded POSReady",
                uuid.UUID("aa6dd3aa-c2b4-40e2-a544-a6bbb3f5c395") : "Windows 7 Embedded ThinPC",
                uuid.UUID("e1a8296a-db37-44d1-8cce-7bc961d59c54") : "Windows 7 Embedded Standard",
                #########################
                ## Windows Server 2008 ##
                #########################
                uuid.UUID("ddfa9f7c-f09e-40b9-8c1a-be877a9a7f4b") : "Windows Server 2008 Web",
                uuid.UUID("ad2542d4-9154-4c6d-8a44-30f11ee96989") : "Windows Server 2008 Standard",
                uuid.UUID("2401e3d0-c50a-4b58-87b2-7e794b7d2607") : "Windows Server 2008 Standard without Hyper-V",
                uuid.UUID("c1af4d90-d1bc-44ca-85d4-003ba33db3b9") : "Windows Server 2008 Enterprise",
                uuid.UUID("8198490a-add0-47b2-b3ba-316b12d647b4") : "Windows Server 2008 Enterprise without Hyper-V",
                uuid.UUID("7afb1156-2c1d-40fc-b260-aab7442b62fe") : "Windows Server 2008 HPC Edition (Compute Cluster)",
                uuid.UUID("68b6e220-cf09-466b-92d3-45cd964b9509") : "Windows Server 2008 Datacenter",
                uuid.UUID("fd09ef77-5647-4eff-809c-af2b64659a45") : "Windows Server 2008 Datacenter without Hyper-V",
                uuid.UUID("01ef176b-3e0d-422a-b4f8-4ea880035e8f") : "Windows Server 2008 for Itanium-based Systems",
                ###################
                ## Windows Vista ##
                ###################
                uuid.UUID("4f3d1606-3fea-4c01-be3c-8d671c401e3b") : "Windows Vista Business",
                uuid.UUID("2c682dc2-8b68-4f63-a165-ae291d4cf138") : "Windows Vista Business N",
                uuid.UUID("cfd8ff08-c0d7-452b-9f60-ef5c70c32094") : "Windows Vista Enterprise",
                uuid.UUID("d4f54950-26f2-4fb4-ba21-ffab16afcade") : "Windows Vista Enterprise N",
                #################
                ## Office 2016 ##
                #################
                uuid.UUID("d450596f-894d-49e0-966a-fd39ed4c4c64") : "Office Professional Plus 2016",
                uuid.UUID("dedfa23d-6ed1-45a6-85dc-63cae0546de6") : "Office Standard 2016",
                uuid.UUID("4f414197-0fc2-4c01-b68a-86cbb9ac254c") : "Office Project Professional 2016",
                uuid.UUID("829b8110-0e6f-4349-bca4-42803577788d") : "Office Project Professional 2016 [Click-to-Run]",
                uuid.UUID("da7ddabc-3fbe-4447-9e01-6ab7440b4cd4") : "Office Project Standard 2016",
                uuid.UUID("cbbaca45-556a-4416-ad03-bda598eaa7c8") : "Office Project Standard 2016 [Click-to-Run]",
                uuid.UUID("6bf301c1-b94a-43e9-ba31-d494598c47fb") : "Office Visio Professional 2016",
                uuid.UUID("b234abe3-0857-4f9c-b05a-4dc314f85557") : "Office Visio Professional 2016 [Click-to-Run]",
                uuid.UUID("aa2a7821-1827-4c2c-8f1d-4513a34dda97") : "Office Visio Standard 2016",
                uuid.UUID("361fe620-64f4-41b5-ba77-84f8e079b1f7") : "Office Visio Standard 2016 [Click-to-Run]",
                uuid.UUID("67c0fc0c-deba-401b-bf8b-9c8ad8395804") : "Office Access 2016",
                uuid.UUID("c3e65d36-141f-4d2f-a303-a842ee756a29") : "Office Excel 2016",
                uuid.UUID("9caabccb-61b1-4b4b-8bec-d10a3c3ac2ce") : "Office Mondo 2016",
                uuid.UUID("e914ea6e-a5fa-4439-a394-a9bb3293ca09") : "Office Mondo Retail 2016",
                uuid.UUID("d8cace59-33d2-4ac7-9b1b-9b72339c51c8") : "Office OneNote 2016",
                uuid.UUID("ec9d9265-9d1e-4ed0-838a-cdc20f2551a1") : "Office Outlook 2016",
                uuid.UUID("d70b1bba-b893-4544-96e2-b7a318091c33") : "Office Powerpoint 2016",
                uuid.UUID("041a06cb-c5b8-4772-809f-416d03d16654") : "Office Publisher 2016",
                uuid.UUID("83e04ee1-fa8d-436d-8994-d31a862cab77") : "Office Skype for Business 2016",
                uuid.UUID("bb11badf-d8aa-470e-9311-20eaf80fe5cc") : "Office Word 2016",
		#################
                ## Office 2013 ##
                #################
                uuid.UUID("87d2b5bf-d47b-41fb-af62-71c382f5cc85") : "Office Professional Plus 2013 [Preview]",
                uuid.UUID("b322da9c-a2e2-4058-9e4e-f59a6970bd69") : "Office Professional Plus 2013",
                uuid.UUID("b13afb38-cd79-4ae5-9f7f-eed058d750ca") : "Office Standard 2013",
                uuid.UUID("3cfe50a9-0e03-4b29-9754-9f193f07b71f") : "Office Project Professional 2013 [Preview]",
                uuid.UUID("4a5d124a-e620-44ba-b6ff-658961b33b9a") : "Office Project Professional 2013",
                uuid.UUID("39e49e57-ae68-4ee3-b098-26480df3da96") : "Office Project Standard 2013 [Preview]",
                uuid.UUID("427a28d1-d17c-4abf-b717-32c780ba6f07") : "Office Project Standard 2013",
                uuid.UUID("cfbfd60e-0b5f-427d-917c-a4df42a80e44") : "Office Visio Professional 2013 [Preview]",
                uuid.UUID("e13ac10e-75d0-4aff-a0cd-764982cf541c") : "Office Visio Professional 2013",
                uuid.UUID("7012cc81-8887-42e9-b17d-4e5e42760f0d") : "Office Visio Standard 2013 [Preview]",
                uuid.UUID("ac4efaf0-f81f-4f61-bdf7-ea32b02ab117") : "Office Visio Standard 2013",
                uuid.UUID("44b538e2-fb34-4732-81e4-644c17d2e746") : "Office Access 2013 [Preview]",
                uuid.UUID("6ee7622c-18d8-4005-9fb7-92db644a279b") : "Office Access 2013",
                uuid.UUID("9373bfa0-97b3-4587-ab73-30934461d55c") : "Office Excel 2013 [Preview]",
                uuid.UUID("f7461d52-7c2b-43b2-8744-ea958e0bd09a") : "Office Excel 2013",
                uuid.UUID("67c0f908-184f-4f64-8250-12db797ab3c3") : "Office OneNote 2013 [Preview]",
                uuid.UUID("efe1f3e6-aea2-4144-a208-32aa872b6545") : "Office OneNote 2013",
                uuid.UUID("7bce4e7a-dd80-4682-98fa-f993725803d2") : "Office Outlook 2013 [Preview]",
                uuid.UUID("771c3afa-50c5-443f-b151-ff2546d863a0") : "Office OutLook 2013",
                uuid.UUID("1ec10c0a-54f6-453e-b85a-6fa1bbfea9b7") : "Office PowerPoint 2013 [Preview]",
                uuid.UUID("8c762649-97d1-4953-ad27-b7e2c25b972e") : "Office PowerPoint 2013",
                uuid.UUID("15aa2117-8f79-49a8-8317-753026d6a054") : "Office Publisher 2013 [Preview]",
                uuid.UUID("00c79ff1-6850-443d-bf61-71cde0de305f") : "Office Publisher 2013",
                uuid.UUID("7ccc8256-fbaa-49c6-b2a9-f5afb4257cd2") : "Office InfoPath 2013 [Preview]",
                uuid.UUID("a30b8040-d68a-423f-b0b5-9ce292ea5a8f") : "Office InfoPath 2013",
                uuid.UUID("c53dfe17-cc00-4967-b188-a088a965494d") : "Office Lync 2013 [Preview]",
                uuid.UUID("1b9f11e3-c85c-4e1b-bb29-879ad2c909e3") : "Office Lync 2013",
                uuid.UUID("de9c7eb6-5a85-420d-9703-fff11bdd4d43") : "Office Word 2013 [Preview]",
                uuid.UUID("d9f5b1c6-5386-495a-88f9-9ad6b41ac9b3") : "Office Word 2013",
                uuid.UUID("2816a87d-e1ed-4097-b311-e2341c57b179") : "Office Mondo 2013 [Preview]",
                uuid.UUID("dc981c6b-fc8e-420f-aa43-f8f33e5c0923") : "Office Mondo 2013",
                uuid.UUID("aa286eb4-556f-4eeb-967c-c1b771b7673e") : "Office SharePoint Workspace (Groove) 2013 [Preview]",
                uuid.UUID("fb4875ec-0c6b-450f-b82b-ab57d8D1677f") : "Office SharePoint Workspace (Groove) 2013",
                ## uuid.UUID("???") : "Office SharePoint Designer (Frontpage) 2013 [Preview]",
                uuid.UUID("ba3e3833-6a7e-445a-89d0-7802a9a68588") : "Office SharePoint Designer (Frontpage) 2013",
                uuid.UUID("1dc00701-03af-4680-b2af-007ffc758a1f") : "Office Mondo Retail 2013",
                #################
                ## Office 2010 ##
                #################
                uuid.UUID("6f327760-8c5c-417c-9b61-836a98287e0c") : "Office Professional Plus 2010",
                uuid.UUID("9da2a678-fb6b-4e67-ab84-60dd6a9c819a") : "Office Standard 2010",
                uuid.UUID("df133ff7-bf14-4f95-afe3-7b48e7e331ef") : "Office Project Professional 2010",
                uuid.UUID("5dc7bf61-5ec9-4996-9ccb-df806a2d0efe") : "Office Project Standard 2010",
                uuid.UUID("e558389c-83c3-4b29-adfe-5e4d7f46c358") : "Office Visio Professional 2010",
                uuid.UUID("9ed833ff-4f92-4f36-b370-8683a4f13275") : "Office Visio Standard 2010",
                uuid.UUID("92236105-bb67-494f-94c7-7f7a607929bd") : "Office Visio Premium 2010",                
                uuid.UUID("8ce7e872-188c-4b98-9d90-f8f90b7aad02") : "Office Access 2010",
                uuid.UUID("cee5d470-6e3b-4fcc-8c2b-d17428568a9f") : "Office Excel 2010",
                uuid.UUID("ab586f5c-5256-4632-962f-fefd8b49e6f4") : "Office OneNote 2010",
                uuid.UUID("ecb7c192-73ab-4ded-acf4-2399b095d0cc") : "Office OutLook 2010",
                uuid.UUID("45593b1d-dfb1-4e91-bbfb-2d5d0ce2227a") : "Office PowerPoint 2010",
                uuid.UUID("b50c4f75-599b-43e8-8dcd-1081a7967241") : "Office Publisher 2010",
                uuid.UUID("ca6b6639-4ad6-40ae-a575-14dee07f6430") : "Office InfoPath 2010",
                uuid.UUID("8947d0b8-c33b-43e1-8c56-9b674c052832") : "Office SharePoint Workspace (Groove) 2010",
                uuid.UUID("2d0882e7-a4e7-423b-8ccc-70d91e0158b1") : "Office Word 2010",
                uuid.UUID("ea509e87-07a1-4a45-9edc-eba5a39f36af") : "Office Small Business Basics 2010",
                uuid.UUID("2745e581-565a-4670-ae90-6bf7c57ffe43") : "Office Starter 2010 Retail",
                ## uuid.UUID("???") : "Office SharePoint Designer (Frontpage) 2010",
                uuid.UUID("09ed9640-f020-400a-acd8-d7d867dfd9c2") : "Office Mondo 1 2010",
                uuid.UUID("ef3d4e49-a53d-4d81-a2b1-2ca6c2556b2c") : "Office Mondo 2 2010",

                ######################
                ## Windows Previews ##
                ######################
                uuid.UUID("a4383e6b-dada-423d-a43d-f25678429676") : "Windows 8.1 Professional (Blue) [Preview]",
                uuid.UUID("631ead72-a8ab-4df8-bbdf-372029989bdd") : "Windows 8.1 ARM [Beta Pre-Release]",
                uuid.UUID("2b9c337f-7a1d-4271-90a3-c6855a2b8a1c") : "Windows 8.1 [Beta Pre-Release]",
                uuid.UUID("ba947c44-d19d-4786-b6ae-22770bc94c54") : "Windows Server 2016 Datacenter [Preview]",
                uuid.UUID("ff808201-fec6-4fd4-ae16-abbddade5706") : "Windows 10 Professional [Pre-Release]",
                uuid.UUID("cf59a07b-1a2a-4be0-bfe0-423b5823e663") : "Windows 8 Professional WMC [RC]",
                
                #################################
                ## A lot of Previews to define ##
                #################################
                uuid.UUID("34260150-69ac-49a3-8a0d-4a403ab55763") : "Windows 10 Professional N [Pre-Release]",
                uuid.UUID("64192251-81b0-4898-ac63-913cc3edf919") : "Windows XX [XX]",
                uuid.UUID("cc17e18a-fa93-43d6-9179-72950a1e931a") : "Windows 10 Professional WMC [Pre-Release]",
                
                uuid.UUID("903663f7-d2ab-49c9-8942-14aa9e0a9c72") : "Windows 10 Home / Core [Pre-Release]",
                uuid.UUID("4dfd543d-caa6-4f69-a95f-5ddfe2b89567") : "Windows 10 Home / Core N [Pre-Release]",
                uuid.UUID("6496e59d-89dc-49eb-a353-09ceb9404845") : "Windows 10 Home / Core [Pre-Release]",
                uuid.UUID("2cc171ef-db48-4adc-af09-7c574b37f139") : "Windows 10 Home / Core Single Language [Pre-Release]",
                uuid.UUID("5fe40dd6-cf1f-4cf2-8729-92121ac2e997") : "Windows 10 Home / Core Country Specific [Pre-Release]",
                
                uuid.UUID("af43f7f0-3b1e-4266-a123-1fdb53f4323b") : "Windows 10 Education [Pre-Release]",
                uuid.UUID("075aca1f-05d7-42e5-a3ce-e349e7be7078") : "Windows 10 Education N [Pre-Release]",
                uuid.UUID("e8ced63e-420d-4ab6-8723-aaf165efb5eb") : "Windows XX Education [Pre-Release]",
                uuid.UUID("3885bca5-11c1-4d4e-9395-df38f7f09a0e") : "Windows XX Education N [Pre-Release]",
                
                uuid.UUID("6ae51eeb-c268-4a21-9aae-df74c38b586d") : "Windows 10 Enterprise N [Pre-Release]",
                uuid.UUID("c23947f3-3f2e-401f-a38c-f38fe0ecb0bd") : "Windows XX Enterprise N [XX]",
                uuid.UUID("38fbe2ac-465a-4ef7-b9d8-72044f2792b6") : "Windows XX Enterprise [XX]",
                uuid.UUID("2cf5af84-abab-4ff0-83f8-f040fb2576eb") : "Windows 10 Enterprise XX LTSB [Pre-Release]",
                uuid.UUID("11a37f09-fb7f-4002-bd84-f3ae71d11e90") : "Windows 10 Enterprise XX LTSB N [Pre-Release]",
                uuid.UUID("75d003b0-dc66-42c0-b3a1-308a3f35741a") : "Windows 10 Enterprise XX LTSB [Pre-Release]",
                uuid.UUID("4e4d5504-e7b1-419c-913d-3c80c15294fc") : "Windows 10 Enterprise XX LTSB N [Pre-Release]",
                uuid.UUID("43f2ab05-7c87-4d56-b27c-44d0f9a3dabd") : "Windows 10 Enterprise [Pre-Release]",
                
                uuid.UUID("b554b49f-4d57-4f08-955e-87886f514d49") : "Windows 10 Core ARM [Pre-Release]",
                uuid.UUID("f18bbe32-16dc-48d4-a27b-5f3966f82513") : "Windows 10 Core Connected N [Pre-Release]",
                uuid.UUID("964a60f6-1505-4ddb-af03-6a9ce6997d3b") : "Windows 10 Core Connected Single Language [Pre-Release]",
                uuid.UUID("b5fe5eaa-14cc-4075-84ae-57c0206d1133") : "Windows 10 Core Connected Country Specific [Pre-Release]",
                uuid.UUID("827a0032-dced-4609-ab6e-16b9d8a40280") : "Windows 10 Core Connected [Pre-Release]",
                
                uuid.UUID("b15187db-11c6-4f13-91ca-8121cebf5b88") : "Windows 10 Professional S [Pre-Release]",
                uuid.UUID("6cdbc9fb-63f5-431b-a5c0-c6f19ae26a9b") : "Windows 10 Professional S N [Pre-Release]",
                uuid.UUID("aa234c15-ee34-4e5f-adb5-73afafb77143") : "Windows XX Professional S [Pre-Release]",
                uuid.UUID("9f6a1bc9-5278-4991-88c9-7301c87a75ea") : "Windows XX Professional S N [Pre-Release]",
                uuid.UUID("49066601-00dc-4d2c-83a8-4343a7b990d1") : "Windows 10 Professional Student [Pre-Release]",
                uuid.UUID("bd64ebf7-d5ec-44c5-ba00-6813441c8c87") : "Windows 10 Professional Student N [Pre-Release]",
                uuid.UUID("5b2add49-b8f4-42e0-a77c-adad4efeeeb1") : "Windows 10 PPIPro [Pre-Release]",

                uuid.UUID("3a9a9414-24bf-4836-866d-ba13a298efb0") : "Windows 8 Core ARM [RC]",
                uuid.UUID("c8cca3ca-bea8-4f6f-87e0-4d050ce8f0a9") : "Windows 8 Embedded Industry Enterprise [TAP-CTP]",
                uuid.UUID("5ca3e488-dbae-4fae-8282-a98fbcd21126") : "Windows 8 Embedded Industry Enterprise [Beta]",

                uuid.UUID("cde952c7-2f96-4d9d-8f2b-2d349f64fc51") : "Windows 8.1 Enterprise [Pre-Release]",
                uuid.UUID("c436def1-0dcc-4849-9a59-8b6142eb70f3") : "Windows 8.1 Core Connected [Pre-Release]",
                uuid.UUID("86f72c8d-8363-4188-b574-1a53cb374711") : "Windows 8.1 Core Connected N [Pre-Release]",
                uuid.UUID("a8651bfb-7fe0-40df-b156-87337ecd5acc") : "Windows 8.1 Core Connected Country Specific [Pre-Release]",
                uuid.UUID("5b120df4-ea3f-4e82-b0c0-6568f719730e") : "Windows 8.1 Core Connected Single Language [Pre-Release]",
                uuid.UUID("fd5ae385-f5cf-4b53-b1fa-1af6fff7c0d8") : "Windows 8.1 Professional Student [Pre-Release]",
                uuid.UUID("687f6358-6a21-453a-a712-3b3b57123827") : "Windows 8.1 Professional Student N [Pre-Release]",
                uuid.UUID("c35a9336-fb02-48db-8f4d-245c17f03667") : "Windows 8.1 Embedded Industry [Beta]",
                uuid.UUID("4daf1e3e-6be9-4848-8f5a-a18a0d2895e1") : "Windows 8.1 Embedded Industry Enterprise [Beta]",
                uuid.UUID("9cc2564c-292e-4d8a-b9f9-1f5007d9409a") : "Windows 8.1 Embedded Industry Automotive [Beta]",
                               
                uuid.UUID("3ddb92aa-332e-46f9-abb7-8bdf62f8d967") : "Windows Longhorn Web Edition [XX]",
                uuid.UUID("7ea4f647-9e67-453b-a7ba-56f7102afde2") : "Windows Longhorn Standard Server [XX]",
                uuid.UUID("5a99526c-1c09-4481-80fb-b60e8b3d99f8") : "Windows Longhorn Enterprise Server [XX]",
                uuid.UUID("8372b47d-5221-41d8-88d0-3f924e50623e") : "Windows Longhorn Computer Cluster [XX]",
                uuid.UUID("932ef1f5-4327-4548-b147-51b0f5502995") : "Windows Longhorn Datacenter Server [XX]",
                uuid.UUID("bebf03b1-a184-4c5e-9103-88af08055e68") : "Windows Longhorn Enterprise Server IA64 [XX]",
                
                uuid.UUID("bfa6b683-56be-47b8-a22e-461b27b9cf11") : "Windows Server XX MultiPoint Standard [XX]",
                uuid.UUID("bc20fb5b-4097-484f-84d2-55b18dac95eb") : "Windows Server XX MultiPoint Premium [XX]",
                uuid.UUID("8a409d61-30fe-4903-bdbc-1fb28603ba3a") : "Windows Server XX Enterprise [XX]",
                uuid.UUID("9dce1f29-bb10-4be0-8027-35b953dd46d5") : "Windows 7 Server Enterprise [XX]",
                uuid.UUID("bf9eda2f-74cc-4ba3-8967-cde30f18c230") : "Windows 7 Server Enterprise IA64 [XX]",
                uuid.UUID("dc06c019-b222-4706-a820-645e77d26a91") : "Windows 7 Server Enterprise without Hyper-V [XX]",
                uuid.UUID("d3872724-5c08-4b1b-91f2-fc9eafed4990") : "Windows XX Server Standard [XX]",
                uuid.UUID("92374131-ed4c-4d1b-846a-32f43c3eb90d") : "Windows 7 Server Standard [XX]",
                uuid.UUID("f963bf4b-9693-46e6-9d9d-09c73eaa2b60") : "Windows 7 Server Standard without Hyper-V [XX]",
                uuid.UUID("e5676f13-9b66-4a1f-8b0c-43490e236202") : "Windows XX Server Web [XX]",
                uuid.UUID("4f4cfa6c-76d8-49f5-9c41-0a57f8af1bbc") : "Windows 7 Server Web [XX]",
                uuid.UUID("0839e017-cfef-4ac6-a97e-ed2ea7962787") : "Windows 7 Server Datacenter without Hyper-V [XX]",
                uuid.UUID("cc64c548-1867-4777-a1cc-0022691bc2a0") : "Windows 7 Server Datacenter [XX]",                
                uuid.UUID("2412bea9-b6e0-441e-8dc2-a13720b42de9") : "Windows XX Server HPC Edition [XX]",
                uuid.UUID("c6e3410d-e48d-41eb-8ca9-848397f46d02") : "Windows Server 2012 N / Windows 8 Core N [RC]",
                uuid.UUID("b148c3f4-6248-4d2f-8c6d-31cce7ae95c3") : "Windows Server 2012 Single Language / Windows 8 Core Single Language [RC]",
                uuid.UUID("c7a8a09a-571c-4ea8-babc-0cbe4d48a89d") : "Windows Server 2012 Country Specific / Windows 8 Core Country Specific [RC]",
                uuid.UUID("8f365ba6-c1b9-4223-98fc-282a0756a3ed") : "Windows Server 2012 R2 Essentials [RTM]",
                uuid.UUID("b995b62c-eae2-40aa-afb9-111889a84ef4") : "Windows XX Server HI [Beta]",
                               
                uuid.UUID("99ff9b26-016a-49d3-982e-fc492f352e57") : "Windows Vista Business [XX]",
                uuid.UUID("90284483-de09-44a2-a406-98957f8dd09d") : "Windows Vista Business [XX]",
                uuid.UUID("af46f56f-f06b-49f0-a420-caa8a8d2bf8c") : "Windows Vista Business N [XX]",
                uuid.UUID("cf67834d-db4a-402c-ab1f-2c134f02b700") : "Windows Vista Enterprise [XX]",
                uuid.UUID("14478aca-ea15-4958-ac34-359281101c99") : "Windows Vista Enterprise [XX]",
                uuid.UUID("0707c7fc-143d-46a4-a830-3705e908202c") : "Windows Vista Enterprise N [XX]",

                uuid.UUID("957ec1e8-97cd-42a8-a091-01a30cf779da") : "Windows 7 Business [XX]",
                uuid.UUID("0ff4e536-a746-4018-b107-e81dd0b6d33a") : "Windows 7 Business N [XX]",
                uuid.UUID("ea77973e-4930-4fa1-a899-02dfaeada1db") : "Windows 7 Enterprise [XX]",
                uuid.UUID("e4ecef68-4372-4740-98e8-6c157cd301c2") : "Windows 7 Enterprise N [XX]",

                uuid.UUID("2a4403df-877f-4046-8271-db6fb6ec54c8") : "Enterprise ProdKey3 Win 9984 DLA/Bypass NQR Test",
                uuid.UUID("38fbe2ac-465a-4ef7-b9d8-72044f2792b6") : "Windows XX Enterprise [XX]",

			
	}

	licenseStates = {
		0 : "Unlicensed",
		1 : "Activated",
		2 : "Grace Period",
		3 : "Out-of-Tolerance Grace Period",
		4 : "Non-Genuine Grace Period",
		5 : "Notifications Mode",
		6 : "Extended Grace Period",
	}

	licenseStatesEnum = {
		'unlicensed' : 0,
		'licensed' : 1,
		'oobGrace' : 2,
		'ootGrace' : 3,
		'nonGenuineGrace' : 4,
		'notification' : 5,
		'extendedGrace' : 6
	}

	errorCodes = {
		'SL_E_VL_NOT_WINDOWS_SLP' : 0xC004F035,
		'SL_E_VL_NOT_ENOUGH_COUNT' : 0xC004F038,
		'SL_E_VL_BINDING_SERVICE_NOT_ENABLED' : 0xC004F039,
		'SL_E_VL_INFO_PRODUCT_USER_RIGHT' : 0x4004F040,
		'SL_I_VL_OOB_NO_BINDING_SERVER_REGISTRATION' : 0x4004F041,
		'SL_E_VL_KEY_MANAGEMENT_SERVICE_ID_MISMATCH' : 0xC004F042,
		'SL_E_VL_MACHINE_NOT_BOUND' : 0xC004F056
	}

	def __init__(self, data, config):
		self.data = data
		self.config = config

	def getConfig(self):
		return self.config

	def getOptions(self):
		return self.config

	def getData(self):
		return self.data

	def getResponse(self):
		return ''

	def getResponsePadding(self, bodyLength):
		if bodyLength % 8 == 0:
			paddingLength = 0
		else:
			paddingLength = 8 - bodyLength % 8
		padding = bytearray(paddingLength)
		return padding

	def serverLogic(self, kmsRequest):
		if self.config['sqlite'] and self.config['dbSupport']:
			self.dbName = 'clients.db'
			if not os.path.isfile(self.dbName):
				# Initialize the database.
				con = None
				try:
					con = sqlite3.connect(self.dbName)
					cur = con.cursor()
					cur.execute("CREATE TABLE clients(clientMachineId TEXT, machineName TEXT, applicationId TEXT, skuId TEXT, licenseStatus TEXT, lastRequestTime INTEGER, kmsEpid TEXT, requestCount INTEGER)")

				except sqlite3.Error, e:
                                        logging.error("%s:" % e.args[0])
					sys.exit(1)

				finally:
					if con:
						con.commit()
						con.close()

		shell_message(nshell = 15)
                logging.debug("KMS Request Bytes: \n%s\n" % justify(binascii.b2a_hex(str(kmsRequest))))
                logging.debug("KMS Request: \n%s\n" % justify(kmsRequest.dump(print_to_stdout = False)))
			
		clientMachineId = kmsRequest['clientMachineId'].get()
		global applicationId 
		applicationId = kmsRequest['applicationId'].get()
		skuId = kmsRequest['skuId'].get()
		requestDatetime = filetimes.filetime_to_dt(kmsRequest['requestTime'])

		# Try and localize the request time, if pytz is available
		try:
			import timezones
			from pytz import utc
			local_dt = utc.localize(requestDatetime).astimezone(timezones.localtz())
		except ImportError:
			local_dt = requestDatetime

		infoDict = {
			"machineName" : kmsRequest.getMachineName(),
			"clientMachineId" : str(clientMachineId),
			"appId" : self.appIds.get(applicationId, str(applicationId)),
			"skuId" : self.skuIds.get(skuId, str(skuId)),
			"licenseStatus" : kmsRequest.getLicenseStatus(),
			"requestTime" : int(time.time()),
			"kmsEpid" : None
		}

		#print infoDict
                logging.info("Machine Name: %s" % infoDict["machineName"])
                logging.info("Client Machine ID: %s" % infoDict["clientMachineId"])
                logging.info("Application ID: %s" % infoDict["appId"])
                logging.info("SKU ID: %s" % infoDict["skuId"])
                logging.info("License Status: %s" % infoDict["licenseStatus"])
                logging.info("Request Time: %s" % local_dt.strftime('%Y-%m-%d %H:%M:%S %Z (UTC%z)'))

		if self.config['sqlite'] and self.config['dbSupport']:
			con = None
			try:
				con = sqlite3.connect(self.dbName)
				cur = con.cursor()
				cur.execute("SELECT * FROM clients WHERE clientMachineId=:clientMachineId;", infoDict)
				try:
					data = cur.fetchone()
					if not data:
						#print "Inserting row..."
						cur.execute("INSERT INTO clients (clientMachineId, machineName, applicationId, skuId, licenseStatus, lastRequestTime, requestCount) VALUES (:clientMachineId, :machineName, :appId, :skuId, :licenseStatus, :requestTime, 1);", infoDict)
					else:
						#print "Data:", data
						if data[1] != infoDict["machineName"]:
							cur.execute("UPDATE clients SET machineName=:machineName WHERE clientMachineId=:clientMachineId;", infoDict)
						if data[2] != infoDict["appId"]:
							cur.execute("UPDATE clients SET applicationId=:appId WHERE clientMachineId=:clientMachineId;", infoDict)
						if data[3] != infoDict["skuId"]:
							cur.execute("UPDATE clients SET skuId=:skuId WHERE clientMachineId=:clientMachineId;", infoDict)
						if data[4] != infoDict["licenseStatus"]:
							cur.execute("UPDATE clients SET licenseStatus=:licenseStatus WHERE clientMachineId=:clientMachineId;", infoDict)
						if data[5] != infoDict["requestTime"]:
							cur.execute("UPDATE clients SET lastRequestTime=:requestTime WHERE clientMachineId=:clientMachineId;", infoDict)
						# Increment requestCount
						cur.execute("UPDATE clients SET requestCount=requestCount+1 WHERE clientMachineId=:clientMachineId;", infoDict)

				except sqlite3.Error, e:
                                        logging.error("%s:" % e.args[0])
					
			except sqlite3.Error, e:
                                logging.error("%s:" % e.args[0])
				sys.exit(1)
			finally:
				if con:
					con.commit()
					con.close()

		return self.createKmsResponse(kmsRequest)

	def createKmsResponse(self, kmsRequest):
		response = self.kmsResponseStruct()
		response['versionMinor'] = kmsRequest['versionMinor']
		response['versionMajor'] = kmsRequest['versionMajor']
		#print " : ", kmsRequest['applicationId'] ----> This line was returning garbage in the pidGenerator
		if not self.config["epid"]:
			response["kmsEpid"] = kmsPidGenerator.epidGenerator(applicationId, kmsRequest['versionMajor'], self.config["lcid"]).encode('utf-16le')
		else:
			response["kmsEpid"] = self.config["epid"].encode('utf-16le')
			
		response['clientMachineId'] = kmsRequest['clientMachineId']
		response['responseTime'] = kmsRequest['requestTime']
		response['currentClientCount'] = self.config["CurrentClientCount"]
		response['vLActivationInterval'] = self.config["VLActivationInterval"]
		response['vLRenewalInterval'] = self.config["VLRenewalInterval"]

		if self.config['sqlite'] and self.config['dbSupport']:
			con = None
			try:
				con = sqlite3.connect(self.dbName)
				cur = con.cursor()
				cur.execute("SELECT * FROM clients WHERE clientMachineId=?;", [str(kmsRequest['clientMachineId'].get())])
				try:
					data = cur.fetchone()
					#print "Data:", data
					if data[6]:
						response["kmsEpid"] = data[6].encode('utf-16le')
					else:
						cur.execute("UPDATE clients SET kmsEpid=? WHERE clientMachineId=?;", (str(response["kmsEpid"].decode('utf-16le')), str(kmsRequest['clientMachineId'].get())))

				except sqlite3.Error, e:
                                        logging.error("%s:" % e.args[0])
					
			except sqlite3.Error, e:
                                logging.error("%s:" % e.args[0])
				sys.exit(1)
			finally:
				if con:
					con.commit()
					con.close()

                logging.info("Server ePID: %s" % response["kmsEpid"].decode('utf-16le').encode('utf-8'))
                        
		return response


import kmsRequestV4, kmsRequestV5, kmsRequestV6, kmsRequestUnknown

def generateKmsResponseData(data, config):
	version = kmsBase.GenericRequestHeader(data)['versionMajor']
	currentDate = datetime.datetime.now().ctime()

	if version == 4:
		logging.info("Received V%d request on %s." % (version, currentDate))
		messagehandler = kmsRequestV4.kmsRequestV4(data, config)
		messagehandler.executeRequestLogic()
	elif version == 5:
		logging.info("Received V%d request on %s." % (version, currentDate))
		messagehandler = kmsRequestV5.kmsRequestV5(data, config)
		messagehandler.executeRequestLogic()
	elif version == 6:
		logging.info("Received V%d request on %s." % (version, currentDate))
		messagehandler = kmsRequestV6.kmsRequestV6(data, config)
		messagehandler.executeRequestLogic()
	else:
		logging.info("Unhandled KMS version V%d." % version)
		messagehandler = kmsRequestUnknown.kmsRequestUnknown(data, config)
		
	return messagehandler.getResponse()
