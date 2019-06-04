# History
_py-kms_ is a port of node-kms created by [cyrozap](http://forums.mydigitallife.info/members/183074-markedsword), which is a port of either the C#, C++, or .NET implementations of KMS Emulator. The original version was written by [CODYQX4](http://forums.mydigitallife.info/members/89933-CODYQX4) and is derived from the reverse-engineered code of Microsoft's official KMS.

# Features
- Responds to V4, V5, and V6 KMS requests.
- Supports activating:
	- Windows Vista 
	- Windows 7 
	- Windows 8
	- Windows 8.1
	- Windows 10 ( 1511 / 1607 / 1703 / 1709 / 1803 / 1809 / 1903 )
	- Windows Server 2008
	- Windows Server 2008 R2
	- Windows Server 2012
	- Windows Server 2012 R2
	- Windows Server 2016
	- Windows Server 2019
	- Microsoft Office 2010 ( Volume License )
	- Microsoft Office 2013 ( Volume License )
	- Microsoft Office 2016 ( Volume License )
	- Microsoft Office 2019 ( Volume License )
- It's written in Python:
	- tested with Python 2.7.15rc1 
	- tested with Python 3.6.7

# Dependencies
- Python 3.x or Python 2.7.x or Python 2.6.x with the ```argparse``` module installed.
- Tkinter module.
- If the ```tzlocal``` module is installed, the "Request Time" in the verbose output will be converted into local time. Otherwise, it will be in UTC.
- It can use the ```sqlite3``` module so you can use the database function, storing activation data so it can be recalled again. 
- Installation example on Ubuntu / Mint:
    - ```sudo apt-get update```
    - for python3
    - ```sudo apt-get install python3-tk python3-pip```
    - ```sudo pip3 install tzlocal pysqlite3```
    - or for python2
    - ```sudo apt-get install python-tk python-pip```
    - ```sudo pip install tzlocal pysqlite```
       
# Usage
- __NOTE__: Pay attention to how invoke scripts, if you want to run with python2 use ```python...``` while for python3 use ```python3...```, also depending on the Python versions that resides in your PC.
- To start the server, execute ```python pykms_Server.py [IPADDRESS] [PORT]```.
  The default _IPADDRESS_ is "0.0.0.0" ( all interfaces ) and the default _PORT_ is "1688".
- To run the client (only for testing purposes), use ```python pykms_Client.py IPADDRESS [PORT]```. 
Argument _IPADDRESS_ is always required, while the default _PORT_ is "1688", so a valid command is: ```python pykms_Client.py 0.0.0.0```
- To show the help pages type: ```python pykms_Server.py -h``` and ```python pykms_Client.py -h```
- To generate a random HWID use ```-w``` option: ```python pykms_Server.py -w RANDOM```
- To get the HWID from any server use the client, for example type: ```python pykms_Client.py 0.0.0.0 1688 -m Windows8.1 -V INFO```
- To view a minimal set of logging information use ```-V MINI``` option, for example: ```python pykms_Server.py -V MINI```
- To redirect logging on stdout use ```-F STDOUT``` option, for example: ```python pykms_Server.py -F STDOUT```
- For launching py-kms GUI make executable all _.py_ files in _py-kms_ directory ```chmod +x /path/to/scripts/py-kms/*.py```, then simply run ```pykms_Server.py``` double-clicking.

# Other Important Stuff
Consult the [Wiki](https://github.com/SystemRage/py-kms/wiki) for more information about activation with _py-kms_ and to get GVLK keys.

# License
   [![License](https://img.shields.io/badge/license-unlicense-lightgray.svg)](https://github.com/SystemRage/py-kms/blob/master/LICENSE)
