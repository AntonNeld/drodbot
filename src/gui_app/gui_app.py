import asyncio
from PIL import ImageTk, Image
from queue import Empty
import tkinter
import traceback

QUEUE_POLL_INTERVAL = 50

INSTRUCTIONS = "Press 'Go' and focus the DROD window to move randomly."
# The DROD window size is 1024x768, use half that for canvas to preserve aspect ratio
CANVAS_WIDTH = 512
CANVAS_HEIGHT = 384


class GuiApp(tkinter.Frame):
    def __init__(self, root, event_loop, queue, bot):
        super().__init__(root)
        self.root = root
        self.event_loop = event_loop
        self.queue = queue
        self.bot = bot
        self.pack()
        self.create_widgets()
        self.root.after(QUEUE_POLL_INTERVAL, self.check_queue)

    def create_widgets(self):
        self.label = tkinter.Label(
            self,
            text=INSTRUCTIONS,
        )
        self.label.pack(side=tkinter.TOP)
        self.canvas = tkinter.Canvas(
            self, width=CANVAS_WIDTH, height=CANVAS_HEIGHT, bg="white"
        )
        self.canvas.pack(side=tkinter.LEFT)
        self.quit = tkinter.Button(self, text="Quit", command=self.root.destroy)
        self.quit.pack(side=tkinter.RIGHT)
        self.go = tkinter.Button(self, text="Go", command=self.move_randomly_forever)
        self.go.pack(side=tkinter.RIGHT)
        self.go = tkinter.Button(self, text="Get view", command=self.show_view)
        self.go.pack(side=tkinter.RIGHT)

    def check_queue(self):
        try:
            item, detail = self.queue.get(block=False)
            if item == "quit":
                self.root.destroy()
            elif item == "display_image":
                resized_image = detail.resize(
                    (CANVAS_WIDTH, CANVAS_HEIGHT), Image.LANCZOS
                )
                # Assign to self.view to prevent from being garbage collected
                self.view = ImageTk.PhotoImage(image=resized_image)
                self.canvas.create_image(0, 0, image=self.view, anchor=tkinter.NW)
        except Empty:
            pass
        self.root.after(QUEUE_POLL_INTERVAL, self.check_queue)

    def run_coroutine(self, coroutine):
        async def wrapped_coroutine():
            try:
                await coroutine
            except Exception:
                traceback.print_exc()

        asyncio.run_coroutine_threadsafe(wrapped_coroutine(), self.event_loop)

    def move_randomly_forever(self):
        self.run_coroutine(self.bot.move_randomly_forever())

    def show_view(self):
        self.run_coroutine(self.bot.show_view())
