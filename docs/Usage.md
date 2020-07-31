# Usage

## _How to run pykms_Server.py manually_.
***
A Linux user with ```ifconfig``` command can get his KMS IP (Windows users can try ```ipconfig /all```).
```
user@user ~ $ ifconfig
eth0    Link encap: Ethernet HWaddr xx:xx:xx:xx.....
	inet addr: 192.168.1.102 Bcast 192.168.1.255 Mask: 255.255.255.0
	UP BROADCAST RUNNING MULTICAST MTU:1500 Metric:1
	RX Packets: 6 errors: 0 dropped, etc.. 0
	TX packets: 3 errors:0, etc.. 0
	colisions: 0 txqueuelen: 1000
	RX bytes: 1020 TX Bytes: 708

lo      Link encap: Local Loopback
        inet addr: 127.0.0.1 Mask 255.0.0.0
	UP Loopback running MTU: 65536 Metric: 1
	RX packets 4: errors: 0 etc 0
	TX packets 4: errors: 0 etc 0
```
In the example above is 192.168.1.102, so is valid:

```user@user ~/path/to/folder/py-kms $ python3 pykms_Server.py 192.168.1.102 1688```

To stop _pykms_Server.py_, in the same bash window where code running, simply press CTRL+C.
Alternatively, in a new bash window, use ```kill <pid>``` command (you can type ```ps aux``` first and have the process <pid>) or ```killall <name_of_server>```.

## _How to run pykms_Server.py automatically at start_.
***
You can simply manage a daemon that runs as a background process.

If you are running a Linux distro using ```upstart``` (deprecated),
create the file: ```sudo nano /etc/init/py3-kms.conf```,
then add the following (changing where needed) and save:
```
description "py3-kms"
author "SystemRage"
env PYTHONPATH=/usr/bin
env PYKMSPATH=</path/to/your/pykms/files/folder>/py-kms
env LOGPATH=</path/to/your/log/files/folder>/pykms_logserver.log
start on runlevel [2345]
stop on runlevel [016]
exec $PYTHONPATH/python3 $PYKMSPATH/pykms_Server.py 0.0.0.0 1688 -V DEBUG -F $LOGPATH
respawn
```
Check syntax with: ```sudo init-checkconf -d /etc/init/py3-kms.conf```, then
reload upstart to recognise this process: ```sudo initctl reload-configuration```.
Now start the service: ```sudo start py3-kms```, and 
you can see the logfile stating that your daemon is running: ```cat  </path/to/your/log/files/folder>/pykms_logserver.log```.

If you are running a Linux distro using ```systemd```,
create the file: ```sudo nano /etc/systemd/system/py3-kms.service```,
then add the following (changing where needed) and save:
```
[Unit]
Description=py3-kms
After=network.target
StartLimitIntervalSec=0

[Service]
Type=simple
Restart=always
RestartSec=1
KillMode=process
User=root
ExecStart=/usr/bin/python3 </path/to/your/pykms/files/folder>/py-kms/pykms_Server.py 0.0.0.0 1688 -V DEBUG -F </path/to/your/log/files/folder>/pykms_logserver.log

[Install]
WantedBy=multi-user.target
```
Check syntax with: ```sudo systemd-analyze verify py3-kms.service```,
give file permission (if needed): ```sudo chmod 644 /etc/systemd/system/py3-kms.service```,
then reload systemd manager configuration: ```sudo systemctl daemon-reload```,
start daemon: ```sudo systemctl start py3-kms.service``` and view status: ```sudo systemctl status py3-kms.service```.
Check if daemon is correctly running: ```cat  </path/to/your/log/files/folder>/pykms_logserver.log```.

You can also create a daemon with ```SysV``` (obsolete).
Finally a few generic commands useful for interact with your daemon: [here](https://eopio.com/linux-upstart-process-manager/) and [here](https://linoxide.com/linux-how-to/enable-disable-services-ubuntu-systemd-upstart/)

If you are using Windows, to run _pykms_Server.py_ as service you need to install [pywin32](https://sourceforge.net/projects/pywin32/),
then you can create a file for example named _kms-winservice.py_ and put into it this code:
```
import win32serviceutil
import win32service
import win32event
import servicemanager
import socket
import subprocess

class AppServerSvc (win32serviceutil.ServiceFramework):
    _svc_name_ = "py-kms"
    _svc_display_name_ = "py-kms"
    _proc = None
    _cmd = ["C:\Windows\Python27\python.exe", "C:\Windows\Python27\py-kms\pykms_Server.py"]

    def __init__(self,args):
        win32serviceutil.ServiceFramework.__init__(self,args)
        self.hWaitStop = win32event.CreateEvent(None,0,0,None)
        socket.setdefaulttimeout(60)

    def SvcStop(self):
        self.killproc()
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)

    def SvcDoRun(self):
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                              servicemanager.PYS_SERVICE_STARTED,
                              (self._svc_name_,''))
        self.main()

    def main(self):
        self._proc = subprocess.Popen(self._cmd)
        self._proc.wait()

    def killproc(self):
        self._proc.kill()

if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(AppServerSvc)
```
Now in a command prompt type ```C:\Windows\Python27\python.exe kms-winservice.py install``` to install the service.
Display all the services with ```services.msc``` and find the service associated with _py-kms_, changing startup type from "manual" to "auto". 
Finally "Start" the service.
If this approach fails, you can try to use [Non-Sucking Service Manager](https://nssm.cc/) or Task Scheduler as described [here](https://blogs.esri.com/esri/arcgis/2013/07/30/scheduling-a-scrip/).

## _pykms_Server.py Options_.
***
Follows a list of usable parameters:

    ip <IPADDRESS>
> Instructs py-kms to listen on _IPADDRESS_ (can be an hostname too). If this option is not specified, _IPADDRESS_ 0.0.0.0 is used.

    port <PORT>
> Define TCP _PORT_ the KMS service is listening on. Default is 1688.

    -e or --epid <EPID>
> Enhanced Privacy ID (_EPID_) is a cryptographic scheme for providing anonymous signatures.
Use _EPID_ as Windows _EPID_. If no _EPID_ is specified, a random one will be generated.

    -l or --lcid <LCID>
> Do not randomize the locale ID part of the _EPID_ and use _LCID_ instead.
The Language Code Identifier (_LCID_) describes localizable information in Windows.
This structure is used to identify specific languages for the purpose of customizing 
software for particular languages and cultures. For example, it can specify the way dates, 
times, and numbers are formatted as strings. It can also specify paper sizes and preferred sort order based on language elements.
The _LCID_ must be specified as a decimal number (example: 1049 for "Russian - Russia"). 
By default py-kms generates a valid locale ID but this may lead to a value which is unlikely to occur in your country. 
You may want to select the locale ID of your country instead. 
See [here](https://msdn.microsoft.com/en-us/library/cc233982.aspx) for a list of valid _LCIDs_.
If an _EPID_ is manually specified, this setting is ignored. Default is a fixed _LCID_ of 1033 (English - US). 

    -w or --hwid <HWID>
> Use specified _HWID_ for all products. 
Hardware Identification is a security measure used by Microsoft upon the activation of 
the Windows operating system. As part of the Product Activation system, a unique
HWID number is generated when the operating system is first installed. The _HWID_ identifies the hardware components that the system 
is utilizing, and this number is communicated to Microsoft.
Every 10 days and at every reboot the operating system will generate another _HWID_ number and compare it to the original 
to make sure that the operating system is still running on the same device.
If the two _HWID_ numbers differ too much then the operating system will shut down until Microsoft reactivates the product.
The theory behind _HWID_ is to ensure that the operating system is not being used on any device other than the one
for which it was purchased and registered.
HWID must be an 16-character string of hex characters that are interpreted as a series of 8 bytes (big endian). 
Default is _364F463A8863D35F_. To auto generate the _HWID_, type ```-w RANDOM```.

    -c or --client-count <CLIENTCOUNT>
> Use this flag to specify the current _CLIENTCOUNT_. Default is None. Remember that a number >=25 is 
required to enable activation of client OSes while for server OSes and Office >=5.

    -a or --activation-interval <ACTIVATIONINTERVAL>
> Instructs clients to retry activation every _ACTIVATIONINTERVAL_ minutes if it was unsuccessful,
e.g. because it could not reach the server. The default is 120 minutes (2 hours). 

    -r or --renewal-interval <RENEWALINTERVAL>
> Instructs clients to renew activation every _RENEWALINTERVAL_ minutes. The default is 10080 minutes (7 days).

    -s or --sqlite
> Use this option to store request information from unique clients in an SQLite database.

    -t0 or --timeout-idle <TIMEOUT>
> Maximum inactivity time (in seconds) after which the connection with the client is closed. 
Default setting is serve forever (no timeout).

    -y or --async-msg
> With high levels of logging (e.g hundreds of log statements), in a traditional synchronous log model, 
the overhead involved becomes more expensive, so using this option you enable printing (pretty / logging) messages 
asynchronously reducing time-consuming. Desactivated by default.

    -V or --loglevel <{CRITICAL, ERROR, WARNING, INFO, DEBUG, MINI}>
> Use this flag to set a logging loglevel. The default is _ERROR_.
example: 
user@user ~/path/to/folder/py-kms $ ```python3 pykms_Server.py -V INFO```
creates _pykms_logserver.log_ with these initial messages:
  ```
  Mon, 12 Jun 2017 22:09:00 INFO     TCP server listening at 0.0.0.0 on port 1688.
  Mon, 12 Jun 2017 22:09:00 INFO     HWID: 364F463A8863D35F
  ```
    -F or --logfile <LOGFILE>
> Creates a _LOGFILE.log_ logging file. The default is named _pykms_logserver.log_.
example: 
user@user ~/path/to/folder/py-kms $ ```python3 pykms_Server.py 192.168.1.102 8080 -F ~/path/to/folder/py-kms/newlogfile.log -V INFO -w RANDOM```
creates _newlogfile.log_ with these initial messages:
  ```
  Mon, 12 Jun 2017 22:09:00 INFO     TCP server listening at 192.168.1.102 on port 8080.
  Mon, 12 Jun 2017 22:09:00 INFO     HWID: 58C4F4E53AE14224
  ```

  You can also enable other suboptions of ```-F``` doing what is reported in the following table:
  |         command               | pretty msg | logging msg | logfile |
  |-------------------------------|:----------:|:-----------:|:-------:|
  | ```-F <logfile>```            | ON         | OFF         | ON      |
  | ```-F STDOUT```               | OFF        | ON          | OFF     |
  | ```-F FILESTDOUT <logfile>``` | OFF        | ON          | ON      |
  | ```-F STDOUTOFF <logfile>```  | OFF        | OFF         | ON      |
  | ```-F FILEOFF```              | ON         | OFF         | OFF     |

    -S or --logsize <MAXSIZE>
> Use this flag to set a maximum size (in MB) to the output log file. Desactivated by default.

## _pykms_Client.py Options_.
***
If _py-kms_ server doesn't works correctly, you can test it with the KMS client _pykms_Client.py_, 
running on the same machine where you started _pykms_Server.py_. 
For example (in separated bash windows) run these commands:
```
user@user ~/path/to/folder/py-kms $ python3 pykms_Server.py -V DEBUG
user@user ~/path/to/folder/py-kms $ python3 pykms_Client.py 0.0.0.0 1688 -V DEBUG
```
or if you want better specify:
```
user@user ~/path/to/folder/py-kms $ python3 pykms_Server.py <YOUR_IPADDRESS> 1688 -V DEBUG
user@user ~/path/to/folder/py-kms $ python3 pykms_Client.py <YOUR_IPADDRESS> 1688 -V DEBUG
```
You can also put further parameters as defined below:

    ip <IPADDRESS>
> Define _IPADDRESS_ (or hostname) of py-kms' KMS Server. This parameter is always required.

    port <PORT>
> Define TCP _PORT_ the KMS service is listening on. Default is 1688.

    -m or --mode <{WindowsVista, Windows7, Windows8, Windows8.1, Windows10, Office2010, Office2013, Office2016, Office2019}>
> Use this flag to manually specify a Microsoft _PRODUCTNAME_ for testing the KMS server. Default is Windows8.1.

   -c or --cmid <CMID>
> Use this flag to manually specify a CMID to use. If no CMID is specified, a random one will be generated.
The Microsoft KMS host machine identifies KMS clients with a unique Client Machine ID 
(CMID,   example: ae3a27d1-b73a-4734-9878-70c949815218). For a KMS client to successfully activate, the KMS server 
needs to meet a threshold, which is a minimum count for KMS clients.
Once a KMS server records a count which meets or exceeds threshold, KMS clients will begin to activate successfully.
Each unique CMID recorded by KMS server adds towards the count threshold for KMS clients. This are retained by the KMS server 
for a maximum of 30 days after the last activation request with that CMID. Note that duplicate CMID only impacts on KMS server 
machine count of client machines. Once KMS server meets minimum threshold, KMS clients will 
activate regardless of CMID being unique for a subset of specific machines or not.

    -n or --name <MACHINENAME>
> Use this flag to manually specify an ASCII _MACHINENAME_ to use. If no _MACHINENAME_ is specified a random one will be generated.

    -y or --async-msg
> Prints pretty / logging messages asynchronously. Desactivated by default.

    -V or --loglevel <{CRITICAL, ERROR, WARNING, INFO, DEBUG, MINI}>
> Use this flag to set a logging loglevel. The default is _ERROR_.

    -F or --logfile <LOGFILE>
> Creates a _LOGFILE.log_ logging file. The default is named _pykms_logclient.log_.
You can enable same _pykms_Server.py_ suboptions of ```-F```. 

    -S or --logsize <MAXSIZE>
> Use this flag to set a maximum size (in MB) to the output log file. Desactivated by default.

## Activation Procedure
Briefly the product asks for a key during installation, so it needs to enter the GVLK. Then user can set connection parameters, while KMS server must already be running on server machine. Finally with specific commands activation occurs automatically and can be extended later every time for another 180 (or 45) days.

### _Windows_
***
![win1](https://user-images.githubusercontent.com/25354386/36869547-74d05076-1d9c-11e8-9dee-1ff641449c7c.png)

![win2](https://user-images.githubusercontent.com/25354386/36871704-5f62dda6-1da3-11e8-91f7-a7bc71670926.png)

0. Run a Command Prompt as Administrator (you are directly in ```C:\Windows\System32``` path).

```//nologo``` option of ```cscript``` needs only to hide startup logo.

1. This is facoltative, it's for unistalling existing product key.
2. Then put your product's GVLK.
3. Set connection parameters.
4. Try online activation, but... if that fails with error ```0xC004F074``` you’ll most likely have to configure your firewall that it accepts incoming connections on TCP port 1688.
So for Linux users (server-side with _pykms_Server.py_ running): ```sudo ufw allow 1688``` (to remove this rule ```sudo ufw delete allow 1688```)
5. Attempt online activation  (with now traffic on 1688 enabled). 
6. View license informations (facoltative).

### _Office_
***
Note that you’ll have to install a volume license (VL) version of Office. Office versions downloaded from MSDN and / or Technet are non-VL.

![off1](https://user-images.githubusercontent.com/25354386/36871724-6e9e5958-1da3-11e8-8c09-8fd693b20c52.png)

![off2](https://user-images.githubusercontent.com/25354386/36871740-79ce2ae2-1da3-11e8-9ef1-d9b14b86364c.png)

![off3](https://user-images.githubusercontent.com/25354386/36871754-84fa99e6-1da3-11e8-907b-f9435acd3a2d.png)

![off4](https://user-images.githubusercontent.com/25354386/36871764-8e179e2a-1da3-11e8-8e37-eb138a988dea.png)

0. Run a Command Prompt as Administrator and navigate to Office folder ```cd C:\ProgramFiles\Microsoft Office\OfficeXX``` (64-bit path) or ```cd C:\ProgramFiles(x86)\Microsoft Office\OfficeXX``` (32-bit path), where XX = 14 for Office 2010, 15 for Office 2013, 16 for Office 2016 or Office 2019.
1. As you can see, running ```/dstatus```, my Office is expiring (14 days remaining).
2. Only for example, let's go to uninstall this product.
3. This is confirmed running ```/dstatus``` again.
4. Now i put my product's GVLK (and you your key).
5. Set the connection parameter KMS server address.
6. Set the connection parameter KMS server port.
7. Activate installed Office product key.
8. View license informations (in my case product is now licensed and remaining grace 180 days as expected).

## Supported Products
Note that it is possible to activate all versions in the VL (Volume License) channel, so long as you provide the proper key to let Windows know that it should be activating against a KMS server. KMS activation can't be used for Retail channel products, however you can install a VL product key specific to your edition of Windows even if it was installed as Retail. This effectively converts Retail installation to VL channel and will allow you to activate from a KMS server. This is not valid for Office's products, so Office, Project and Visio must be volume license 	versions. Newer version may work as long as the KMS protocol does not change. 
