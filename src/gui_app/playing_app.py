import asyncio
import tkinter
import traceback

from common import Strategy


class PlayingApp(tkinter.Frame):
    def __init__(self, root, event_loop, bot):
        super().__init__(root)
        self.event_loop = event_loop
        self.bot = bot
        self.selected_strategy = tkinter.StringVar(self)
        self.selected_strategy.set(list(Strategy)[0].value)
        self.create_widgets()

    def create_widgets(self):
        self.control_panel = tkinter.Frame(self)
        self.control_panel.pack(side=tkinter.RIGHT)
        self.run_controls = tkinter.Frame(self.control_panel)
        self.run_controls.pack(side=tkinter.TOP)
        self.strategy_dropdown = tkinter.OptionMenu(
            self.run_controls, self.selected_strategy, *[s.value for s in Strategy]
        )
        self.strategy_dropdown.pack(side=tkinter.LEFT)
        self.go = tkinter.Button(
            self.run_controls, text="Go", command=self.run_strategy
        )
        self.go.pack(side=tkinter.RIGHT)

    def run_coroutine(self, coroutine):
        async def wrapped_coroutine():
            try:
                await coroutine
            except Exception:
                traceback.print_exc()

        asyncio.run_coroutine_threadsafe(wrapped_coroutine(), self.event_loop)

    def run_strategy(self):
        strategy_value = self.selected_strategy.get()
        strategy = next(e for e in Strategy if e.value == strategy_value)
        self.run_coroutine(self.bot.run_strategy(strategy))
