import asyncio
from PIL import ImageTk, Image
from queue import Empty
import tkinter
import traceback

from common import GUIEvent, ImageProcessingStep, Strategy

QUEUE_POLL_INTERVAL = 50

# The DROD room size is 836x704, use half that for canvas to preserve aspect ratio
CANVAS_WIDTH = 418
CANVAS_HEIGHT = 352


class GuiApp(tkinter.Frame):
    def __init__(self, root, event_loop, queue, bot):
        super().__init__(root)
        self.root = root
        self.event_loop = event_loop
        self.queue = queue
        self.bot = bot
        self.selected_view_step = tkinter.StringVar(self)
        self.selected_view_step.set(list(ImageProcessingStep)[-1].value)
        self.selected_strategy = tkinter.StringVar(self)
        self.selected_strategy.set(list(Strategy)[0].value)
        self.pack()
        self.create_widgets()
        self.root.after(QUEUE_POLL_INTERVAL, self.check_queue)

    def create_widgets(self):
        self.canvas = tkinter.Canvas(
            self, width=CANVAS_WIDTH, height=CANVAS_HEIGHT, bg="white"
        )
        self.canvas.pack(side=tkinter.LEFT)
        self.control_panel = tkinter.Frame(self)
        self.control_panel.pack(side=tkinter.RIGHT)
        self.view_controls = tkinter.Frame(self.control_panel)
        self.view_controls.pack(side=tkinter.TOP)
        self.get_view = tkinter.Button(
            self.view_controls, text="Get view", command=self.show_view
        )
        self.get_view.pack(side=tkinter.RIGHT)
        self.view_step_dropdown = tkinter.OptionMenu(
            self.view_controls,
            self.selected_view_step,
            *[s.value for s in ImageProcessingStep]
        )
        self.view_step_dropdown.pack(side=tkinter.LEFT)
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
        self.quit = tkinter.Button(
            self.control_panel, text="Quit", command=self.root.destroy
        )
        self.quit.pack(side=tkinter.TOP)

    def check_queue(self):
        try:
            item, detail = self.queue.get(block=False)
            if item == GUIEvent.QUIT:
                self.root.destroy()
            elif item == GUIEvent.DISPLAY_IMAGE:
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

    def run_strategy(self):
        # Currently only moves randomly
        self.run_coroutine(self.bot.move_randomly_forever())

    def show_view(self):
        step_value = self.selected_view_step.get()
        step = next(e for e in ImageProcessingStep if e.value == step_value)
        self.run_coroutine(self.bot.show_view(step))
