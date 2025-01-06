# Readme
![repo-size](https://img.shields.io/github/repo-size/Py-KMS-Organization/py-kms)
![open-issues](https://img.shields.io/github/issues/Py-KMS-Organization/py-kms)
![last-commit](https://img.shields.io/github/last-commit/Py-KMS-Organization/py-kms/master)
![read-the-docs](https://img.shields.io/readthedocs/py-kms)
***

_Keep in mind that this project is not intended for production use. Feel free to use it to test your own systems or maybe even learn something from the protocol structure. :)_

## History
_py-kms_ is a port of node-kms created by [cyrozap](http://forums.mydigitallife.info/members/183074-markedsword), which is a port of either the C#, C++, or .NET implementations of KMS Emulator. The original version was written by [CODYQX4](http://forums.mydigitallife.info/members/89933-CODYQX4) and is derived from the reverse-engineered code of Microsoft's official KMS.
This version of _py-kms_ is for itself a fork of the original implementation by [SystemRage](https://github.com/SystemRage/py-kms), which was abandoned early 2021.

## Features
- Responds to `v4`, `v5`, and `v6` KMS requests.
- Supports activating:
	- Windows Vista 
	- Windows 7 
	- Windows 8
	- Windows 8.1
	- Windows 10 ( 1511 / 1607 / 1703 / 1709 / 1803 / 1809 )
    - Windows 10 ( 1903 / 1909 / 20H1, 20H2, 21H1, 21H2 )
    - Windows 11 ( 21H2 )
	- Windows Server 2008
	- Windows Server 2008 R2
	- Windows Server 2012
	- Windows Server 2012 R2
	- Windows Server 2016
	- Windows Server 2019
	- Windows Server 2022
	- Windows Server 2025
	- Microsoft Office 2010 ( Volume License )
	- Microsoft Office 2013 ( Volume License )
	- Microsoft Office 2016 ( Volume License )
	- Microsoft Office 2019 ( Volume License )
	- Microsoft Office 2021 ( Volume License )
	- Microsoft Office 2024 ( Volume License )
  - It's written in Python (tested with Python 3.10.1).
  - Supports execution by `Docker`, `systemd` and many more...
  - Uses `sqlite` for persistent data storage (with a simple web-based explorer).

## Documentation
The wiki has been completly reworked and is now available on [readthedocs.io](https://py-kms.readthedocs.io/en/latest/). It should provide you all the necessary information about how to setup and to use _py-kms_ , all without clumping this readme. The documentation also houses more details about activation with _py-kms_ and how to get GVLK keys.
       
## Quick start
- To start the server, execute `python3 pykms_Server.py [IPADDRESS] [PORT]`, the default _IPADDRESS_ is `::` ( all interfaces ) and the default _PORT_ is `1688`. Note that both the address and port are optional. It's allowed to use IPv4 and IPv6 addresses. If you have a IPv6-capable dual-stack OS, a dual-stack socket is created when using a IPv6 address. **In case your OS does not support IPv6, make sure to explicitly specify the legacy IPv4 of `0.0.0.0`!**
- To start the server automatically using Docker, execute `docker run -d --name py-kms --restart always -p 1688:1688 ghcr.io/py-kms-organization/py-kms`.
- To show the help pages type: `python3 pykms_Server.py -h` and `python3 pykms_Client.py -h`.

## License
   - _py-kms_ is [![Unlicense](https://img.shields.io/badge/license-unlicense-lightgray.svg)](./LICENSE)
