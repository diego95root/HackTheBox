# Hack The Box: Heist machine write-up

This is a windows box thoroughly based on enumeration, it starts with a guest access that leaks some credentials followed by smb users enumeration that provides us with even more users. Then winRM is enabled, so we can access the box using those creds. Finally, a search for strings from the firefox process leaks even more credentials giving us full access to the box as admin.

Let's dig in! The IP of the machine is ``10.10.10.149`` and I added it to my `/etc/hosts` file as `heist.htb`.

### Enumeration

As always, we start by enumerating open ports to discover the services running in the machine. I fire up nmap:

*Result of initial nmap scan*

```sh
# Nmap 7.70 scan initiated Mon Aug 19 14:47:18 2019 as: nmap -v -sV -sC -oN nmap/initial heist.htb
Nmap scan report for heist.htb (10.10.10.149)
Host is up (0.077s latency).
Not shown: 997 filtered ports
PORT    STATE SERVICE       VERSION
80/tcp  open  http          Microsoft IIS httpd 10.0
| http-cookie-flags:
|   /:
|     PHPSESSID:
|_      httponly flag not set
| http-methods:
|   Supported Methods: OPTIONS TRACE GET HEAD POST
|_  Potentially risky methods: TRACE
|_http-server-header: Microsoft-IIS/10.0
| http-title: Support Login Page
|_Requested resource was login.php
135/tcp open  msrpc         Microsoft Windows RPC
445/tcp open  microsoft-ds?
Service Info: OS: Windows; CPE: cpe:/o:microsoft:windows

Host script results:
|_clock-skew: mean: -59m31s, deviation: 0s, median: -59m31s
| smb2-security-mode:
|   2.02:
|_    Message signing enabled but not required
| smb2-time:
|   date: 2019-08-19 13:48:13
|_  start_date: N/A

Read data files from: /usr/bin/../share/nmap
Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
# Nmap done at Mon Aug 19 14:48:20 2019 -- 1 IP address (1 host up) scanned in 61.70 seconds
```

Okay so we see that we'll need to enumerate smb shares and also check the web server. I also ran another nmap scan on the background to check all ports (`nmap -v -p- -sV -sC -oN nmap/all heist.htb`) and something interesting came up:

*Result of exhaustive nmap scan*

```sh
5985/tcp  open  http          Microsoft HTTPAPI httpd 2.0 (SSDP/UPnP)
|_http-server-header: Microsoft-HTTPAPI/2.0
|_http-title: Not Found
```

Looks like winRM is enabled! WinRM is a Windows-native protocol used to administer machines remotely that has been known to have some serious flags that allow authenticated RCE.

#### Port 80 enumeration

Upon visiting the webserver we have a log in panel. However, there is an option to log in as guest, which leads us to a chat between `Hazard` and a system administrator that contains an interesting file as attachment.

*Login panel*

![Img](images/login.png)

*Chat found*

![Img](images/chat.png)

The file attached is a config file from a router and contains different credentials:

```
version 12.2
no service pad
service password-encryption
!
isdn switch-type basic-5ess
!
hostname ios-1
!
security passwords min-length 12
enable secret 5 $1$pdQG$o8nrSzsGXeaduXrjlvKc91
!
username rout3r password 7 0242114B0E143F015F5D1E161713
username admin privilege 15 password 7 02375012182C1A1D751618034F36415408
!
!
ip ssh authentication-retries 5
ip ssh version 2
!
!
router bgp 100
 synchronization
 bgp log-neighbor-changes
 bgp dampening
 network 192.168.0.0 mask 300.255.255.0
 timers bgp 3 9
 redistribute connected
!
ip classless
ip route 0.0.0.0 0.0.0.0 192.168.0.1
!
!
access-list 101 permit ip any any
dialer-list 1 protocol ip list 101
!
no ip http server
no ip http secure-server
!
line vty 0 4
 session-timeout 600
 authorization exec SSH
 transport input ssh
```

I cracked two of the hashes with <http://www.ifm.net.nz/cookbooks/passwordcracker.html>:

*Hash 1*

![Img](images/hash1.png)

*Hash 2*

![Img](images/hash2.png)

The other one, `$1$pdQG$o8nrSzsGXeaduXrjlvKc91` was an md5 hash and I cracked it with John The Ripper to obtain `stealth1agent`.

Good, so far we have three possible credential sets:

```
Users: Rout3r, admin, Hazard
Passwords: $uperP@ssword, Q4)sJu\Y8qz*A3?d, stealth1agent
```

#### SMB enumeration

I then tried to access any shares through SMB. Trying credentials with smbmap I got the right ones: `Hazard:stealth1agent`. However, there was nothing interesting on `IPC$` and the other two shares were not accesible.

*smbmap output*

![Img](images/smb1.png)

I then tried to obtain more possible users by using `lookupsid.py` from impacket. And good! I obtained two more users: `Jason` and `Chase`!

*Getting more users through `lookupsid.py`*

![Img](images/lookupsid.png)

#### Getting user with winRM

I cloned a ruby tool called `evil-winrm` from github (<https://github.com/Hackplayers/evil-winrms>):

*Github page of evil-winrm*

![Img](images/evilwinrm.png)

I started trying combinations of credentials until I found the right one and was prompted with a shell, although then I found out that there was a metasploit module that did this automatically for you. Well, too bad.

The credentials were: `chase:Q4)sJu\Y8qz*A3?d`.

*Gaining a shell as user and getting the hash*

![Img](images/user.png)

### Privilege escalation

I tried to run some enumeration powershell scripts but apparently the user `chase` didn't have many permissions. One thing I could do was list processes on the machine, so I ran `get-process` and found out firefox was running, which is not common on HackTheBox boxes.

*Listing processes*

![Img](images/process1.png)

![Img](images/process2.png)

I then searched for the string `password` on the user's directory recursively which would give me anything (if there was) that firefox stored on disk. And turn out there was! I used the following command: `Get-ChildItem -Path C:\Users\ -Recurse -File | Select-String password`

*Getting the admin password*

![Img](images/root-pass.png)

Then I just used it with `Administrator` on the winrm script and had full privileges!

*Getting to root*

![Img](images/root.png)

Overall, I think this is a good machine for windows beginner, maybe a bit too based on users enumeration (I got really frustrated at some points). I hope you found the writeup useful, if you liked it you can give me respect on hackthebox through the following link: <https://www.hackthebox.eu/home/users/profile/31531>.

---

*Diego Bernal Adelantado*
