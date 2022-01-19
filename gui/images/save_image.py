import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad as Pad, unpad as Unpad

global e_cipher
global d_cipher


def CreateCiphers(key):
    global e_cipher
    global d_cipher
    e_cipher = AES.new(key, AES.MODE_ECB)
    d_cipher = AES.new(key, AES.MODE_ECB)


def PadText(text, size, character):
    extra = len(text) % size
    if extra != 0:
        text += character * (size - extra)
    return text


def EncryptText(key, plaintext):
    global e_cipher
    return e_cipher.encrypt(Pad(base64.b64encode(str.encode(plaintext)), 32))


def DecryptText(key, ciphertext):
    global d_cipher
    return base64.b64decode(Unpad(d_cipher.decrypt(ciphertext), 32)).decode()


key = base64.b64decode(str.encode(input("k: ")))
CreateCiphers(key)
image = input("i: ")
target = input("t: ")
with open(image, "rb") as image:
    string = base64.b64encode(image.read()).decode('ASCII')
    image.close()
with open(target, 'wb+') as f:
    f.write(EncryptText(key, string))
    f.close()
