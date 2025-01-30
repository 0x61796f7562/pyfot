from threading import Event
from .utils import notify
from .api import get_substitution_incidents
from .data import Player
from .app_state import app_state
import asyncio
import logging

logger = logging.getLogger(__name__)

coro_lock = asyncio.Lock()

def set_status_text(_, text):
    app_state["monitor"]["status_widget"].set_text(text)

async def add_monitor(monitor_info) -> None:
    async with coro_lock:
        app_state["monitor"]["monitors_count"] += 1
        app_state["monitor"]["monitors_info_list"].append(monitor_info)
        # app_state["monitor"]["status_widget"].set_text(f'[Active Monitors: {app_state["monitor"]["monitors_count"]}]')
        text = f'[Active Monitors: {app_state["monitor"]["monitors_count"]}]'
        if app_state["urwid_loop"]:
            app_state["urwid_loop"].set_alarm_in(0, set_status_text, text)

async def remove_monitor(monitor_info) -> None:
    async with coro_lock:
        app_state["monitor"]["monitors_count"] -= 1
        tmp_list = []
        for index, mi in enumerate(app_state["monitor"]["monitors_info_list"]): 
            if mi["player"] != monitor_info["player"]:
                tmp_list.append(mi)
            else:
                task = app_state["monitor"]["tasks"][index]
                app_state["monitor"]["tasks"].remove(task)
        app_state["monitor"]["monitors_info_list"] = tmp_list

        # app_state["monitor"]["status_widget"].set_text(f'[Active Monitors: {app_state["monitor"]["monitors_count"]}]')
        text = f'[Active Monitors: {app_state["monitor"]["monitors_count"]}]'
        if app_state["urwid_loop"]:
            app_state["urwid_loop"].set_alarm_in(0, set_status_text, text)


def monitor_player_substitution(match_id: int, player: Player) -> None:
    notify("Player Monitoring", f'Substitution Monitoring Started For {player.name}', "mute", 1)

    async def monitoring_work(match_id: int, player: Player, cancel_event: Event) -> bool:
        await add_monitor({"player": player, "cancel_event": cancel_event})

        try:
            while True:
                if cancel_event.is_set():
                    await remove_monitor({"player": player, "cancel_event": cancel_event})
                    return False

                subs_incidents = get_substitution_incidents(match_id)

                if subs_incidents:
                    subs_incident = player.is_player_in(subs_incidents)
                    if subs_incident:
                        await remove_monitor({"player": player, "cancel_event": cancel_event})
                        notify("Player Monitoring", f'{subs_incident.minute}\'  {subs_incident.playerIn.name} is In', "success")
                        return True
                    subs_incident = player.is_player_out(subs_incidents)
                    if subs_incident:
                        await remove_monitor({"player": player, "cancel_event": cancel_event})
                        notify("Player Monitoring", f'{subs_incident.minute}\'  {subs_incident.playerOut.name} is Out', "success")
                        return True

                await asyncio.sleep(60)
        except Exception as e:
            logger.error(e)
            await remove_monitor({"player": player, "cancel_event": cancel_event})
            return False


    cancel_event = Event()
    task = asyncio.create_task(monitoring_work(match_id, player, cancel_event))
    app_state["monitor"]["tasks"].append(task)


def canncel_monitoring():
    for index, mi in enumerate(app_state["monitor"]["monitors_info_list"]):
        mi["cancel_event"].set()
        app_state["monitor"]["tasks"][index].cancel()
    app_state["monitor"]["monitors_count"] = 0



