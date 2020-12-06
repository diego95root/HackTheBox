import re
import requests
import hashlib
import imaplib
import mailparser
import threading


active_threads = 0
max_threads = 20


host = "127.0.0.1"

username = "paulbyrd"
password = "^(#J@SkFv2[%KhIxKk(Ju`hqcHl<:Ht"


def get_url(raw_email_content: bytes):
    search_results = re.search(b"http\:\/\/\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}.*", raw_email_content)
    if search_results:
        return search_results.group().decode(errors="ignore")
    return ""


def http_login(url: str):
    try:
        data = {
            "firstName": "Paul",
            "lastName": "Byrd",
            "email": username + "@sneakymailer.htb",
            "password": password,
            "rpassword": password
        }
        response = requests.post(url, data=data)
    except:
        pass


def get_raw_email_content(email_content: bytes):
    email = mailparser.parse_from_bytes(email_content)
    raw_email = ""
    raw_email += email.subject + "\n"
    raw_email += email.body
    if not get_url(raw_email.encode()):
        raw_email = email_content
    else:
        raw_email = raw_email.encode()
    return raw_email


def process_email(email_content: bytes):
    global active_threads
    raw_email_content = get_raw_email_content(email_content)
    # Extract urls
    url = get_url(raw_email_content)
    if url:
        http_login(url)
        return True
    active_threads -= 1
    exit(0)


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


if __name__ == '__main__':
    main()

