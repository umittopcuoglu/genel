"""
RBAC rol kontrolü: Dekoratör veya dependency ile belirli rollere izin verme.
"""
from functools import wraps
from typing import List, Set, Callable, Optional
from fastapi import Depends, HTTPException, status
from app.models.user import User
from app.core.auth import get_current_user

# Tanımlı roller (sabit)
ALL_ROLES = {
    "superadmin", "manager", "frontdesk", "housekeeping",
    "accounting", "maintenance", "fb", "hr", "guest"
}


def require_roles(allowed_roles: List[str]):
    """
    Belirli rollere sahip kullanıcıları endpoint'e kabul eden dependency.
    Kullanım: @router.get("/admin", dependencies=[Depends(require_roles(["superadmin"]))])
    veya: def endpoint(..., current_user: User = Depends(require_roles(["manager","frontdesk"])))
    """
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": {
                        "code": "INSUFFICIENT_PERMISSIONS",
                        "message": "Bu işlem için yetkiniz yok.",
                        "details": {"required_roles": allowed_roles, "user_role": current_user.role}
                    }
                }
            )
        return current_user
    return role_checker


def require_roles_decorator(allowed_roles: List[str]):
    """
    Dekoratör versiyonu (opsiyonel). Kullanım: @require_roles_decorator(["superadmin"])
    Ancak FastAPI'de Depends daha uygundur.
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, current_user: User = Depends(get_current_user), **kwargs):
            if current_user.role not in allowed_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "error": {
                            "code": "INSUFFICIENT_PERMISSIONS",
                            "message": "Bu işlem için yetkiniz yok.",
                            "details": {"required_roles": allowed_roles, "user_role": current_user.role}
                        }
                    }
                )
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator
