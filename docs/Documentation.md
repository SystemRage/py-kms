# Documentation
What follows are some detailed explanations how the KMS infrastructure works.

## Understanding Key Management Service
KMS activates Microsoft products on a local network, eliminating the need for individual computers to connect to Microsoft. To do this, KMS uses a client–server topology. A KMS client locates a KMS server by using DNS or a static
configuration, then contact it by using Remote Procedure Call (RPC) and tries to activate against it. KMS can activate both physical computers and virtual machines, but a network must meet or exceed the activation threshold
(minimum number of computers that KMS requires) of 25. For activation, KMS clients on the network need to install a KMS client key (General Volume License Key, GVLK), so the product no longer asks Microsoft server but a user–defined
server (the KMS server) which usually resides in a company’s intranet.
	
_py-kms_ is a free open source KMS server emulator written in Python, while Microsoft gives their KMS server only to corporations that signed a Select contract. Furthermore _py-kms_ never refuses activation since it is without
restrictions, while the Microsoft KMS server only activates the products the customer has paid for. _py-kms_ supports KMS protocol versions `4`, `5` and `6`.

**Although _py-kms_ does neither require an activation key nor any payment, it is not meant to run illegal copies of Windows.** Its purpose is to ensure that owners of legal copies can use their software without restrictions, 
e.g. if you buy a new computer or motherboard and your key will be refused activation from Microsoft servers due to hardware changes.

Activation with _py-kms_ is achieved with the following steps:
1. Run _py-kms_ on a computer in the network (this is KMS server or local host).
2. Install the product on client (or said remote host, which is the computer sending data to local host) and enter the GVLK.
3. Configure the client to use the KMS server.
	
Note that KMS activations are only valid for 180 days, the activation validity interval, or 30 to 45 days with consumer-only products. To remain activated, KMS client computers must renew their activation by connecting to the KMS
server at least once every 180 days. For this to work, you have to should ensure that a KMS server is always reachable for all clients on the network. Also remember **you can't activate Windows 8.1 (and above) on a KMS server hosted
on the same machine** (the KMS server must be a different computer than the client).

### About GVLK keys
The GVLK keys for products sold via volume license contracts (renewal every 180 days) are published on 	Microsoft’s Technet web site.

* Windows: [https://technet.microsoft.com/en-us/library/jj612867.aspx](https://technet.microsoft.com/en-us/library/jj612867.aspx)
* Office 2010: [https://technet.microsoft.com/en-us/library/ee624355(v=office.14).aspx#section2_3](https://technet.microsoft.com/en-us/library/ee624355(v=office.14).aspx)
* Office 2013: [https://technet.microsoft.com/en-us/library/dn385360.aspx](https://technet.microsoft.com/en-us/library/dn385360.aspx)
* Office 2016: [https://technet.microsoft.com/en-en/library/dn385360(v=office.16).aspx](https://technet.microsoft.com/en-en/library/dn385360(v=office.16).aspx)

There are also not official keys for consumer-only versions of Windows that require activation renewal every 45 days (Windows 8.1) or 30 days (Windows 8). A more complete and well defined list is available [here](Keys.md).

### SLMGR and OSPP commands
The software License Manager (`slmgr.vbs`) is a Visual Basic script used to configure and retrieve Volume Activation information. The script can be run locally or remotely on the target computer, using the Windows-based script host
(`wscript.exe`) or the command-based script host (`cscript.exe`) - administrators can specify which script engine to use. If no script engine is specified, _SLMGR_ runs using the default script engine (it is recommended to utilize
the `cscript.exe` script engine that resides in the system32 directory). The Software Licensing Service must be restarted for any changes to take effect. To restart it, the Microsoft Management Console (MMC) Services can be used or
running the following command:

```
net stop sppsvc && net start sppsvc
```

The _SLMGR_ requires at least one parameter. If the script is run without any parameters, it displays help information. The general syntax of `slmgr.vbs` is as follows (using the `cscript.exe` as the script engine):
```
cscript slmgr.vbs /parameter
cscript slmgr.vbs [ComputerName] [User] [Password] [Option]
```

Where command line options are:
```
[ComputerName]  Name of a remote computer (default is local computer).
[User]          Account with the required privilege on the remote computer.
[Password]      Password for the account with required privileges on the remote compute.
[Option]        Options are shown in the table below.
```

#### SLMGR
Following tables lists _SLMGR_ more relevant options and a brief description of each. Most of the parameters configure the KMS host.

| Global options | Description |
| --- | --- |
| `/ipk <ProductKey>` | Attempts to install a 5×5 ProductKey for Windows or other application identified by the ProductKey. If the key is valid, this is installed. If a key is already installed, it's silently replaced. |
| `/ato [ActivationID]` | Prompts Windows to attempt online activation, for retail and volume systems with KMS host key. Specifying the ActivationID parameter isolates the effects of the option to the edition associated with that value. |
| `/dli [ActivationID | All]` | Display license information. Specifying the ActivationID parameter displays the license information for the specified edition associated with that ActivationID. Specifying All will display all applicable installed products’ license information. Useful for retrieve the current KMS activation count from the KMS host. |
| `/dlv [ActivationID | All]` | Display detailed license information. |
| `/xpr [ActivationID]` | Display the activation expiration date for the current license state. |

| Advanced options | Description |
| --- | --- |
| `/cpky` | Some servicing operations require the product key to be available in the registry during Out-of-Box Experience (OOBE) operations. So this option removes the product key from the registry to prevent from being stolen by malicious code. |
| `/ilc <LicenseFile>` | Installs the LicenseFile specified by the required parameter. |
| `/rilc` | Reinstalls all licenses stored in %SystemRoot%\system32\oem and %SystemRoot%\System32\spp\tokens. |
| `/rearm` | Resets the activation timers. |
| `/rearm-app <ApplicationID>` | Resets the licensing status of the specified application. |
| `/rearm-sku <ApplicationID>` | Resets the licensing status of the specified SKU. |
| `/upk [ActivationID]` | Uninstalls the product key of the current Windows edition. After a restart, the system will be in an unlicensed state unless a new product key is installed. |
| `/dti [ActivationID]` | Displays installation ID for offline activation of the KMS host for Windows (default) or the application that is identified when its ActivationID is provided. |
| `/atp [ConfirmationID][ActivationID]` | Activate product with user-provided ConfirmationID. |

| KMS client options | Description |
| --- | --- |
| `/skms <Name[:Port] | : port> [ActivationID]` | Specifies the name and the port of the KMS host computer to contact. Setting this value disables auto-detection of the KMS host. If the KMS host uses IPv6 only, the address must be specified in the format [hostname]:port. |
| `/skms-domain <FQDN> [ActivationID]` | Sets the specific DNS domain in which all KMS SRV records can be found. This setting has no effect if the specific single KMS host is set with the /skms option. Use this option, especially in disjoint namespace environments, to force KMS to ignore the DNS suffix search list and look for KMS host records in the specified DNS domain instead.  |
| `/ckms [ActivationID]` | Removes the specified KMS hostname, address, and port information from the registry and restores KMS                   auto-discovery behavior. |
| `/skhc` | Enables KMS host caching (default), which blocks the use of DNS priority and weight after the initial discovery of a working KMS host. If the system can no longer contact the working KMS host, discovery will be attempted again. |
| `/ckhc` | Disables KMS host caching. This setting instructs the client to use DNS auto-discovery each time it attempts KMS activation (recommended when using priority and weight). |
| `/sai <ActivationInterval>` | Changes how often a KMS client attempts to activate itself when it cannot find a KMS host. Replace ActivationInterval with a number of minutes between 15 minutes an 30 days. The default setting is 120. |
| `/sri <RenewalInterval>` | Changes how often a KMS client attempts to renew its activation by contacting a KMS host. Replace RenewalInterval with a number of minutes between 15 minutes an 30 days. The default setting is 10080 (7 days). |
| `/sprt <PortNumber>` | Sets the TCP communications port on a KMS host. It replaces PortNumber with the TCP port number to use. The default setting is 1688. |
| `/sdns` | Enables automatic DNS publishing by the KMS host. |
| `/cdns` | Disables automatic DNS publishing by a KMS host. |
| `/spri` | Sets the priority of KMS host processes to Normal. |
| `/cpri` | Set the KMS priority to Low. |
| `/act-type [ActivationType] [ActivationID]` | Sets a value in the registry that limits volume activation to a single type. ActivationType 1 limits activation to active directory only; 2 limits it to KMS activation; 3 to token-based activation. The 0 option allows any activation type and is the default value. |

#### OSPP
The Office Software Protection Platform script (`ospp.vbs`) can help you to configure and test volume license editions of Office client products. You must open a command prompt by using administrator permissions and navigate to the
folder that contains the mentioned script. The script is located in the folder of the Office installation (use `\Office14` for Office 2010, `\Office15` for Office 2013 and `\Office16` for Office 2016): `%installdir%\Program Files\Microsoft Office\Office15`.
If you are running a 32-bit Office on a 64-bit operating system, the script is located in the folder: `%installdir%\Program Files (x86)\Microsoft Office\Office15`.

Running _OSPP_ requires the `cscript.exe` script engine. To see the help file, type the following command, and then press ENTER:
```
cscript ospp.vbs /?
```

The general syntax is as follows:
```
cscript ospp.vbs [Option:Value] [ComputerName] [User] [Password]
```

Where command line options are:
```
[Option:Value]  Specifies the option and Value to use to activate a product, install or uninstall a product key, install and display license information, set KMS host name and port, and remove KMS host. The options and values are listed in the tables below.
[ComputerName]  Name of the remote computer. If a computer name is not provided, the local computer is used.
[User]          Account that has the required permission on the remote computer.
[Password]      Password for the account. If a user account and password are not provided, the current credentials are used.
```

| Global options | Description |
| --- | --- |
| `/act` | Activates installed Office product keys. |
| `/inpkey:<ProductKey>` | Installs a ProductKey (replaces existing key) with a user-provided ProductKey. |
| `/unpkey:<ProductKey>` | Uninstalls an installed ProductKey with the last five digits of the ProductKey to uninstall (as displayed by the /dstatus option). |
| `/inslic:<LicenseFile>` | Installs a LicenseFile with user-provided path of the .xrm-ms license. |
| `/dstatus` | Displays license information for installed product keys. |
| `/dstatusall` | Displays license information for all installed licenses. |
| `/dhistoryacterr` | Displays the failure history for MAK / Retail activation. |
| `/dinstid` | Displays Installation ID for offline activation. |
| `/actcid:<ConfirmationID>` | Activates product with user-provided ConfirmationID. |
| `/rearm` | Resets the licensing status for all installed Office product keys. |
| `/rearm:<ApplicationID>` | Resets the licensing status for an Office license with a user-provided SKUID value. Use this option with the SKUID value specified by using the /dstatus option if you have run out of rearms and have activated Office through KMS or Active Directory-based activation to gain an additional rearm. |
| `/ddescr:<ErrorCode>` | Displays the description for a user-provided ErrorCode. |

| KMS client options | Description |
| --- | --- |
| `/dhistorykms` | Displays KMS client activation history. |
| `/dcmid` | Displays KMS client computer ID (CMID) |
| `/sethst:<HostName>` | Sets a KMS host name with a user-provided HostName. |
| `/setprt:<Port>` | Sets a KMS port with a user-provided Port number. |
| `/remhst` | Removes KMS hostname (sets port to default). |
| `/cachst:<Value>` | Allows or denies KMS host caching. Parameter Value can be TRUE or FALSE. |
| `/actype:<Value>` | (Windows 8 and later only) Sets volume activation type. Parameter Value can be: 1 (for Active Directory-based), 2 (for KMS), 0 (for both). |
| `/skms-domain:<Value>` | (Windows 8 and later only) Sets the specific DNS domain in which all KMS SRV records can be found. This setting has no effect if the specific single KMS host is set by the /sethst option. Parameter Value is the Fully Qualified Domain Name (FQDN). |
| `/ckms-domain` | (Windows 8 and later only) Clears the specific DNS domain in which all KMS SRV records can be found. The specific KMS host is used if it is set by the /sethst option. Otherwise, auto-discovery of the KMS host is used. |


## Supported Products
Note that it is possible to activate all versions in the VL (Volume License) channel, so long as you provide the proper key to let Windows know that it should be activating against a KMS server. KMS activation can't be used for
Retail channel products, however you can install a VL product key specific to your edition of Windows even if it was installed as Retail. This effectively converts Retail installation to VL channel and will allow you to activate
from a KMS server. **However, this is not valid for Office's products**, so Office, Project and Visio must be always volume license versions. Newer version may work as long as the KMS protocol does not change...

## Further References
* <sup>[1]</sup> https://forums.mydigitallife.net/threads/emulated-kms-servers-on-non-windows-platforms.50234
* <sup>[2]</sup> https://forums.mydigitallife.net/threads/discussion-microsoft-office-2019.75232
* <sup>[3]</sup> https://forums.mydigitallife.net/threads/miscellaneous-kms-related-developments.52594
* <sup>[4]</sup> https://forums.mydigitallife.net/threads/kms-activate-windows-8-1-en-pro-and-office-2013.49686
* <sup>[5]</sup> https://github.com/myanaloglife/py-kms
* <sup>[6]</sup> https://github.com/Wind4/vlmcsd
* <sup>[7]</sup> https://github.com/ThunderEX/py-kms
* <sup>[8]</sup> https://github.com/CNMan/balala/blob/master/pkconfig.csv
* <sup>[9]</sup> http://www.level7techgroup.com/docs/kms_overview.pdf
* <sup>[10]</sup> https://www.dell.com/support/article/it/it/itbsdt1/sln266176/windows-server-using-the-key-management-service-kms-for-activation-of-volume-licensed-systems?lang=en
* <sup>[11]</sup> https://social.technet.microsoft.com/Forums/en-US/c3331743-cba2-4d92-88aa-9633ac74793a/office-2010-kms-current-count-remain-at-10?forum=officesetupdeployprevious
* <sup>[12]</sup> https://betawiki.net/wiki/Microsoft_Windows
* <sup>[13]</sup> https://thecollectionbook.info/builds/windows
* <sup>[14]</sup> https://www.betaarchive.com/forum/viewtopic.php%3Ft%3D29131+&cd=10&hl=it&ct=clnk&gl=it
* <sup>[15]</sup> https://www.google.com/url?sa=t&rct=j&q=&esrc=s&source=web&cd=12&cad=rja&uact=8&ved=2ahUKEwjmvZihtOHeAhVwyoUKHSjeD5Q4ChAWMAF6BAgHEAI&url=ftp%3A%2F%2Flynas.ittc.vu.lt%2Fpub%2FMicrosoft%2FWindows%2520Vista%2FWindows%2520Vista_Volume_Activation_2.0%2FWindows%2520Vista%2520Volume%2520Activation%2FWindows%2520Vista_Volume_Activation_2.0%2Fvolume%2520activation%25202%25200%2520step-by-step%2520guide.doc&usg=AOvVaw3kqhCu3xT-3r416DRGUUs_
* <sup>[16]</sup> https://www.itprotoday.com/windows-78/volume-activation-server-2008
* <sup>[17]</sup> https://docs.microsoft.com/en-us/windows-server/get-started-19/activation-19
* <sup>[18]</sup> https://docs.microsoft.com/en-us/windows-server/get-started/windows-server-release-info
* <sup>[19]</sup> https://support.microsoft.com/en-us/help/13853/windows-lifecycle-fact-sheet
