"""Local development RBAC helpers for the FastAPI backend."""

from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status


@dataclass(frozen=True)
class Role:
    code: str
    name_zh: str
    description: str
    permissions: frozenset[str]


READ_PERMISSIONS = frozenset({
    "project:read",
    "group:read",
    "compound:read",
    "spectrum:read",
    "evidence:read",
    "term:read",
    "asset:read",
})

DATA_ADMIN_PERMISSIONS = READ_PERMISSIONS | frozenset({
    "analysis:create",
    "extraction:create",
    "extraction:update",
    "extraction:review",
    "schema:read",
})

SITE_ADMIN_PERMISSIONS = DATA_ADMIN_PERMISSIONS | frozenset({
    "schema:publish",
    "user:manage",
    "role:manage",
    "site:admin",
})

ROLES: dict[str, Role] = {
    "ordinary_user": Role(
        code="ordinary_user",
        name_zh="普通用户",
        description="可浏览谱学知识库、检索波数、查看证据和谱图。",
        permissions=READ_PERMISSIONS,
    ),
    "data_admin": Role(
        code="data_admin",
        name_zh="数据管理员",
        description="可进行普通浏览，并可提交分析、维护抽取数据和审阅数据。",
        permissions=DATA_ADMIN_PERMISSIONS,
    ),
    "site_admin": Role(
        code="site_admin",
        name_zh="网站管理员",
        description="拥有数据管理员权限，并可管理用户、角色和站点级配置。",
        permissions=SITE_ADMIN_PERMISSIONS,
    ),
}

ROLE_ALIASES = {
    "ordinary": "ordinary_user",
    "reader": "ordinary_user",
    "user": "ordinary_user",
    "普通用户": "ordinary_user",
    "data-manager": "data_admin",
    "data_manager": "data_admin",
    "curator": "data_admin",
    "数据管理员": "data_admin",
    "admin": "site_admin",
    "administrator": "site_admin",
    "site-admin": "site_admin",
    "site_admin": "site_admin",
    "网站管理员": "site_admin",
}


@dataclass(frozen=True)
class CurrentUser:
    id: str
    name: str
    role: Role

    @property
    def permissions(self) -> frozenset[str]:
        return self.role.permissions

    def as_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "role": {
                "code": self.role.code,
                "name_zh": self.role.name_zh,
                "description": self.role.description,
            },
            "permissions": sorted(self.permissions),
        }


def available_roles() -> list[dict]:
    return [
        {
            "code": role.code,
            "name_zh": role.name_zh,
            "description": role.description,
            "permissions": sorted(role.permissions),
        }
        for role in ROLES.values()
    ]


def _resolve_role(role_header: str | None) -> Role:
    requested = (role_header or "ordinary_user").strip()
    code = ROLE_ALIASES.get(requested, requested)
    role = ROLES.get(code)
    if role is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Unknown role: {requested}",
        )
    return role


def get_current_user(x_user_role: Annotated[str | None, Header(alias="X-User-Role")] = None) -> CurrentUser:
    role = _resolve_role(x_user_role)
    return CurrentUser(id=f"local-{role.code}", name=role.name_zh, role=role)


def require_permission(permission: str):
    def dependency(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if permission not in user.permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission required: {permission}",
            )
        return user

    return dependency
