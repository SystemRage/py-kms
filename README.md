# Readme
![repo-size](https://img.shields.io/github/repo-size/SystemRage/py-kms)
![open-issues](https://img.shields.io/github/issues/SystemRage/py-kms)
![last-commit](https://img.shields.io/github/last-commit/SystemRage/py-kms/master)
![docker-status](https://img.shields.io/docker/cloud/build/pykmsorg/py-kms)
![docker-pulls](https://img.shields.io/docker/pulls/pykmsorg/py-kms)
![read-the-docs](https://img.shields.io/readthedocs/py-kms)
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
  - Supports execution by `Docker`, `systemd`, `Upstart` and many more...
  - Includes a GUI for simlpe managing
  - Uses `sqlite` for persistent data storage

## Documentation
The documentation has been completly reworked and is now available on [readthedocs.com](https://py-kms.readthedocs.io/en/latest/Usage.html#start-parameters). It should you provide all necessary information how to get py-kms up
and running using your favourite tools - all without clumping this readme up. The documentation also houses more information about activation with _py-kms_ and to how get GVLK keys.
       
## Get it running (fast)...
- To start the server manually, execute `python3 pykms_Server.py [IPADDRESS] [PORT]`, the default `IPADDRESS` is `::` ( all ipv6-interfaces ) and the default `PORT` is `1688`. Note that both the address and port are optional.
    Also note that it is recommended to use an IPv6 address - even if you are just plan to use IPv4 (the kernel maps the incoming IPv4 requests automatically to IPv6)!
- To start the server automatically using Docker, execute `docker run -d --name py-kms --restart always -p 1688:1688 pykmsorg/py-kms`.
- To show the help pages type: `python3 pykms_Server.py -h` and `python3 pykms_Client.py -h`.
- For launching py-kms GUI make the file `pykms_Server.py` executable with `chmod +x /path/to/folder/py-kms/pykms_Server.py`, then simply run `pykms_Server.py` by double-clicking.

_If you wish to learn more about using py-kms, please refer to the documentation [here](Getting Started.md)!_

## License
   - _py-kms_ is [![Unlicense](https://img.shields.io/badge/license-unlicense-lightgray.svg)](https://github.com/SystemRage/py-kms/blob/master/LICENSE)
   - _py-kms GUI_ is [![MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/SystemRage/py-kms/blob/master/LICENSE.gui.md) © Matteo ℱan
