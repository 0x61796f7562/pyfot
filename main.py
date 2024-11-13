
from ui import AppContainer,palette
from app_state import app_state
from logger import setup_logging
import urwid

def handle_exit(key):
    if key in ("q", "Q"):
        raise urwid.ExitMainLoop

def startMainLoop(top_widget):
    loop = urwid.MainLoop(top_widget, palette=palette, unhandled_input=handle_exit, event_loop=urwid.AsyncioEventLoop())

    app_state["urwid_loop"] = loop

    loop.run()



def main():
    setup_logging()

    app_container = AppContainer()
    startMainLoop(app_container) 



if __name__ == "__main__":
    main()




