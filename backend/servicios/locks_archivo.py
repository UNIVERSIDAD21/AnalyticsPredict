"""Exclusión entre procesos nativa, sin borrar locks ni desactivar protección."""
import errno
import os

if os.name == "nt":
    import msvcrt
else:
    import fcntl


def adquirir(fd: int) -> None:
    """Intenta adquirir sin esperar. El descriptor debe ser de lectura/escritura."""
    if os.name != "nt":
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return
    # El rango puede extenderse más allá de EOF. No escribir un byte antes de
    # adquirir: esa escritura competiría con un proceso que ya tiene el lock.
    os.lseek(fd, 0, os.SEEK_SET)
    try:
        msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
    except OSError as exc:
        if exc.errno in (errno.EACCES, errno.EAGAIN, errno.EDEADLK):
            raise BlockingIOError("Recurso ocupado por otro proceso") from exc
        raise


def liberar(fd: int) -> None:
    if os.name == "nt":
        os.lseek(fd, 0, os.SEEK_SET)
        msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
    else:
        fcntl.flock(fd, fcntl.LOCK_UN)
