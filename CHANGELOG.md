# Changelog

### py-kms_2020-10-01
- Sql database path customizable.
- Sql database file keeps different AppId.
- Support for multi-address connection.
- Added timeout send / receive.

### py-kms_2020-07-01
- py-kms Gui: now matches all cli options, added modes onlyserver / onlyclient,
  added some animations.
- Added suboptions FILEOFF and STDOUTOFF of -F.
- Created option for asynchronous messages.
- Cleaned options parsing process.

### py-kms_2020-02-02
- Optimized pretty-print messages process.
- Added -F FILESTDOUT option.
- Added deamonization options (via [Etrigan](https://github.com/SystemRage/Etrigan) project).
- py-kms GUI resurrected (and improved).
- Cleaned, cleaned, cleaned.

### py-kms_2019-05-15
- Merging for Python2 / Python3 compatibility all-in-one.
- Added new options: 
    - timeout, [logsize](https://github.com/SystemRage/py-kms/pull/21).
    - more control on logging and info visualization (custom loglevel and stdout logfile redirection) to match [this](https://github.com/SystemRage/py-kms/issues/22) request.
- Setup for multithreading support.
- Graphical improvements:
    - added a (_"really silly"_) tkinter GUI as an alternative to command line.
- [Dockerized](https://github.com/SystemRage/py-kms/pull/20) with sqlite-web. 
- Fixed activation threshold.
- Renamed files, cosmetics and many other little big adjustments.

### py-kms_2018-11-15
 - Implemented some good modifications inspired by [this](https://github.com/ThunderEX/py-kms) other fork.
 	- Clean up code ( deleted no longer useful files randomHWID.py, randomEPID.py, timezones.py;
			erased useless functions and import modules )
	- Reading parameters directly from a slightly modified KmsDataBase.xml ( created with LicenseManager 5.0 by Hotbird64 HGM ) with kmsDB2Dict.py
- Added support for Windows Server 2019 and Office 2019.
- Improved random EPID generation.
- Corrected [this](https://github.com/SystemRage/py-kms/issues/8) in kmsBase.py

### py-kms_2018-03-01
 - *py-kms NOW is for Python3 too ( py3-kms ), the previous one ( written with Python2 ) is renamed py2-kms*
 - *Repaired logging messages*
 - *Added pretty processing messages*
 
### py-kms_2017-06-01
 - *Added option verbose logging in a file*
 - *Updated "kmsBase.py" with new SKUIDs*
 - *Added a brief guide "py-kms-Guide.pdf" ( replaced "client-activation.txt" )*
 - *Added a well formatted and more complete list of volume keys "py-kms-ClientKeys.pdf" ( replaced "client-keys.txt" )*

### py-kms_2016-12-30
 - *Updated kmsBase.py (Matches LicenseManager 4.6.0 by Hotbird64 HGM)*

### py-kms_2016-08-13
 - *Fixed major bug on Response function*
 - *Fixed Random PID Generator (thanks: mkuba50)*

### py-kms_2016-08-12
 - *Added missing UUID, credits: Hotbird64*
 - *Added Windows Server 2016 in random PID generator*
		
### py-kms_2016-08-11
 - *Added Windows Server 2016 UUID*
 - *Fixed GroupID and PIDRange*
 - *Added Office 2016 CountKMSID*
	
### py-kms_2015-07-29
 - *Added Windows 10 UUID*
		
### py-kms_2014-10-13 build 3:
 - *Added Client Activation Examples: "client-activation.txt"*
 - *Added Volume Keys: "client-keys.txt"*

### py-kms_2014-10-13 build 2:
 - *Added missing skuIds in file "kmsbase.py". Thanks (user_hidden)*
	
### py-kms_2014-10-13 build 1:
 - *The server now outputs the hwid in use.*
 - *The server hwid can be random by using parameter: "-w random". Example: "python server.py -w random"*
 - *Included file "randomHWID.py" to generate random hwid on demand.*
 - *Included file "randomPID.py" to generate random epid and hwid on demand.*

### py-kms_2014-03-21T232943Z:
- *The server HWID can now be specified on the command line.*
- *The client will print the HWID when using the v6 protocol.*
	
### py-kms_2014-01-03T032458Z:
 - *Made the sqlite3 module optional.*
 - *Changed the "log" flag to an "sqlite" flag and made a real log flag in preparation for when real request logging is implemented.*

### py-kms_2014-01-03T025524Z:
 - *Added RPC response decoding to the KMS client emulator.*
		
### py-kms_2013-12-30T064443Z:
 - *The v4 hash now uses the proper pre-expanded key.*

### py-kms_2013-12-28T073506Z:
 - *Modified the v4 code to use the custom aes module in order to make it more streamlined and efficient.*

### py-kms_2013-12-20T051257Z:
 - *Removed the need for the pre-computed table (tablecomplex.py) for v4 CMAC calculation, cutting the zip file size in half.*

### py-kms_2013-12-16T214638Z:
 - *Switched to getting the to-be-logged request time from the KMS server instead of the client.*

### py-kms_2013-12-16T030001Z:
 - *You can now specify the CMID and the Machine Name to use with the client emulator.*

### py-kms_2013-12-16T021215Z:
 - *Added a request-logging feature to the server. It stores requests in an SQLite database and uses the ePIDs stored there on a per-CMID basis.*
 - *The client emulator now works for v4, v5, and v6 requests.*
 - *The client emulator now also verifies the KMS v4 responses it receives.*
	
### py-kms_2013-12-14T230215Z
 - *Added a client (work in progress) that right now can only generate and send RPC bind requests.*
 - *Added a bunch of new classes to handle RPC client stuff, but I might just end up moving their functions back into the old classes at some point.*
 - *Lots of other code shuffling.*
 - *Made the verbose and debug option help easier to read.*
 - *Added some server error messages.*

### py-kms_2013-12-08T051332Z:
 - *Made some really huge internal changes to streamline packet parsing.*

### py-kms_2013-12-06T034100Z:
 - *Added tons of new SKU IDs*

### py-kms_2013-12-05T044849Z:
 - *Added Office SKU IDs*
 - *Small internal changes*

### py-kms_2013-12-04T010942Z:
 - *Made the rpcResponseArray in rpcRequest output closer to spec*

### py-kms_2013-12-01T063938Z:
 - *SKUID conversion: Converts the SKUID UUID into a human-readable product version for SKUIDs in its SKUID dictionary.*
 - *Fancy new timezone conversion stuff.*
 - *Enabled setting custom LCIDs.*
 - *Data parsing is now handled by structure.py.*
 - *Some other minor stuff you probably won't notice.*

### py-kms_2013-11-27T061658Z:
 - *Got rid of custom functions module (finally)*

### py-kms_2013-11-27T054744Z:
 - *Simplified custom functions module*
 - *Got rid of "v4" subfolder*
 - *Cleaned up a bunch of code*

### py-kms_2013-11-23T044244Z:
 - *Added timestamps to verbose output*
 - *Made the verbose output look better*

### py-kms_2013-11-21T014002Z:
 - *Moved some stuff into verbose output*
 - *Enabled server ePIDs of arbitrary length*

### py-kms_2013-11-20T180347Z:
 - *Permanently fixed machineName decoding*
 - *Adheres closer to the DCE/RPC protocol spec*
 - *Added client info to program output*
 - *Small formatting changes*

### py-kms_2013-11-13:
 - *First working release added to the Mega folder.*
