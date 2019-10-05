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

# Usage
```
docker run -d --name py3-kms \
    -p 8080:8080 \
    -p 1688:1688 \
    -e IP=0.0.0.0 \
    -e PORT=1688 \
    -e SQLITE=true \
    -e HWID=RANDOM \
    -e LOGLEVEL=INFO \
    -e LOGSIZE=2 \
    -e LOGFILE=/var/log/py3-kms.log \
    -v /etc/localtime:/etc/localtime:ro \
    -v /var/log:/var/log:rw \
    --restart unless-stopped ekonprof18/pykms:py3-kms
```

# Sqlite-web
A web-based SQLite database browser written in Python.
Start on http://example.com:8080/ in read-only mode for clients.db.

# Options
```
# EN: Variables
# RU: Переменные

# EN: IP-address
# RU: IP-адрес
ENV IP		0.0.0.0
# The IP address to listen on. The default is "0.0.0.0" (all interfaces).

# EN: TCP-port
# RU: TCP-порт
ENV PORT		1688
# The network port to listen on. The default is "1688".

# EN: ePID
# RU: ePID
ENV EPID		""
# Use this flag to manually specify an ePID to use. If no ePID is specified, a random ePID will be generated.

# EN: lcid
# RU: lcid
ENV LCID		1033
# Use this flag to manually specify an LCID for use with randomly generated ePIDs. Default is 1033 (en-us).

# EN: the current client count
# RU: текущий счётчик запросов на активацию продуктов от Microsoft
ENV CLIENT_COUNT	26
# Use this flag to specify the current client count. Default is 26.
# A number >=25 is required to enable activation of client OSes; for server OSes and Office >=5.

# EN: the activation interval (in minutes)
# RU: интервал активации (в минутах)
ENV ACTIVATION_INTERVAL	120
# Use this flag to specify the activation interval (in minutes). Default is 120 minutes (2 hours).

# EN: the renewal interval (in minutes)
# RU: интервал обновления (в минутах)
ENV RENEWAL_INTERVAL	10080
# Use this flag to specify the renewal interval (in minutes). Default is 10080 minutes (7 days).

# EN: Use SQLITE
# RU: Использовать РСУБД SQLITE
ENV SQLITE		false
# Use this flag to store request information from unique clients in an SQLite database.

# EN: hwid
# RU: hwid
ENV HWID		364F463A8863D35F
# Use this flag to specify a HWID. 
# The HWID must be an 16-character string of hex characters.
# The default is "364F463A8863D35F" or type "RANDOM" to auto generate the HWID.

# EN: log level ("CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG")
# RU: Уровень логирования ("CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG")
ENV LOGLEVEL		ERROR
# Use this flag to set a Loglevel. The default is "ERROR".

# EN: log file
# RU: Лог-файл
ENV LOGFILE		/var/log/pykms_logserver.log
# Use this flag to set an output Logfile. The default is "/var/log/pykms_logserver.log".

# EN: log file size in MB
# RU: Максимальный размер Лог-файл в мегабайтах
ENV LOGSIZE             ""
# Use this flag to set a maximum size (in MB) to the output log file. Desactivated by default.
```

# Other Important Stuff
Consult the [Wiki](https://github.com/SystemRage/py-kms/wiki) for more informations about activation with _py-kms_ and to get GVLK keys.

# License
   [![License](https://img.shields.io/badge/license-unlicense-lightgray.svg)](https://github.com/SystemRage/py-kms/blob/master/LICENSE)
