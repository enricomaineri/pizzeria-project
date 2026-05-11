from slowapi import Limiter
from slowapi.util import get_remote_address

# Istanza condivisa del rate limiter.
# Importata da main.py (registrazione sull'app) e da auth_routes.py (decorator).
limiter = Limiter(key_func=get_remote_address)
