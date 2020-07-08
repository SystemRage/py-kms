# History
_py-kms_ is a port of node-kms created by [cyrozap](http://forums.mydigitallife.info/members/183074-markedsword), which is a port of either the C#, C++, or .NET implementations of KMS Emulator. The original version was written by [CODYQX4](http://forums.mydigitallife.info/members/89933-CODYQX4) and is derived from the reverse-engineered code of Microsoft's official KMS.

# Features
- Responds to V4, V5, and V6 KMS requests.
- Supports activating:
	- Windows Vista 
	- Windows 7 
	- Windows 8
	- Windows 8.1
	- Windows 10 ( 1511 / 1607 / 1703 / 1709 / 1803 / 1809 )
    - Windows 10 ( 1903 / 1909 / 20H1 )
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
	- tested with Python 3.6.7

# Dependencies
- Python 3.x.
- Tkinter module.
- If the `tzlocal` module is installed, the "Request Time" in the verbose output will be converted into local time. Otherwise, it will be in UTC.
- It can use the `sqlite3` module so you can use the database function, storing activation data so it can be recalled again. 
- Installation example on Ubuntu / Mint:
    - `sudo apt-get update`
    - `sudo apt-get install python3-tk python3-pip`
    - `sudo pip3 install tzlocal pysqlite3`
       
# Usage
- To start the server, execute `python3 pykms_Server.py [IPADDRESS] [PORT]`, the default _IPADDRESS_ is `0.0.0.0` or `::` ( all interfaces ) and the default _PORT_ is "1688".
- To run the client (only for testing purposes), use `python3 pykms_Client.py [IPADDRESS] [PORT]`, with the same defaults of `pykms_Server.py`.
- To show the help pages type: `python3 pykms_Server.py -h` and `python3 pykms_Client.py -h`.
- To generate a random HWID use `-w` option: `python3 pykms_Server.py -w RANDOM`.
- To get the HWID from any server use the client, for example type: `python3 pykms_Client.py 0.0.0.0 1688 -m Windows8.1 -V INFO`.

- To change your logfile path use `-F` option, for example: `python3 pykms_Server.py -F /path/to/your/logfile.log -V DEBUG`.
- To view a minimal set of logging information use `-V MINI` option, for example: `python3 pykms_Server.py -F /path/to/your/logfile.log -V MINI`.
- To redirect logging on stdout use `-F STDOUT` option, for example: `python3 pykms_Server.py -F STDOUT -V DEBUG`.
- You can create logfile and view logging information on stdout at the same time with `-F FILESTDOUT` option, for example: `python3 pykms_Server.py -F FILESTDOUT /path/to/your/logfile.log -V DEBUG`.
- With `-F STDOUTOFF` you disable all stdout messages (but a logfile will be created), for example: `python3 pykms_Server.py -F STDOUTOFF /path/to/your/logfile.log -V DEBUG`.
- With `-F FILEOFF` you disable logfile creation.

- Select timeout (seconds) for py-kms with `-t0` option, for example `python3 pykms_Server.py -t0 10`.
- Option `-y` enables printing asynchronously of messages (pretty / logging).
- For launching py-kms GUI make executable `pykms_Server.py` file with `chmod +x /path/to/folder/py-kms/pykms_Server.py`, then simply run `pykms_Server.py` double-clicking.
- You can run py-kms daemonized (via [Etrigan](https://github.com/SystemRage/Etrigan)) using a command like: `python3 pykms_Server.py etrigan start` and stop it with: `python3 pykms_Server.py etrigan stop`.
- With Etrigan you have another way to launch py-kms GUI (specially suitable if you're using a virtualenv), so: `python3 pykms_Server.py etrigan start -g`
and stop the GUI with `python3 pykms_Server.py etrigan stop` (or interact with the EXIT button).

# Docker
![auto-docker](https://img.shields.io/docker/cloud/automated/pykmsorg/py-kms)
![status-docker](https://img.shields.io/docker/cloud/build/pykmsorg/py-kms)
![pulls-docker](https://img.shields.io/docker/pulls/pykmsorg/py-kms)
![size-docker](https://img.shields.io/docker/image-size/pykmsorg/py-kms)

This project has docker image support. You can find all available image configurations inside the docker folder.
There are three tags of the images available:

* `latest`, currently the same like minimal...
* `minimal`, wich is based on the python3 minimal configuration of py-kms. _This image does NOT include SQLLite support!_
* `python3`, which is fully configurable and equiped with SQLLite support and web interface.

If you just want to use the image and don't want to build them yourself, you can use the official image at the docker hub (`pykmsorg/py-kms`).
To ensure that the image is always up-to-date you should check [watchtower](https://github.com/containrrr/watchtower) out!

# Other Important Stuff
Consult the [Wiki](https://github.com/SystemRage/py-kms/wiki) for more information about activation with _py-kms_ and to get GVLK keys.

# License
   - _py-kms_ is [![License0](https://img.shields.io/badge/license-unlicense-lightgray.svg)](https://github.com/SystemRage/py-kms/blob/master/LICENSE)
   - _py-kms GUI_ is [![License1](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/SystemRage/py-kms/blob/master/LICENSE.gui.md) © Matteo ℱan
