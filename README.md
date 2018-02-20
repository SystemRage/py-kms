# History
py-kms is a port of node-kms created by [cyrozap](http://forums.mydigitallife.info/members/183074-markedsword), which is a port of either the C#, C++, or .NET implementations of KMS Emulator. The original version was written by [CODYQX4](http://forums.mydigitallife.info/members/89933-CODYQX4) and is derived from the reverse-engineered code of Microsoft's official KMS.
 
# Features
- Responds to V4, V5, and V6 KMS requests.
- Supports activating:
	- Windows Vista 
	- Windows 7 
	- Windows 8
	- Windows 8.1
	- Windows 10 ( 1511 / 1607 / 1703 / 1709 )
	- Windows Server 2008
	- Windows Server 2008 R2
	- Windows Server 2012
	- Windows Server 2012 R2
	- Windows Server 2016
	- Microsoft Office 2010 ( Volume License )
	- Microsoft Office 2013 ( Volume License )
	- Microsoft Office 2016 ( Volume License )
- It's written in Python:
	- py2-kms tested with Python 2.7.12 
	- py3-kms tested with Python 3.5.2

# Dependencies
- Python 3.x or Python 2.7.x or "Python 2.6.x with the 'argparse' module installed."
- If the "pytz" module is installed, the "Request Time" in the verbose output will be converted into local time. Otherwise, it will be in UTC.
- It can use the "sqlite3" module so you can use the database function. (it stores activation data so it can be recalled again.) (-s)
	- Installation Example on Ubuntu:
		- "sudo apt-get install python-pip"  
		- "sudo pip install pytz"  
		- "sudo apt-get install python-sqlite" or "sudo pip install pysqlite"

# Usage
- To start the server, execute "python server.py [listen_IPADDRESS] [PORT]".
  The default listen_IPADDRESS is "0.0.0.0" ( all interfaces ) and the default PORT is "1688".
- To run the client, use "python client.py server_IPADDRESS [PORT]". The default PORT is "1688".
- To show the help pages type: "python server.py -h" and "python client.py -h"
- To generate a random HWID type: "python randomHWID.py" or directly in the server ( with -w option ) "python server.py -w random"
- To get the HWID from any server use the client, for example type: "python client.py 0.0.0.0 1688 -m Windows81 -v INFO" 
- To generate random EPID type: "python randomPID.py"

# Other Important Stuff
- Read "py-kms_Guide.pdf" for more informations about activation with py-kms.
- File "py-kms_ClientKeys.pdf" contains GVLK keys.

# License
   [![License](https://img.shields.io/badge/license-unlicense-lightgray.svg)](https://github.com/SystemRage/py-kms/blob/master/LICENSE)

