import uuid
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


def EncryptTextWithKey(key, plaintext, decode=True):
    from cryptography.fernet import Fernet
    encoded_text = Fernet(key).encrypt(str.encode(plaintext))
    return encoded_text.decode() if decode else encoded_text


def DecryptTextWithKey(key, ciphertext, decode=True):
    from cryptography.fernet import Fernet
    encoded_text = Fernet(key).decrypt(str.encode(ciphertext))
    return encoded_text.decode() if decode else encoded_text

"""
def HashText(text):
    salt = uuid.uuid4().hex  # generates random salt value
    hash_object = hashlib.sha256(salt.encode() + text.encode())
    hashed_string = hash_object.hexdigest()
    hashed_text = "{}:{}".format(hashed_string, salt)
    # we use : as a character because hashed_string only contains hex characters, and hence cannot contain colons.
    return hashed_text


def CompareTextToHashed(text, hashed_text):
    hash_value, salt = hashed_text.split(":")
    hash_object = hashlib.sha256(salt.encode() + text.encode())
    # we hash the plain text for comparison with already hashed value
    new_hash_value = hash_object.hexdigest()
    return hash_value == new_hash_value
"""