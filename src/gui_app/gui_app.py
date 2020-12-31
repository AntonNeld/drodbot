from queue import Empty
import tkinter
from tkinter import ttk

from common import GUIEvent
from .interpret_screen_app import InterpretScreenApp
from .playing_app import PlayingApp
from .classification_training_app import ClassificationTrainingApp

QUEUE_POLL_INTERVAL = 50

APPS = ["Play game", "Interpret screen", "Train classifier"]
DEFAULT_APP = 0


class GuiApp(tkinter.Frame):
    def __init__(self, root, event_loop, queue, bot, play_interface, classifier):
        super().__init__(root)
        self.root = root
        self.queue = queue
        self.selected_app_var = tkinter.StringVar(self)
        self.selected_app_var.set(APPS[DEFAULT_APP])
        self.create_widgets(event_loop, bot, play_interface, classifier)
        self.root.after(QUEUE_POLL_INTERVAL, self.check_queue)

    def create_widgets(self, event_loop, bot, play_interface, classifier):
        self.controls = tkinter.Frame(self)
        self.controls.pack(side=tkinter.BOTTOM)
        self.quit = tkinter.Button(
            self.controls, text="Quit", command=self.root.destroy
        )
        self.quit.pack(side=tkinter.RIGHT)
        self.app_select_menu = tkinter.OptionMenu(
            self.controls, self.selected_app_var, *APPS, command=self.switch_app
        )
        self.app_select_menu.pack(side=tkinter.LEFT)
        self.separator = ttk.Separator(self, orient="horizontal")
        self.separator.pack(side=tkinter.BOTTOM, fill=tkinter.X)
        self.interpret_screen_app = InterpretScreenApp(self, event_loop, play_interface)
        self.playing_app = PlayingApp(self, event_loop, bot)
        self.classification_training_app = ClassificationTrainingApp(
            self, event_loop, classifier
        )
        self.switch_app(APPS[DEFAULT_APP])

    def check_queue(self):
        try:
            item, *detail = self.queue.get(block=False)
            if item == GUIEvent.QUIT:
                self.root.destroy()
            elif item == GUIEvent.SET_INTERPRET_SCREEN_DATA:
                self.interpret_screen_app.set_data(*detail)
            elif item == GUIEvent.SET_TRAINING_DATA:
                self.classification_training_app.set_data(*detail)
        except Empty:
            pass
        self.root.after(QUEUE_POLL_INTERVAL, self.check_queue)

    def switch_app(self, app):
        self.playing_app.pack_forget()
        self.classification_training_app.pack_forget()
        self.interpret_screen_app.pack_forget()
        if app == "Play game":
            self.playing_app.pack(side=tkinter.TOP)
        elif app == "Interpret screen":
            self.interpret_screen_app.pack(side=tkinter.TOP)
        elif app == "Train classifier":
            self.classification_training_app.pack(side=tkinter.TOP)
