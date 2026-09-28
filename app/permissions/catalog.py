"""SYSTEM PERMISSIONS CATALOG.

"flask seed" creates these permissions. They are "system" permissions: they can't be
deleted or renamed because the code uses them in @permission_required(...).

Name format:  action-module  ->  view-users, create-roles, delete-permissions...
For a new module (e.g. products) add it to MODULES and run "flask seed".
"""

ACTIONS = ["view", "create", "edit", "delete"]
MODULES = ["permissions", "roles", "users", "categories", "products"]

BASE_PERMISSIONS = {"view-dashboard": "Ver el panel de inicio"}
for _module in MODULES:
    for _action in ACTIONS:
        BASE_PERMISSIONS[f"{_action}-{_module}"] = f"{_action.capitalize()} {_module}"

# Which permissions each system role gets when running "flask seed"
ROLE_PERMISSIONS = {
    "admin": list(BASE_PERMISSIONS),     # ALL of them
    "user": ["view-dashboard"],
}
