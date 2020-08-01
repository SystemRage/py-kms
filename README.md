# Readme
***

## History
_py-kms_ is a port of node-kms created by [cyrozap](http://forums.mydigitallife.info/members/183074-markedsword), which is a port of either the C#, C++, or .NET implementations of KMS Emulator. The original version was written by [CODYQX4](http://forums.mydigitallife.info/members/89933-CODYQX4) and is derived from the reverse-engineered code of Microsoft's official KMS.

## Features
- Responds to `v4`, `v5`, and `v6` KMS requests.
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
- It's written in Python (tested with Python 3.6.7)

## Dependencies
- Python 3.x.
- Tkinter module (for the GUI).
- If the `tzlocal` module is installed, the "Request Time" in the verbose output will be converted into local time. Otherwise, it will be in UTC.
- It can use the `sqlite3` module so you can use the database function, storing activation data so it can be recalled again.
       
## Usage
- To start the server, execute `python3 pykms_Server.py [IPADDRESS] [PORT]`, the default _IPADDRESS_ is `::` ( all interfaces ) and the default _PORT_ is `1688`. Note that both the address and port are optional. Also note that you have to use an IPv6 address - even if you are just plan to use IPv4 (the kernel maps the incoming IPv4 requests automatically to IPv6), otherwise you will get unsupported address family exceptions!
- To run the client (only for testing purposes), use `python3 pykms_Client.py [IPADDRESS] [PORT]`, with the same defaults of `pykms_Server.py`.
- To show the help pages type: `python3 pykms_Server.py -h` and `python3 pykms_Client.py -h`.

- For launching py-kms GUI make executable `pykms_Server.py` file with `chmod +x /path/to/folder/py-kms/pykms_Server.py`, then simply run `pykms_Server.py` double-clicking.

## Docker
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

## Other Important Stuff
Consult the [Wiki](https://github.com/SystemRage/py-kms/wiki) for more information about activation with _py-kms_ and to get GVLK keys.

## License
   - _py-kms_ is [![License0](https://img.shields.io/badge/license-unlicense-lightgray.svg)](https://github.com/SystemRage/py-kms/blob/master/LICENSE)
   - _py-kms GUI_ is [![License1](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/SystemRage/py-kms/blob/master/LICENSE.gui.md) © Matteo ℱan
