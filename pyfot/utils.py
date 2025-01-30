from typing import Literal
from plyer import notification
from pathlib import Path
import chime




def notify(title: str, message: str, status_sound: Literal["success", "info", "error", "mute"], timeout=2) -> None:
    icon_name = "football.png"
    icon_path = str((Path(__file__).parent / "assets" / icon_name).resolve())

    if status_sound == "info":
        chime.info()
    elif status_sound == "error":
        chime.error()
    elif status_sound == "success":
        chime.success()

    notification.notify(title, message, timeout=timeout, app_name="PyFot", app_icon=icon_path)


