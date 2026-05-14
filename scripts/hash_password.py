# Genera l'hash bcrypt di una password da mettere in ADMIN_PASSWORD_HASH nel .env
# Uso: python scripts/hash_password.py <password>
#
# Esempio:
#   python scripts/hash_password.py mia_password_sicura
#   → $2b$12$...
#   Copia l'output nel .env come: ADMIN_PASSWORD_HASH=$2b$12$...

import sys
import bcrypt


def main():
    if len(sys.argv) != 2:
        print("Uso: python scripts/hash_password.py <password>")
        sys.exit(1)

    password = sys.argv[1].encode()
    hashed = bcrypt.hashpw(password, bcrypt.gensalt()).decode()
    print(hashed)


if __name__ == "__main__":
    main()
