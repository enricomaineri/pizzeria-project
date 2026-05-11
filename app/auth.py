from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from fastapi import Request, HTTPException
from app.config import SECRET_KEY, ADMIN_USERNAME, ADMIN_PASSWORD

SESSION_COOKIE = "admin_session"
SESSION_MAX_AGE = 60 * 60 * 8  # 8 ore

serializer = URLSafeTimedSerializer(SECRET_KEY)


def create_session_token(username: str) -> str:
    return serializer.dumps(username, salt="admin-session")


def verify_session_token(token: str) -> str | None:
    try:
        username = serializer.loads(token, salt="admin-session", max_age=SESSION_MAX_AGE)
        return username
    except (BadSignature, SignatureExpired):
        return None


def check_admin_credentials(username: str, password: str) -> bool:
    return username == ADMIN_USERNAME and password == ADMIN_PASSWORD


def get_current_admin(request: Request) -> str | None:
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        return None
    return verify_session_token(token)


def require_admin(request: Request) -> str:
    admin = get_current_admin(request)
    if not admin:
        # HTTPException(401) blocca la route e viene catturata dall'exception handler
        # in main.py che fa il redirect a /admin/login
        raise HTTPException(status_code=401, detail="Non autenticato")
    return admin
