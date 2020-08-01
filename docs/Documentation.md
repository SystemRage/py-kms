# Documentation
What follows are some detailed explanations how some parts work.

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

<table width="700" cellspacing="0" cellpadding="0">
    <colgroup>
       <col span="1" width="250">
       <col span="1" width="450">
    </colgroup>
    <thead><tr><th>Global options</th><th>Description</th></tr></thead>
    <tbody>
         <tr>
            <td>/ipk <<i>ProductKey</i>></td>
            <td>Attempts to install a 5×5 <i>ProductKey</i> for Windows or other application identified by the <i>ProductKey</i>. If the key is valid, this is installed. If a key is already installed, it's silently replaced.</td>
         </tr>
         <tr>
            <td>/ato [<i>ActivationID</i>]</td>
            <td>Prompts Windows to attempt online activation, for retail and volume systems with KMS host key. Specifying the <i>ActivationID</i> parameter isolates the effects of the option to the edition associated with that value.</td>
         </tr>
         <tr>
            <td>/dli [<i>ActivationID</i> | <i>All</i>]</td>
            <td>Display license information. Specifying the <i>ActivationID</i> parameter displays the license information for the specified edition associated with that <i>ActivationID</i>. Specifying <i>All</i> will display all applicable installed products’ license information. Useful for retrieve the current KMS activation count from the KMS host.</td>
         </tr>
         <tr>
            <td>/dlv [<i>ActivationID</i> | <i>All</i>]</td>
            <td>Display detailed license information.</td>
         </tr>
         <tr>
            <td>/xpr [<i>ActivationID</i>]</td>
            <td>Display the activation expiration date for the current license state.</td>
         </tr>
    </tbody>
</table>

<table width="700" cellspacing="0" cellpadding="0">
    <colgroup>
       <col span="1" width="250">
       <col span="1" width="450">
    </colgroup>
    <thead><tr><th>Advanced options</th><th>Description</th></tr></thead>
    <tbody>
         <tr>
            <td>/cpky</td>
            <td>Some servicing operations require the product key to be available in the registry during Out-of-Box Experience (OOBE) operations. So this option removes the product key from the registry to prevent from being stolen by malicious code.</td>
         </tr>
         <tr>
            <td>/ilc <<i>LicenseFile</i>></td>
            <td>Installs the <i>LicenseFile</i> specified by the required parameter.</td>
         </tr>
         <tr>
            <td>/rilc</td>
            <td>Reinstalls all licenses stored in <i>%SystemRoot%\system32\oem</i> and <i>%SystemRoot%\System32\spp\tokens</i>.</td>
         </tr>
         <tr>
            <td>/rearm</td>
            <td>Resets the activation timers.</td>
         </tr>
         <tr>
            <td>/rearm-app <<i>ApplicationID</i>></td>
            <td>Resets the licensing status of the specified application.</td>
         </tr>
         <tr>
            <td>/rearm-sku <<i>ApplicationID</i>></td>
            <td>Resets the licensing status of the specified <i>SKU</i>.</td>
         </tr>
         <tr>
            <td>/upk [<i>ActivationID</i>]</td>
            <td>Uninstalls the product key of the current Windows edition. After a restart, the system will be in an unlicensed state unless a new product key is installed.</td>
         </tr>
         <tr>
            <td>/dti [<i>ActivationID</i>]</td>
            <td>Displays installation ID for offline activation of the KMS host for Windows (default) or the application that is identified when its <i>ActivationID</i> is provided.</td>
         </tr>
         <tr>
            <td>/atp [<i>ConfirmationID</i>][<i>ActivationID</i>]</td>
            <td>Activate product with user-provided <i>ConfirmationID</i>.</td>
         </tr>
    </tbody>
</table>

<table width="750" cellspacing="0" cellpadding="0">
    <colgroup>
       <col span="1" width="250">
       <col span="1" width="450">
    </colgroup>
    <thead><tr><th>KMS client options</th><th>Description</th></tr></thead>
    <tbody>
         <tr>
            <td>/skms <<i>Name</i>[:<i>Port</i>] | : <i>port</i>> [<i>ActivationID</i>]</td>
            <td>Specifies the name and the port of the KMS host computer to contact. Setting this value disables auto-detection of the KMS host. If the KMS host uses IPv6 only, the address must be specified in the format [<i>hostname</i>]:<i>port</i>.</td>
         </tr>
         <tr>
            <td>/skms-domain <<i>FQDN</i>> [<i>ActivationID</i>]</td>
            <td>Sets the specific DNS domain in which all KMS SRV records can be found. This setting has no effect if the specific single KMS host is set with the /skms option. Use this option, especially in disjoint namespace environments, to force KMS to ignore the DNS suffix search list and look for KMS host records in the specified DNS domain instead. </td>
         </tr>
         <tr>
            <td>/ckms [<i>ActivationID</i>]</td>
            <td>Removes the specified KMS hostname, address, and port information from the registry and restores KMS                   auto-discovery behavior.</td>
         </tr>
         <tr>
            <td>/skhc</td>
            <td>Enables KMS host caching (default), which blocks the use of DNS priority and weight after the initial discovery of a working KMS host. If the system can no longer contact the working KMS host, discovery will be attempted again.</td>
         </tr>
         <tr>
            <td>/ckhc</td>
            <td>Disables KMS host caching. This setting instructs the client to use DNS auto-discovery each time it attempts KMS activation (recommended when using priority and weight).</td>
         </tr>
         <tr>
            <td>/sai <<i>ActivationInterval</i>></td>
            <td>Changes how often a KMS client attempts to activate itself when it cannot find a KMS host. Replace <i>ActivationInterval</i> with a number of minutes between 15 minutes an 30 days. The default setting is 120.</td>
         </tr>
         <tr>
            <td>/sri <<i>RenewalInterval</i>></td>
            <td>Changes how often a KMS client attempts to renew its activation by contacting a KMS host. Replace <i>RenewalInterval</i> with a number of minutes between 15 minutes an 30 days. The default setting is 10080 (7 days).</td>
         </tr>
         <tr>
            <td>/sprt <<i>PortNumber</i>></td>
            <td>Sets the TCP communications port on a KMS host. It replaces PortNumber with the TCP port number to use. The default setting is 1688.</td>
         </tr>
         <tr>
            <td>/sdns</td>
            <td>Enables automatic DNS publishing by the KMS host.</td>
         </tr>
         <tr>
            <td>/cdns</td>
            <td>Disables automatic DNS publishing by a KMS host.</td>
         </tr>
         <tr>
            <td>/spri</td>
            <td>Sets the priority of KMS host processes to <i>Normal</i>.</td>
         </tr>
         <tr>
            <td>/cpri</td>
            <td>Set the KMS priority to <i>Low</i>.</td>
         </tr>
         <tr>
            <td>/act-type [<i>ActivationType</i>] [<i>ActivationID<i/>]</td>
            <td>Sets a value in the registry that limits volume activation to a single type. <i>ActivationType</i> 1 limits activation to active directory only; 2 limits it to KMS activation; 3 to token-based activation. The 0 option allows any activation type and is the default value.</td>
         </tr>
    </tbody>
</table>

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

<table width="750" cellspacing="0" cellpadding="0">
    <colgroup>
       <col span="1" width="250">
       <col span="1" width="450">
    </colgroup>
    <thead><tr><th>Global options</th><th>Description</th></tr></thead>
    <tbody>
         <tr>
            <td>/act</td>
            <td>Activates installed Office product keys.</td>
         </tr>
         <tr>
            <td>/inpkey:<<i>ProductKey</i>></td>
            <td>Installs a <i>ProductKey</i> (replaces existing key) with a user-provided <i>ProductKey</i>.</td>
         </tr>
         <tr>
            <td>/unpkey:<<i>ProductKey</i>></td>
            <td>Uninstalls an installed <i>ProductKey</i> with the last five digits of the <i>ProductKey</i> to uninstall (as displayed by the /dstatus option).</td>
         </tr>
         <tr>
            <td>/inslic:<<i>LicenseFile</i>></td>
            <td>Installs a <i>LicenseFile</i> with user-provided path of the .xrm-ms license.</td>
         </tr>
         <tr>
            <td>/dstatus</td>
            <td>Displays license information for installed product keys.</td>
         </tr>
         <tr>
            <td>/dstatusall</td>
            <td>Displays license information for all installed licenses.</td>
         </tr>
         <tr>
            <td>/dhistoryacterr</td>
            <td>Displays the failure history for MAK / Retail activation.</td>
         </tr>
         <tr>
            <td>/dinstid</td>
            <td>Displays Installation ID for offline activation.</td>
         </tr>
         <tr>
            <td>/actcid:<<i>ConfirmationID</i>></td>
            <td>Activates product with user-provided <i>ConfirmationID</i>.</td>
         </tr>
         <tr>
            <td>/rearm</td>
            <td>Resets the licensing status for all installed Office product keys.</td>
         </tr>
         <tr>
            <td>/rearm:<<i>ApplicationID</i>></td>
            <td>Resets the licensing status for an Office license with a user-provided <i>SKUID</i> value. Use this option with the <i>SKUID</i> value specified by using the /dstatus option if you have run out of rearms and have activated Office through KMS or Active Directory-based activation to gain an additional rearm.</td>
         </tr>
         <tr>
            <td>/ddescr:<<i>ErrorCode</i>></td>
            <td>Displays the description for a user-provided <i>ErrorCode</i>.</td>
         </tr>
    </tbody>
</table>

<table width="750" cellspacing="0" cellpadding="0">
    <colgroup>
       <col span="1" width="250">
       <col span="1" width="450">
    </colgroup>
    <thead><tr><th>KMS client options</th><th>Description</th></tr></thead>
    <tbody>
         <tr>
            <td>/dhistorykms</td>
            <td>Displays KMS client activation history.</td>
         </tr>
         <tr>
            <td>/dcmid</td>
            <td>Displays KMS client computer ID (CMID)</td>
         </tr>
         <tr>
            <td>/sethst:<<i>HostName</i>></td>
            <td>Sets a KMS host name with a user-provided <i>HostName</i>.</td>
         </tr>
         <tr>
            <td>/setprt:<<i>Port</i>></td>
            <td>Sets a KMS port with a user-provided <i>Port</i> number.</td>
         </tr>
         <tr>
            <td>/remhst</td>
            <td>Removes KMS hostname (sets port to default).</td>
         </tr>
         <tr>
            <td>/cachst:<<i>Value</i>></td>
            <td>Allows or denies KMS host caching. Parameter <i>Value</i> can be TRUE or FALSE.</td>
         </tr>
         <tr>
            <td>/actype:<<i>Value</i>></td>
            <td>(Windows 8 and later only) Sets volume activation type. Parameter <i>Value</i> can be: 1 (for Active Directory-based), 2 (for KMS), 0 (for both).</td>
         </tr>
         <tr>
            <td>/skms-domain:<<i>Value</i>></td>
            <td>(Windows 8 and later only) Sets the specific DNS domain in which all KMS SRV records can be found. This setting has no effect if the specific single KMS host is set by the /sethst option. Parameter <i>Value</i> is the Fully Qualified Domain Name (FQDN).</td>
         </tr>
         <tr>
            <td>/ckms-domain</td>
            <td>(Windows 8 and later only) Clears the specific DNS domain in which all KMS SRV records can be found. The specific KMS host is used if it is set by the /sethst option. Otherwise, auto-discovery of the KMS host is used.</td>
         </tr>
    </tbody>
</table>

## Further references
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
