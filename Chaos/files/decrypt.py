from Crypto.Cipher import AES
from Crypto import Random
from Crypto.Hash import SHA256

BLOCK_SIZE = 16

pad = lambda s: s + (BLOCK_SIZE - len(s) % BLOCK_SIZE) * \
                chr(BLOCK_SIZE - len(s) % BLOCK_SIZE)

unpad = lambda s: s[:-ord(s[len(s) - 1:])]

def getKey(password):
        hasher = SHA256.new(password.encode('utf-8'))
        return hasher.digest()

key = getKey("sahay")

with open("msg.txt") as msg:
        decoded = msg.read().decode('base64')
        filesize = decoded[:16]
	iv = decoded[16:32]
	cipher = AES.new(key, AES.MODE_CBC, iv)
	print unpad(cipher.decrypt((decoded[32:]))).decode('utf8').decode('base64')

