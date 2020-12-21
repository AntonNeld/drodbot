import tkinter

UPDATE_INTERVAL = 100

INSTRUCTIONS = """I will now move randomly. Focus the DROD window,
then focus this window and press 'Go'.
Move the mouse to the corner of the screen to exit.
"""


class GuiApp(tkinter.Frame):
    def __init__(self, root=None):
        super().__init__(root)
        self.root = root
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
        self.text.pack(side=tkinter.TOP)
        self.go = tkinter.Button(self, text="Go", command=self.root.destroy)
        self.go.pack(side=tkinter.BOTTOM)
