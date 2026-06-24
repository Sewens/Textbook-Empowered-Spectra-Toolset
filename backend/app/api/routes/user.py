from fastapi import APIRouter, Depends

from app.core.security import CurrentUser, available_roles, get_current_user, require_permission

router = APIRouter(prefix="/user", tags=["user"])


@router.get("/me")
def me(user: CurrentUser = Depends(get_current_user)) -> dict:
    return user.as_dict()


@router.get("/roles")
def roles(_user: CurrentUser = Depends(require_permission("user:manage"))) -> dict:
    roles_list = available_roles()
    return {"total": len(roles_list), "items": roles_list}
