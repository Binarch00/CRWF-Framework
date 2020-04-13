from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes
from Crypto.Cipher import AES, PKCS1_OAEP


class RSATools:

    @staticmethod
    def gen_keys(size=2048, passphrase="", prv_file="private.pem", pub_file="public.pem"):
        key = RSA.generate(size)
        private_key = key.export_key(passphrase=passphrase)
        file_out = open(prv_file, "wb")
        file_out.write(private_key)
        file_out.flush()
        file_out.close()

        public_key = key.publickey().export_key()
        file_out = open(pub_file, "wb")
        file_out.write(public_key)
        file_out.flush()
        file_out.close()

    def decrypt(self, data):
        data = bytearray(data)

        enc_session_key = data[:self.prv_key.size_in_bytes()]
        data = data[self.prv_key.size_in_bytes():]
        nonce = data[:16]
        data = data[16:]
        tag = data[:16]
        ciphertext = data[16:]

        # Decrypt the session key with the private RSA key
        cipher_rsa = PKCS1_OAEP.new(self.prv_key)
        session_key = cipher_rsa.decrypt(enc_session_key)

        # Decrypt the data with the AES session key
        cipher_aes = AES.new(session_key, AES.MODE_EAX, nonce)
        data = cipher_aes.decrypt_and_verify(ciphertext, tag)
        return data.decode("utf-8")

    def encrypt(self, data):
        data = data.encode("utf-8")
        session_key = get_random_bytes(16)
        data_out = []

        # Encrypt the session key with the public RSA key
        cipher_rsa = PKCS1_OAEP.new(self.pub_key)
        enc_session_key = cipher_rsa.encrypt(session_key)

        # Encrypt the data with the AES session key
        cipher_aes = AES.new(session_key, AES.MODE_EAX)
        ciphertext, tag = cipher_aes.encrypt_and_digest(data)
        for x in (enc_session_key, cipher_aes.nonce, tag, ciphertext):
            data_out += x
        return bytes(data_out)

    @staticmethod
    def _load_key(key_file, passphrase=""):
        if key_file:
            with open(key_file) as fl:
                return RSA.import_key(fl.read(), passphrase=passphrase)

    def __init__(self, pub_key=None, prv_key=None, passphrase=""):
        self.pub_key = self._load_key(pub_key, passphrase)
        self.prv_key = self._load_key(prv_key, passphrase)
        self.passphrase = passphrase


if __name__ == "__main__":
    # RSATools.gen_keys(size=4028, passphrase="1234567890")
    rc = RSATools("public.pem", "private.pem", passphrase="1234567890")
    enc = rc.encrypt("Hello Word")
    print(enc)
    print("_"+rc.decrypt(enc)+"_")
