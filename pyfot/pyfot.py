
from requests.exceptions import HTTPError, ConnectionError
from .ui import AppContainer, palette
from .app_state import app_state
from .logger import setup_logging
import urwid
import sys
from datetime import datetime

def handle_exit(key):
    if key in ("q", "Q"):
        raise urwid.ExitMainLoop

def startMainLoop(top_widget):
    loop = urwid.MainLoop(top_widget, palette=palette, unhandled_input=handle_exit, event_loop=urwid.AsyncioEventLoop())

    app_state["urwid_loop"] = loop

    loop.run()



def main():
    setup_logging()

    matches_date = ""
    if len(sys.argv) >= 2: 
        date_arg = sys.argv[1]
        try:
            datetime.strptime(date_arg, "%Y-%m-%d")
            matches_date = date_arg
        except ValueError:
            print(f"Invalid date format: {date_arg}") 
            print(f"Use Year-Month-Day like: {datetime.today().date()}")
            return

    try:
        app_container = AppContainer(matches_date)
        startMainLoop(app_container) 
    except HTTPError:
        print("Verify if https://www.sofascore.com/ is accessible")
    except ConnectionError:
        print("Check your internet connection")



if __name__ == "__main__":
    main()




