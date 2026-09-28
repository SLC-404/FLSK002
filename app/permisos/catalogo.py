"""CATÁLOGO DE PERMISOS DEL SISTEMA.

Estos 13 permisos los crea "flask seed". Son "del sistema": no se pueden borrar ni renombrar
porque el código los usa en @permiso_requerido(...).

Formato del nombre:  accion-modulo   ->  ver-usuarios, crear-roles, eliminar-permisos...
Para un módulo nuevo (ej. productos) agrega aquí sus 4 permisos y corre "flask seed".
"""

ACCIONES = ["ver", "crear", "editar", "eliminar"]
MODULOS = ["permisos", "roles", "usuarios"]

PERMISOS_BASE = {"ver-inicio": "Ver el panel de inicio"}
for _modulo in MODULOS:
    for _accion in ACCIONES:
        PERMISOS_BASE[f"{_accion}-{_modulo}"] = f"{_accion.capitalize()} {_modulo}"

# Qué permisos recibe cada rol del sistema al correr "flask seed"
PERMISOS_POR_ROL = {
    "admin": list(PERMISOS_BASE),     # TODOS
    "usuario": ["ver-inicio"],
}
