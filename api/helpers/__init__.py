import time

from texts import Texts
from helpers import get_readable_time

boot_time = time.time()
__version__ = "v1"


def about_text(name: str) -> str:
    """Render the /about card."""
    return Texts.ABOUT_TXT.format(
        name,
        get_readable_time(time.time() - boot_time),
        __version__,
    )
