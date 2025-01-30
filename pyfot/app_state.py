from typing import TypedDict, Union
from .data import Player
import urwid
import asyncio


class MonitorInfo(TypedDict):
    player: Player
    cancel_event: asyncio.Event

class MonitorState(TypedDict):
    monitors_count: int
    monitors_info_list: list[MonitorInfo]
    tasks: list[asyncio.Task]
    status_widget: urwid.Text

class AppState(TypedDict):
    urwid_loop: Union[None, urwid.MainLoop]
    monitor: MonitorState

app_state: AppState = {
    "urwid_loop": None,
    "monitor": { 
        "monitors_count": 0,
        "monitors_info_list": [],
        "tasks": [],
        "status_widget": urwid.Text("")
    }
}






