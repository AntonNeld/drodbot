from queue import Empty
import tkinter
from tkinter import ttk

from common import GUIEvent
from .interpret_screen_app import InterpretScreenApp
from .playing_app import PlayingApp
from .classification_app import ClassificationApp

_QUEUE_POLL_INTERVAL = 50

_APPS = ["Play game", "Interpret screen", "Manage classifier"]
_DEFAULT_APP = 0


class GuiApp(tkinter.Frame):
    """The content of the main window.

    This class contains the sub-apps, and the menu used to switch
    between them. It also dispatches messages from the backend thread.

    Parameters
    ----------
    root
        The parent of the tkinter Frame.
    event_loop
        The asyncio event loop for the backend thread.
    queue
        The queue used for getting updates from the backend.
    bot
        The DRODbot that makes plans and performs actions.
    play_interface
        The interface toward DROD when playing.
    classifcation_app_backend
        The backend for the classification app.
    """

    def __init__(
        self, root, event_loop, queue, bot, play_interface, classification_app_backend
    ):
        super().__init__(root)
        self._main_window = root
        self._queue = queue
        self._selected_app_var = tkinter.StringVar(self)
        self._selected_app_var.set(_APPS[_DEFAULT_APP])
        self._main_window.after(_QUEUE_POLL_INTERVAL, self._check_queue)

        # Create widgets
        self._controls = tkinter.Frame(self)
        self._controls.pack(side=tkinter.BOTTOM)
        self._quit = tkinter.Button(
            self._controls, text="Quit", command=self._main_window.destroy
        )
        self._quit.pack(side=tkinter.RIGHT)
        self._app_select_menu = tkinter.OptionMenu(
            self._controls, self._selected_app_var, *_APPS, command=self._switch_app
        )
        self._app_select_menu.pack(side=tkinter.LEFT)
        self._separator = ttk.Separator(self, orient="horizontal")
        self._separator.pack(side=tkinter.BOTTOM, fill=tkinter.X)
        self._interpret_screen_app = InterpretScreenApp(
            self, event_loop, play_interface
        )
        self._playing_app = PlayingApp(self, event_loop, bot)
        self._classification_app = ClassificationApp(
            self, event_loop, classification_app_backend
        )
        self._switch_app(_APPS[_DEFAULT_APP])

    def _check_queue(self):
        try:
            item, *detail = self._queue.get(block=False)
            if item == GUIEvent.QUIT:
                self._main_window.destroy()
            elif item == GUIEvent.SET_INTERPRET_SCREEN_DATA:
                self._interpret_screen_app.set_data(*detail)
            elif item == GUIEvent.SET_TRAINING_DATA:
                self._classification_app.set_data(*detail)
        except Empty:
            pass
        self._main_window.after(_QUEUE_POLL_INTERVAL, self._check_queue)

    def _switch_app(self, app):
        self._playing_app.pack_forget()
        self._classification_app.pack_forget()
        self._interpret_screen_app.pack_forget()
        if app == "Play game":
            self._playing_app.pack(side=tkinter.TOP)
        elif app == "Interpret screen":
            self._interpret_screen_app.pack(side=tkinter.TOP)
        elif app == "Manage classifier":
            self._classification_app.pack(side=tkinter.TOP)
