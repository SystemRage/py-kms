# Getting Started

## Run pykms_Server.py manually
***

A Linux user with `ifconfig` command can get his KMS IP (Windows users can try `ipconfig /all`).
```bash
user@host ~ $ ifconfig
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

```
user@host ~/path/to/folder/py-kms $ python3 pykms_Server.py 192.168.1.102 1688
```

To stop `pykms_Server.py`, in the same bash window where code running, simply press CTRL+C.
Alternatively, in a new bash window, use `kill <pid>` command (you can type `ps aux` first and have the process <pid>) or `killall <name_of_server>`.

## Run pykms_Server.py automatically at start
***

You can simply manage a daemon that runs as a background process.

### Systemd
If you are running a Linux distro using `systemd`, create the file: `sudo nano /etc/systemd/system/py3-kms.service`, then add the following (change it where needed) and save:
```systemd
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
Check syntax with `sudo systemd-analyze verify py3-kms.service`, correct file permission (if needed) `sudo chmod 644 /etc/systemd/system/py3-kms.service`, then reload systemd manager configuration `sudo systemctl daemon-reload`,
start the daemon `sudo systemctl start py3-kms.service` and view its status `sudo systemctl status py3-kms.service`. Check if daemon is correctly running with `cat </path/to/your/log/files/folder>/pykms_logserver.log`. Finally a
few generic commands useful for interact with your daemon [here](https://linoxide.com/linux-how-to/enable-disable-services-ubuntu-systemd-upstart/).

### Upstart (deprecated)
If you are running a Linux distro using `upstart` (deprecated), create the file: `sudo nano /etc/init/py3-kms.conf`, then add the following (change it where needed) and save:
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
Check syntax with `sudo init-checkconf -d /etc/init/py3-kms.conf`, then reload upstart to recognise this process `sudo initctl reload-configuration`. Now start the service `sudo start py3-kms`, and you can see the logfile
stating that your daemon is running: `cat </path/to/your/log/files/folder>/pykms_logserver.log`. Finally a few generic commands useful for interact with your daemon [here](https://eopio.com/linux-upstart-process-manager/).

### Windows
If you are using Windows, to run `pykms_Server.py` as service you need to install [pywin32](https://sourceforge.net/projects/pywin32/), then you can create a file for example named `kms-winservice.py` and put into it this code:
```python
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
Now in a command prompt type `C:\Windows\Python27\python.exe kms-winservice.py install` to install the service. Display all the services with `services.msc` and find the service associated with _py-kms_, change the startup type
from `manual` to `auto`. Finally `Start` the service. If this approach fails, you can try to use [Non-Sucking Service Manager](https://nssm.cc/) or Task Scheduler as described [here](https://blogs.esri.com/esri/arcgis/2013/07/30/scheduling-a-scrip/).
