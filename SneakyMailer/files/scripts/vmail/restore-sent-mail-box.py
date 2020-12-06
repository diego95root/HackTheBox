import imaplib
import time

host = "127.0.0.1"

original_with_creds = b'MIME-Version: 1.0\r\nTo: root <root@debian>\r\nFrom: Paul Byrd <paulbyrd@sneakymailer.htb>\r\nSubject: Password reset\r\nDate: Fri, 15 May 2020 13:03:37 -0500\r\nImportance: normal\r\nX-Priority: 3\r\nContent-Type: multipart/alternative;\r\n\tboundary="_21F4C0AC-AA5F-47F8-9F7F-7CB64B1169AD_"\r\n\r\n--_21F4C0AC-AA5F-47F8-9F7F-7CB64B1169AD_\r\nContent-Transfer-Encoding: quoted-printable\r\nContent-Type: text/plain; charset="utf-8"\r\n\r\nHello administrator, I want to change this password for the developer accou=\r\nnt\r\n\r\nUsername: developer\r\nOriginal-Password: m^AsY7vTKVT+dV1{WOU%@NaHkUAId3]C\r\n\r\nPlease notify me when you do it=20\r\n\r\n--_21F4C0AC-AA5F-47F8-9F7F-7CB64B1169AD_\r\nContent-Transfer-Encoding: quoted-printable\r\nContent-Type: text/html; charset="utf-8"\r\n\r\n<html xmlns:o=3D"urn:schemas-microsoft-com:office:office" xmlns:w=3D"urn:sc=\r\nhemas-microsoft-com:office:word" xmlns:m=3D"http://schemas.microsoft.com/of=\r\nfice/2004/12/omml" xmlns=3D"http://www.w3.org/TR/REC-html40"><head><meta ht=\r\ntp-equiv=3DContent-Type content=3D"text/html; charset=3Dutf-8"><meta name=\r\n=3DGenerator content=3D"Microsoft Word 15 (filtered medium)"><style><!--\r\n/* Font Definitions */\r\n@font-face\r\n\t{font-family:"Cambria Math";\r\n\tpanose-1:2 4 5 3 5 4 6 3 2 4;}\r\n@font-face\r\n\t{font-family:Calibri;\r\n\tpanose-1:2 15 5 2 2 2 4 3 2 4;}\r\n/* Style Definitions */\r\np.MsoNormal, li.MsoNormal, div.MsoNormal\r\n\t{margin:0in;\r\n\tmargin-bottom:.0001pt;\r\n\tfont-size:11.0pt;\r\n\tfont-family:"Calibri",sans-serif;}\r\n.MsoChpDefault\r\n\t{mso-style-type:export-only;}\r\n@page WordSection1\r\n\t{size:8.5in 11.0in;\r\n\tmargin:1.0in 1.0in 1.0in 1.0in;}\r\ndiv.WordSection1\r\n\t{page:WordSection1;}\r\n--></style></head><body lang=3DEN-US link=3Dblue vlink=3D"#954F72"><div cla=\r\nss=3DWordSection1><p class=3DMsoNormal>Hello administrator, I want to chang=\r\ne this password for the developer account</p><p class=3DMsoNormal><o:p>&nbs=\r\np;</o:p></p><p class=3DMsoNormal>Username: developer</p><p class=3DMsoNorma=\r\nl>Original-Password: m^AsY7vTKVT+dV1{WOU%@NaHkUAId3]C</p><p class=3DMsoNorm=\r\nal><o:p>&nbsp;</o:p></p><p class=3DMsoNormal>Please notify me when you do i=\r\nt </p></div></body></html>=\r\n\r\n--_21F4C0AC-AA5F-47F8-9F7F-7CB64B1169AD_--\r\n'
original_for_low_hint = b'To: low@debian\r\nFrom: Paul Byrd <paulbyrd@sneakymailer.htb>\r\nSubject: Module testing\r\nMessage-ID: <4d08007d-3f7e-95ee-858a-40c6e04581bb@sneakymailer.htb>\r\nDate: Wed, 27 May 2020 13:28:58 -0400\r\nUser-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:68.0) Gecko/20100101\r\n Thunderbird/68.8.0\r\nMIME-Version: 1.0\r\nContent-Type: text/plain; charset=utf-8; format=flowed\r\nContent-Transfer-Encoding: 7bit\r\nContent-Language: en-US\r\n\r\nHello low\r\n\r\n\r\nYour current task is to install, test and then erase every python module you \r\nfind in our PyPI service, let me know if you have any inconvenience.\r\n\r\n'

original_emails = {original_with_creds: False, original_for_low_hint: False}

username = "paulbyrd"
password = "^(#J@SkFv2[%KhIxKk(Ju`hqcHl<:Ht"


def sent_mail(client: imaplib.IMAP4, email: bytes):
	client.append('"INBOX.Sent Items"', "", imaplib.Time2Internaldate(time.time()), email)


def check_sent_items():
	client = imaplib.IMAP4(host)
	client.login(username, password)
	client.select('"INBOX.Sent Items"')

	typ, data = client.search(None, "ALL")
	for number in data[0].split():
		mail_type, mail_data = client.fetch(number, '(RFC822)')
		raw_email = mail_data[0][1]
		if raw_email in original_emails:
			original_emails[raw_email] = True
		else:
			client.store(number, '+FLAGS', '\\Deleted')
	for original_email in original_emails.keys():
		if not original_emails[original_email]:
			sent_mail(client, original_email)
	client.expunge()
	client.close()
	client.logout()


def main():
	check_sent_items()


if __name__ == '__main__':
	main()

