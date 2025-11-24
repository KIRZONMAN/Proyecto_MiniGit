#!/usr/bin/env python3
"""
MiniGit reducido en Python.

Comandos principales:
    python minigit.py init
    python minigit.py add <archivo1> [archivo2 ...]
    python minigit.py commit "mensaje del commit"
    python minigit.py restore <id>

Extras:
    python minigit.py log
    python minigit.py status
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List

# Directorios base (siempre relativos al directorio actual)
REPO_DIR = Path.cwd()
MINIGIT_DIR = REPO_DIR / ".minigit"
COMMITS_DIR = MINIGIT_DIR / "commits"
OBJECTS_DIR = MINIGIT_DIR / "objects"
INDEX_FILE = MINIGIT_DIR / "index.json"
HEAD_FILE = MINIGIT_DIR / "head.json"


# ----------------- Utilidades -----------------

def load_json(path: Path, default: Any) -> Any:
    """Carga JSON desde 'path'. Si no existe o está corrupto, devuelve 'default'."""
    if not path.exists():
        return default
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return default


def save_json(path: Path, data: Any) -> None:
    """Guarda 'data' como JSON en 'path'."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def ensure_repo_initialized() -> None:
    """Verifica que .minigit exista, si no, termina el programa con un mensaje."""
    if not MINIGIT_DIR.is_dir():
        print("Error: este directorio no es un repositorio MiniGit.")
        print("Ejecuta primero: python minigit.py init")
        sys.exit(1)


def print_usage() -> None:
    print("Uso:")
    print("  python minigit.py init")
    print("  python minigit.py add <archivo1> [archivo2 ...]")
    print('  python minigit.py commit "mensaje del commit"')
    print("  python minigit.py restore <id>")
    print()
    print("Comandos extra:")
    print("  python minigit.py log")
    print("  python minigit.py status")


# ----------------- Comandos principales -----------------

def cmd_init() -> None:
    """Inicializa el repositorio MiniGit (.minigit)."""
    if MINIGIT_DIR.exists():
        print("MiniGit ya estaba inicializado en este directorio.")
        return

    # Crear estructura de directorios
    COMMITS_DIR.mkdir(parents=True, exist_ok=True)
    OBJECTS_DIR.mkdir(parents=True, exist_ok=True)

    # Crear index.json vacío
    save_json(INDEX_FILE, {"files": []})

    # Crear head.json inicial
    save_json(HEAD_FILE, {
        "last_commit_id": 0,
        "current_commit_id": 0
    })

    print("Repositorio MiniGit inicializado correctamente.")


def cmd_add(file_args: List[str]) -> None:
    """Agrega uno o más archivos al área de preparación (index)."""
    ensure_repo_initialized()

    if not file_args:
        print("Error: debes indicar al menos un archivo.")
        print("Ejemplo: python minigit.py add archivo1.txt")
        sys.exit(1)

    index = load_json(INDEX_FILE, {"files": []})
    staged = set(index.get("files", []))

    for arg in file_args:
        p = Path(arg)
        if not p.is_file():
            print(f"Advertencia: el archivo '{arg}' no existe y se omite.")
            continue

        try:
            rel = str(p.relative_to(REPO_DIR))
        except ValueError:
            # El archivo está fuera del repositorio actual
            rel = arg

        if rel not in staged:
            staged.add(rel)
            print(f"Agregado al área de preparación: {rel}")
        else:
            print(f"Ya estaba en el área de preparación: {rel}")

    index["files"] = sorted(staged)
    save_json(INDEX_FILE, index)


def cmd_commit(message: str) -> None:
    """Crea un nuevo commit con los archivos del área de preparación."""
    ensure_repo_initialized()

    index = load_json(INDEX_FILE, {"files": []})
    files = index.get("files", [])

    if not files:
        print("No hay archivos en el área de preparación (index).")
        print("Usa primero: python minigit.py add <archivo>")
        sys.exit(1)

    head = load_json(HEAD_FILE, {"last_commit_id": 0, "current_commit_id": 0})
    last_id = int(head.get("last_commit_id", 0))
    current_id = int(head.get("current_commit_id", 0))
    new_id = last_id + 1

    commit_files: Dict[str, str] = {}

    for rel in files:
        src = REPO_DIR / rel
        if not src.is_file():
            print(f"Error: el archivo '{rel}' ya no existe. Cancelo el commit.")
            sys.exit(1)

        # Nombre del archivo dentro de objects: <id>_<ruta_relativa_reemplazando_separadores>
        safe_rel = rel.replace("\\", "__").replace("/", "__")
        object_name = f"{new_id}_{safe_rel}"
        dest = OBJECTS_DIR / object_name

        # Copiar el contenido tal cual (modo binario)
        dest.parent.mkdir(parents=True, exist_ok=True)
        with src.open("rb") as f_src, dest.open("wb") as f_dest:
            f_dest.write(f_src.read())

        commit_files[rel] = object_name

    commit_data = {
        "id": new_id,
        "parent": current_id if current_id != 0 else None,
        "datetime": datetime.now().isoformat(timespec="seconds"),
        "message": message,
        "files": commit_files
    }

    save_json(COMMITS_DIR / f"{new_id}.json", commit_data)

    # Actualizar head.json
    head["last_commit_id"] = new_id
    head["current_commit_id"] = new_id
    save_json(HEAD_FILE, head)

    # Limpiar el index (staging vacío)
    save_json(INDEX_FILE, {"files": []})

    print(f"Commit {new_id} creado:")
    print(f'    Mensaje: "{message}"')
    print(f"    Archivos: {', '.join(sorted(commit_files.keys()))}")


def cmd_restore(commit_id_str: str) -> None:
    """Restaura los archivos a la versión almacenada en un commit dado."""
    ensure_repo_initialized()

    try:
        commit_id = int(commit_id_str)
    except ValueError:
        print("Error: el id del commit debe ser un número entero.")
        sys.exit(1)

    commit_path = COMMITS_DIR / f"{commit_id}.json"
    if not commit_path.is_file():
        print(f"Error: el commit {commit_id} no existe.")
        sys.exit(1)

    commit_data = load_json(commit_path, None)
    if not commit_data:
        print(f"Error: el commit {commit_id} está corrupto o vacío.")
        sys.exit(1)

    commit_files: Dict[str, str] = commit_data.get("files", {})

    if not commit_files:
        print(f"Advertencia: el commit {commit_id} no contiene archivos.")
        sys.exit(0)

    # Restaurar cada archivo
    for rel, object_name in commit_files.items():
        src = OBJECTS_DIR / object_name
        dest = REPO_DIR / rel

        if not src.is_file():
            print(f"Advertencia: el objeto {object_name} no existe, no puedo restaurar {rel}.")
            continue

        dest.parent.mkdir(parents=True, exist_ok=True)
        with src.open("rb") as f_src, dest.open("wb") as f_dest:
            f_dest.write(f_src.read())

        print(f"Restaurado: {rel}")

    # Actualizar HEAD para que apunte a este commit
    head = load_json(HEAD_FILE, {"last_commit_id": 0, "current_commit_id": 0})
    head["current_commit_id"] = commit_id
    # last_commit_id no se toca, porque la "historia" no cambia
    save_json(HEAD_FILE, head)

    print(f"Repositorio restaurado al commit {commit_id}.")
    if commit_data.get("message"):
        print(f'Mensaje del commit: "{commit_data["message"]}"')


# ----------------- Comandos extra -----------------

def cmd_log() -> None:
    """Muestra el historial de commits (similar a 'git log')."""
    ensure_repo_initialized()

    if not COMMITS_DIR.exists():
        print("No hay commits todavía.")
        return

    commit_files = sorted(COMMITS_DIR.glob("*.json"), key=lambda p: int(p.stem))

    if not commit_files:
        print("No hay commits todavía.")
        return

    print("Historial de commits:")
    print("-" * 40)
    for path in reversed(commit_files):  # del más reciente al más antiguo
        data = load_json(path, {})
        cid = data.get("id", path.stem)
        fecha = data.get("datetime", "desconocida")
        msg = data.get("message", "")
        archivos = data.get("files", {})
        print(f"Commit {cid}")
        print(f"Fecha: {fecha}")
        print(f'Mensaje: "{msg}"')
        print(f"Archivos: {', '.join(sorted(archivos.keys()))}")
        print("-" * 40)


def _list_all_repo_files() -> List[str]:
    """Lista todos los archivos del repo (excluyendo .minigit)."""
    files: List[str] = []
    for p in REPO_DIR.rglob("*"):
        if p.is_file() and ".minigit" not in p.parts:
            rel = str(p.relative_to(REPO_DIR))
            files.append(rel)
    return files


def cmd_status() -> None:
    """Muestra un resumen del estado actual del repositorio."""
    ensure_repo_initialized()

    index = load_json(INDEX_FILE, {"files": []})
    staged = set(index.get("files", []))

    head = load_json(HEAD_FILE, {"last_commit_id": 0, "current_commit_id": 0})
    current_id = int(head.get("current_commit_id", 0))

    committed_files: Dict[str, str] = {}
    if current_id != 0:
        commit_path = COMMITS_DIR / f"{current_id}.json"
        commit_data = load_json(commit_path, {})
        committed_files = commit_data.get("files", {})

    all_files = set(_list_all_repo_files())

    # Archivos modificados o borrados respecto al último commit
    modified: List[str] = []
    deleted: List[str] = []

    for rel, obj_name in committed_files.items():
        file_path = REPO_DIR / rel
        object_path = OBJECTS_DIR / obj_name

        if not file_path.exists():
            deleted.append(rel)
            continue

        if not object_path.is_file():
            # El objeto falta; lo consideramos "modificado"
            modified.append(rel)
            continue

        # Comparar contenidos
        with file_path.open("rb") as f1, object_path.open("rb") as f2:
            if f1.read() != f2.read():
                modified.append(rel)

    # Archivos no rastreados: están en el repo pero no en el último commit ni en el index
    tracked_or_staged = set(committed_files.keys()) | staged
    untracked = sorted(all_files - tracked_or_staged)

    print("=== MiniGit status ===")
    if current_id == 0:
        print("Aún no hay commits.")
    else:
        print(f"Último commit aplicado (HEAD): {current_id}")
    print()

    print("Archivos en el área de preparación (staged):")
    if staged:
        for f in sorted(staged):
            print(f"  {f}")
    else:
        print("  (ninguno)")
    print()

    print("Archivos modificados desde el último commit:")
    if modified:
        for f in sorted(modified):
            print(f"  {f}")
    else:
        print("  (ninguno)")
    print()

    print("Archivos eliminados desde el último commit:")
    if deleted:
        for f in sorted(deleted):
            print(f"  {f}")
    else:
        print("  (ninguno)")
    print()

    print("Archivos no rastreados (untracked):")
    if untracked:
        for f in untracked:
            print(f"  {f}")
    else:
        print("  (ninguno)")
    print()


# ----------------- Punto de entrada -----------------

def main(argv: List[str]) -> None:
    if len(argv) < 2:
        print_usage()
        sys.exit(1)

    command = argv[1]

    if command == "init":
        cmd_init()
    elif command == "add":
        cmd_add(argv[2:])
    elif command == "commit":
        if len(argv) < 3:
            print("Error: falta el mensaje del commit.")
            print('Ejemplo: python minigit.py commit "Mensaje inicial"')
            sys.exit(1)
        message = " ".join(argv[2:])
        cmd_commit(message)
    elif command == "restore":
        if len(argv) != 3:
            print("Uso: python minigit.py restore <id>")
            sys.exit(1)
        cmd_restore(argv[2])
    elif command == "log":
        cmd_log()
    elif command == "status":
        cmd_status()
    else:
        print(f"Comando desconocido: {command}")
        print_usage()
        sys.exit(1)


if __name__ == "__main__":
    main(sys.argv)
