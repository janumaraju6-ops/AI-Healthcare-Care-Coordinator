from typing import Any
from fastapi import HTTPException, status


def validate_role(user: Any, allowed_roles: list[str]) -> None:
    if user.role not in allowed_roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Access forbidden')
