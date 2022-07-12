# Troubleshooting

Something does not work as expected ? _Before_ you open an issue, please make sure to at least follow these steps to further diagnose or even resolve your problem.
If you not follow this, do not expect that we can or want to help you!


* Are you activating a legit Windows copy checked with `sha256`, `md5` or is it maybe a warez torrent version ?
* Did you tried a clean installation (format all) ? You skipped entering any key during installation, turning off internet connection, first activating and then updating Windows (and eventually later upgrading) ?
* Are you activating Windows or Office on a different machine (physical or virtual) where py-kms runs?
* Have you installed all latest packages ? Especially before upgrading ? Are you upgrading using the "Update Assistant"/"Media Creation" tool to switch from Windows 7 / 8 / 8.1 to 10 (for me has always worked) ?
* If isn't a clean install, so far as you have kept activated your Windows copy ? Have you used some other activator (maybe not trusted) that injects or changes .dll files and therefore may have corrupted something ?
* Have you forgot to reactivate at least once before 180 (45 or 30, depending on your version) days ?
* Is your system very tweaked with some service disabled (have you used [O&O Shutup 10](https://www.oo-software.com/en/shutup10) or similar tools) ?
* Have you disabled (or created an exception for) ALL firewalls (Public/Private/Office) / antivirus (Windows defender, etc..), server-side AND client-side ?
* Have you already activated with a OEM/Retail/other license and now you want to activate using `py-kms` ? So, have you switched to volume channel with appropriate [GVLK](Keys.md) ? Make sure you first deleted the previous key (example: [#24 (comment)](https://github.com/SystemRage/py-kms/issues/24#issuecomment-492431436)) ?
* Are you running the commands using the **elevated** command prompt ?
* Are you connecting correctly to your `py-kms` server instance ?
* Have you tried to fix with "Windows Troubleshoot", `sfc /scannow` or other strange Windows tools ?
* If you activated successfully with `py-kms` other Windows stuff, consider it could be an error specific for your PC (so you may need a scented clean installation) ?
* Is your `py-kms` really running ? Already tried to enable debug logs ?
* Did you already searched for your issue [here](https://github.com/SystemRage/py-kms/issues) ?
* Are you running the latest version of `py-kms` ?
* For Office: Did you made sure to use a Office **with** GLVK support ?!
* You found a real bug ? Could you maybe make our life's easier and describe what goes wrong **and** also provide some information about your environment (OS, Python-Version, Docker, Commit-Hashes, Network-Setup) ?
* When you post logs: Please remove personal information (replace IPs with something like `[IP_ADDRESS_A]`)...

If you have already thought about all of this, your last hope to solve your problem is reading some verse of the Holy Bible of activations: "MDL forums" - otherwise "I don't know !", but try open up an issue anyways :)
