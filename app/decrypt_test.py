# decrypt_test.py
import sys
from cryptography.fernet import Fernet

if len(sys.argv) != 3:
    print("Użycie: python decrypt_test.py <FERNET_KEY> <TOKEN>")
    sys.exit(1)

key = sys.argv[1].encode()
token = sys.argv[2].encode()

try:
    f = Fernet(key)
    print("ODSZYFROWANE:", f.decrypt(token).decode())
except Exception as e:
    print("Błąd odszyfrowania:", e)
