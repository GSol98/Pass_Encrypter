import hashlib, base64, os, re
from tokenize import PlainToken
from Crypto import Random
from Crypto.Cipher import AES


# =================================================================== Classe del cifrario
# La classe consente di creare degli oggetti Cifrario
class AESCipher(object):

    def __init__(self, key): 
        self.bs = AES.block_size
        self.key = hashlib.sha256(key.encode()).digest()

    def encrypt(self, raw):
        raw = self._pad(raw.encode())
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return base64.b64encode(iv + cipher.encrypt(raw))

    def decrypt(self, enc):
        enc = base64.b64decode(enc)
        iv = enc[:AES.block_size]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return self._unpad(cipher.decrypt(enc[AES.block_size:])).decode('utf-8')

    # Nell'AES CBC il testo deve eavere una dimensione multipla di 16 byte. Si deve effettuare un padding
    # che, in questo caso, aggiunge una lettera dipendente dalla quantità di padding da fare. Grazie a questo
    # è possibile risalire in fase di decifratura al padding che era stato effettuato.
    def _pad(self, s):
        return s + (self.bs - len(s) % self.bs) * chr((self.bs - len(s) % self.bs) + 33).encode()

    @staticmethod
    def _unpad(s):
        return s[: -(ord(s[len(s)-1:]) - 33)]
        
# =================================================================== Funzioni d'utilità
      
# Prende in input un array di bytes
# e lo trasforma in stringa
def bytes2string(bytes):
    res = ""
    for byte in bytes:
        res += chr(byte)
    return res

# Legge il testo cifrato contenuto nel file passwords.txt e lo decifra
def decrypt(cipher):
    try:
        f_passwords = open("./passwords.txt", "r")
        passwords = f_passwords.read()
        return cipher.decrypt(passwords)
    except:
        return '2'


# ========================================================================= Funzioni principali

# Viene invocato solamente durante il primo avvio e consente di 
# impostare la chiave master. Inoltre, se non è presente un file delle
# password lo crea, altrimenti cifra quello esistente con la chiave
# master appena inserita dall'utente 
def configKey(key, key_confirmation):
    try:
        key_enc = key.encode('UTF-8')
        key_confirmation_enc = key_confirmation.encode('UTF-8')

        if key != key_confirmation:
            return '1'
        elif len(key) < 8:
            return '3'

        key_hash = hashlib.sha512(key_enc).hexdigest()
        f_key = open('./key.txt', 'w')
        f_key.write(key_hash)
        f_key.close()

        if not os.path.isfile('./passwords.txt'):
            f_key = open('./passwords.txt', 'w')
            f_key.write(' ')
            f_key.close()
        else:
            cipher = AESCipher(key)
            f_passwords = open('./passwords.txt', 'r')
            plaintext = f_passwords.read()
            f_passwords.close()

            text_encr = bytes2string(cipher.encrypt(plaintext))

            f_passwords = open('./passwords.txt', 'w')
            f_passwords.write(text_encr)
            f_passwords.close()
        return '0'
    except:
        return '2'


# Consente di effettuare il login nell'applicazione
def login(key):
    try:
        f_key = open('./key.txt', 'r')
        key_hash = f_key.read()
        f_key.close()

        digest = hashlib.sha512(key.encode('UTF-8')).hexdigest()

        if digest == key_hash:
            return '0'
        else:
            return '1'
    except:
        return '2'


# Consente di leggere tutti i dati riferiti a un programma 
def read_pass(cipher, name):
    plaintext = decrypt(cipher)
    low_plain = plaintext.lower()
    
    try:
        name = name.lower()
        match = re.search(name+' *:? *[\n]+', low_plain)
        if not match:
            return '0'
        else:
            i = len(name)-1
            while not name[i].isalnum():
                i -= 1
            name = name[:i+1]

            start = end = match.span()[0]

            while end < len(low_plain)-2:
                end += 1
                if plaintext[end] == plaintext[end+1] == '\n':
                    break
            
            plaintext = plaintext[start:end+2]

            return plaintext.replace('\t', '    ')
    except:
        return '2'


# Estrarre la password dal testo in chiaro. Serve solo
# quando l'utente vuole copiarla negli appunti della tastiera
def extract_password(plaintext):
    plaintext_split = plaintext.split('\n')
    password = ''

    # Per selezionare solo la passsord
    for i in range(len(plaintext_split)):
        if 'pass' in plaintext_split[i].lower():
            password = plaintext_split[i].split(':')[1].strip(' ')

    return password


# Scrive il file decifrato nel file delle password consentendo all'utente 
# di modificarlo
def modify_pass(cipher, passwords):
    try:
        passwords = bytes2string(cipher.encrypt(passwords))
        f_passwords = open('./passwords.txt', 'w')
        f_passwords.write(passwords)
        f_passwords.close()

        return '0'
    except: 
        return '2'


# Consente di modificare la chiave primaria
def editKey(cipher, key1, key2):
    try:
        if key1 != key2:
            return '1'
            
        # Decifro il file col vecchio cifrario
        plaintext = decrypt(cipher)

        # Creo il nuovo cifrario
        new_cipher = AESCipher(key1)

        # Memorizzo l'hash della nuova chiave
        subkey_hash = hashlib.sha512(key1.encode("UTF-8")).hexdigest()
        f_key = open("./key.txt", "w")
        f_key.write(str(subkey_hash))
        f_key.close()

        # Cifro il testo con il nuovo cifrario e lo salvo nel file
        text_encr = bytes2string(new_cipher.encrypt(plaintext))
        f_passwords = open('./passwords.txt', 'w')
        f_passwords.write(text_encr)
        f_passwords.close()

        return new_cipher
    except:
        return '2'
