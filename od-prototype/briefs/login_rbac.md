# OpenDesign Brief — Login and RBAC

Feature: Login, session, role-aware navigation

Primary user: admin / curator / reviewer / reader

Screens:

1. Login
2. Current user profile menu
3. User management table
4. Role/permission matrix
5. Forbidden state

Required states:

- invalid credentials
- inactive user
- session expired
- insufficient permission
- admin can manage users/roles
- reader sees read-only navigation

React mapping:

- LoginPage
- AuthProvider
- RequireAuth
- RequirePermission
- UserManagementPage
- RoleManagementPage
