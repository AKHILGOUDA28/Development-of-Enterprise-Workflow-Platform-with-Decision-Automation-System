"""
auth.py
-------
Security & JWT Authentication with Role-Based Access Control (RBAC).

Roles:
  - Employee: Can submit incidents and view own status
  - IT Support: Can view, assign, and update incidents
  - Admin: Can manage system, trigger HITL approvals, test failure modes
"""

import os
from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "enterprise-ai-triage-secret-2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

security = HTTPBearer(auto_error=False)

# Dynamic database proxy for user lookup (backward compatible with USERS_DB)
class UsersDbProxy:
    def __getitem__(self, key):
        from database.connection import db_manager
        user = db_manager.fetchone("SELECT * FROM users WHERE LOWER(username) = ?", (key.lower().strip(),))
        if not user:
            raise KeyError(key)
        return user
    
    def __contains__(self, key):
        from database.connection import db_manager
        user = db_manager.fetchone("SELECT * FROM users WHERE LOWER(username) = ?", (key.lower().strip(),))
        return user is not None

USERS_DB = UsersDbProxy()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> dict:
    if not credentials:
        # Default fallback to Guest/Employee if token omitted in basic mode
        return {
            "username": "emp1024",
            "name": "Akhil Gouda",
            "role": "Employee",
            "employee_id": "EMP1024",
            "email": "akhil@company.com"
        }
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

def require_role(roles: list):
    def role_checker(current_user: dict = Depends(verify_token)):
        if current_user.get("role") not in roles:
            raise HTTPException(
                status_code=403,
                detail=f"Access denied. Required role: {', '.join(roles)}. Your role: {current_user.get('role')}"
            )
        return current_user
    return role_checker
