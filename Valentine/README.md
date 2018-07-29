# Hack The Box: Valentine machine write-up

The following box was fairly easy so this will be a short write-up. Ip address of the machine: 10.10.10.79.

#### Enumeration

First of all, I run nmap to see services running:

```sh
$ nmap -sC -sV -oA nmap/initial 10.10.10.79
```

I get the following output:

*Result of nmap scan*

```bash
# Nmap 7.01 scan initiated Fri Jul  6 18:48:57 2018 as: nmap -sC -sV -oA nmap/initial 10.10.10.79
Nmap scan report for 10.10.10.79
Host is up (0.054s latency).
Not shown: 991 closed ports
PORT      STATE    SERVICE       VERSION
22/tcp    open     tcpwrapped
80/tcp    open     http          Apache httpd 2.2.22 ((Ubuntu))
|_http-server-header: Apache/2.2.22 (Ubuntu)
|_http-title: Site doesn't have a title (text/html).
443/tcp   open     ssl/http      Apache httpd 2.2.22 ((Ubuntu))
|_http-server-header: Apache/2.2.22 (Ubuntu)
|_http-title: Site doesn't have a title (text/html).
| ssl-cert: Subject: commonName=valentine.htb/organizationName=valentine.htb/stateOrProvinceName=FL/countryName=US
| Not valid before: 2018-02-06T00:45:25
|_Not valid after:  2019-02-06T00:45:25
|_ssl-date: 2018-07-06T16:49:27+00:00; 0s from scanner time.
1594/tcp  filtered sixtrak
3268/tcp  filtered globalcatLDAP
5440/tcp  filtered unknown
9877/tcp  filtered unknown
49155/tcp filtered unknown
49156/tcp filtered unknown

Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
# Nmap done at Fri Jul  6 18:49:33 2018 -- 1 IP address (1 host up) scanned in 35.44 seconds
```

So I head over port 80 and check the webpage, but it's only an image.

*Image served on port 80*

![Img](images/image_init.png "Img")

I checked exif, strings and binwalk to check if there was anything on it but no success. So then I start DirBuster.

*Result of DirBuster scan*

```bash
DirBuster 1.0-RC1 - Report
http://www.owasp.org/index.php/Category:OWASP_DirBuster_Project
Report produced on Fri Jul 06 14:58:12 PDT 2018
--------------------------------

http://10.10.10.79:80
--------------------------------
Directories found during testing:

Dirs found with a 200 response:

/index/
/
/dev/
/encode/
/decode/

Dirs found with a 403 response:

/cgi-bin/
/icons/
/doc/
/icons/small/


--------------------------------
Files found during testing:

Files found with a 200 responce:

/index.php
/dev/hype_key
/dev/notes.txt
/encode.php
/decode.php


--------------------------------
```

Something interesting. First of all, I check the `dev` directory. On `notes.txt` I discover some notes the user of the machine left:

```
To do:

1) Coffee.
2) Research.
3) Fix decoder/encoder before going live.
4) Make sure encoding/decoding is only done client-side.
5) Don't use the decoder/encoder until any of this is done.
6) Find a better way to take notes.
```

Makes sense because we found the encode and decode php scripts as well with DirBuster.

Then, I check [`hype_key`](files/hype_key.txt), which turns out to be some hex characters. I decode them and obtain an RSA private key:

```
-----BEGIN RSA PRIVATE KEY-----
Proc-Type: 4,ENCRYPTED
DEK-Info: AES-128-CBC,AEB88C140F69BF2074788DE24AE48D46

DbPrO78kegNuk1DAqlAN5jbjXv0PPsog3jdbMFS8iE9p3UOL0lF0xf7PzmrkDa8R
5y/b46+9nEpCMfTPhNuJRcW2U2gJcOFH+9RJDBC5UJMUS1/gjB/7/My00Mwx+aI6
0EI0SbOYUAV1W4EV7m96QsZjrwJvnjVafm6VsKaTPBHpugcASvMqz76W6abRZeXi
Ebw66hjFmAu4AzqcM/kigNRFPYuNiXrXs1w/deLCqCJ+Ea1T8zlas6fcmhM8A+8P
OXBKNe6l17hKaT6wFnp5eXOaUIHvHnvO6ScHVWRrZ70fcpcpimL1w13Tgdd2AiGd
pHLJpYUII5PuO6x+LS8n1r/GWMqSOEimNRD1j/59/4u3ROrTCKeo9DsTRqs2k1SH
QdWwFwaXbYyT1uxAMSl5Hq9OD5HJ8G0R6JI5RvCNUQjwx0FITjjMjnLIpxjvfq+E
p0gD0UcylKm6rCZqacwnSddHW8W3LxJmCxdxW5lt5dPjAkBYRUnl91ESCiD4Z+uC
Ol6jLFD2kaOLfuyee0fYCb7GTqOe7EmMB3fGIwSdW8OC8NWTkwpjc0ELblUa6ulO
t9grSosRTCsZd14OPts4bLspKxMMOsgnKloXvnlPOSwSpWy9Wp6y8XX8+F40rxl5
XqhDUBhyk1C3YPOiDuPOnMXaIpe1dgb0NdD1M9ZQSNULw1DHCGPP4JSSxX7BWdDK
aAnWJvFglA4oFBBVA8uAPMfV2XFQnjwUT5bPLC65tFstoRtTZ1uSruai27kxTnLQ
+wQ87lMadds1GQNeGsKSf8R/rsRKeeKcilDePCjeaLqtqxnhNoFtg0Mxt6r2gb1E
AloQ6jg5Tbj5J7quYXZPylBljNp9GVpinPc3KpHttvgbptfiWEEsZYn5yZPhUr9Q
r08pkOxArXE2dj7eX+bq65635OJ6TqHbAlTQ1Rs9PulrS7K4SLX7nY89/RZ5oSQe
2VWRyTZ1FfngJSsv9+Mfvz341lbzOIWmk7WfEcWcHc16n9V0IbSNALnjThvEcPky
e1BsfSbsf9FguUZkgHAnnfRKkGVG1OVyuwc/LVjmbhZzKwLhaZRNd8HEM86fNojP
09nVjTaYtWUXk0Si1W02wbu1NzL+1Tg9IpNyISFCFYjSqiyG+WU7IwK3YU5kp3CC
dYScz63Q2pQafxfSbuv4CMnNpdirVKEo5nRRfK/iaL3X1R3DxV8eSYFKFL6pqpuX
cY5YZJGAp+JxsnIQ9CFyxIt92frXznsjhlYa8svbVNNfk/9fyX6op24rL2DyESpY
pnsukBCFBkZHWNNyeN7b5GhTVCodHhzHVFehTuBrp+VuPqaqDvMCVe1DZCb4MjAj
Mslf+9xK+TXEL3icmIOBRdPyw6e/JlQlVRlmShFpI8eb/8VsTyJSe+b853zuV2qL
suLaBMxYKm3+zEDIDveKPNaaWZgEcqxylCC/wUyUXlMJ50Nw6JNVMM8LeCii3OEW
l0ln9L1b/NXpHjGa8WHHTjoIilB5qNUyywSeTBF2awRlXH9BrkZG4Fc4gdmW/IzT
RUgZkbMQZNIIfzj1QuilRVBm/F76Y/YMrmnM9k/1xSGIskwCUQ+95CGHJE8MkhD3
-----END RSA PRIVATE KEY-----
```

However, as we can see, it's encrypted, so we will need to find a passphrase in order to decrypt it.

I tried to exploit both `encode.php` and `decode.php` but couldn't find anything, so I decided to look back at the image. And after some googling I found that the image is a hint making a reference to the heartbleed bug.

#### Vulnerability

So I download a python script, [ssltest.py](ssltest.py), which should tell me whether the box is vulnerable or not.

*Output of ssltest.py*

![Img](images/ssltest.png "Img")

So once there, we fire up metasploit with `msfconsole`:

![Img](images/meta1.png "Img")
![Img](images/meta2.png "Img")

And looks like we found a leak: `$text=aGVhcnRibGVlZGJlbGlldmV0aGVoeXBlCg==`. We decode the base64 string which becomes: `heartbleedbelievethehype`. I was 99% sure it was the passphrase of the RSA key, so I tried it and it worked.

*Decryption of key*

![Img](images/key.png "Img")

Hence, we just have to guess the user to get ssh access to the box. Based upon the name of the key file, which was `hype_key`, I thought it could be `hype`.

*SSH access with key and root hash*

![Img](images/ssh.png "Img")

#### Root

Once in, I ran the usual `linenum.sh` after having wget'ed it from my local machine. Interestingly, it revealed that `.bash_history` contained some previously typed commands, among these `tmux -S /.devs/dev_sess`. That command restores a previous tmux session and, unfortunately for the user of the machine, it was owned by root. So that's how we gain a root shell.

*Tmux window*

![Img](images/tmux.png "Img")

If we wanted an easier access, we could just type `passwd` to set a new root password and then just log in to root through ssh with our new password.

*Diego Bernal Adelantado*
