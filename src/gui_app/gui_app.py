import asyncio
import tkinter

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
        self.text = tkinter.Text(
            self,
            wrap=tkinter.WORD,
            borderwidth=0,
            background=self.root["bg"],
            width=52,
            height=3,
        )
        self.text.insert(
            "1.0",
            INSTRUCTIONS,
        )
        # self.text.configure(state=tkinter.DISABLED)
        self.text.pack(side=tkinter.TOP)
        self.quit = tkinter.Button(self, text="Quit", command=self.root.destroy)
        self.quit.pack(side=tkinter.RIGHT)
        self.go = tkinter.Button(self, text="Go", command=self.move_randomly_forever)
        self.go.pack(side=tkinter.RIGHT)

    def move_randomly_forever(self):
        asyncio.run_coroutine_threadsafe(
            self.bot.move_randomly_forever(), self.event_loop
        )
