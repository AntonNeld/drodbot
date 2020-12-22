import asyncio
import tkinter
import traceback

INSTRUCTIONS = "Press 'Go' and focus the DROD window to move randomly."


class GuiApp(tkinter.Frame):
    def __init__(self, root, event_loop, bot):
        super().__init__(root)
        self.root = root
        self.event_loop = event_loop
        self.bot = bot
        self.pack()
        self.create_widgets()

    def create_widgets(self):
        self.label = tkinter.Label(
            self,
            text=INSTRUCTIONS,
        )
        self.label.pack(side=tkinter.TOP)
        self.quit = tkinter.Button(self, text="Quit", command=self.root.destroy)
        self.quit.pack(side=tkinter.RIGHT)
        self.go = tkinter.Button(self, text="Go", command=self.move_randomly_forever)
        self.go.pack(side=tkinter.RIGHT)

    def run_coroutine(self, coroutine):
        async def wrapped_coroutine():
            try:
                await coroutine
            except Exception:
                traceback.print_exc()

        asyncio.run_coroutine_threadsafe(wrapped_coroutine(), self.event_loop)

    def move_randomly_forever(self):
        self.run_coroutine(self.bot.move_randomly_forever())
