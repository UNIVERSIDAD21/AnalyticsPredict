"""Permisos privados efectivos en POSIX y Windows; falla antes de escribir datos."""
import getpass
import os
from pathlib import Path
import subprocess


def proteger_privado(path: Path) -> None:
    path.chmod(0o600 if path.is_file() else 0o700)
    if os.name == 'nt':
        domain = os.environ.get('USERDOMAIN', '')
        user = getpass.getuser()
        principal = f'{domain}\\{user}' if domain else user
        rights = ':(F)' if path.is_file() else ':(OI)(CI)(F)'
        subprocess.run(['icacls', str(path), '/inheritance:r', '/grant:r',
                        principal + rights, '*S-1-5-18' + rights],
                       check=True, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
