import tkinter
from tkinter import ttk

from .interpret_screen_app import InterpretScreenApp
from .playing_app import PlayingApp
from .room_solver_app import RoomSolverApp
from .classification_app import ClassificationApp
from .room_tester_app import RoomTesterApp, RoomTesterAppBackend

_APPS = [
    "Play game",
    "Interpret screen",
    "Examine room solver",
    "Manage classifier",
    "Regression test rooms",
]
_DEFAULT_APP = 0


class MainApp(tkinter.Frame):
    """The content of the main window.

    This class contains the sub-apps, and the menu used to switch
    between them. It also dispatches messages from the backend thread.

    Parameters
    ----------
    root
        The parent of the tkinter Frame.
    event_loop
        The asyncio event loop for the backend thread.
    playing_app_backend
        The backend for the playing app.
    interpret_screen_app_backend
        The backend for the interpret screen app.
    classification_app_backend
        The backend for the classification app.
    room_tester_app_backend
        The backend for the room tester app.
    """

    def __init__(
        self,
        root,
        event_loop,
        playing_app_backend,
        interpret_screen_app_backend,
        room_solver_app_backend,
        classification_app_backend,
        room_tester_app_backend: RoomTesterAppBackend,
    ):
        super().__init__(root)
        self._main_window = root
        self._selected_app_var = tkinter.StringVar(self)
        self._selected_app_var.set(_APPS[_DEFAULT_APP])

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
            self, event_loop, interpret_screen_app_backend
        )
        self._playing_app = PlayingApp(self, playing_app_backend)
        self._classification_app = ClassificationApp(
            self, event_loop, classification_app_backend
        )
        self._room_solver_app = RoomSolverApp(self, event_loop, room_solver_app_backend)
        self._room_tester_app = RoomTesterApp(self, room_tester_app_backend)
        self._switch_app(_APPS[_DEFAULT_APP])

    def _switch_app(self, app):
        self._playing_app.pack_forget()
        self._classification_app.pack_forget()
        self._interpret_screen_app.pack_forget()
        self._room_solver_app.pack_forget()
        self._room_tester_app.pack_forget()
        if app == "Play game":
            self._playing_app.pack(side=tkinter.TOP)
        elif app == "Interpret screen":
            self._interpret_screen_app.pack(side=tkinter.TOP)
        elif app == "Examine room solver":
            self._room_solver_app.pack(side=tkinter.TOP)
            # Needed for keybindings to work
            self._room_solver_app.focus_set()
        elif app == "Manage classifier":
            self._classification_app.pack(side=tkinter.TOP)
        elif app == "Regression test rooms":
            self._room_tester_app.pack(side=tkinter.TOP)
