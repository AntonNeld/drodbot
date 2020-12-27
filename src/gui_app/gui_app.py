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
LARGE_CANVAS_WIDTH = 836
LARGE_CANVAS_HEIGHT = 704


class GuiApp(tkinter.Frame):
    def __init__(self, root, event_loop, queue, bot, trainer):
        super().__init__(root)
        self.root = root
        self.event_loop = event_loop
        self.queue = queue
        self.bot = bot
        self.trainer = trainer
        self.selected_view_step = tkinter.StringVar(self)
        self.selected_view_step.set(list(ImageProcessingStep)[-1].value)
        self.selected_strategy = tkinter.StringVar(self)
        self.selected_strategy.set(list(Strategy)[0].value)
        self.enlarged_view = False
        self.raw_view_image = None
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
        self.toggle_view_size_button = tkinter.Button(
            self.view_controls, text="Enlarge view", command=self.toggle_view_size
        )
        self.toggle_view_size_button.pack(side=tkinter.RIGHT)
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
        self.playing_label = tkinter.Label(self.control_panel, text="While playing:")
        self.playing_label.pack(side=tkinter.TOP)
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
        self.editor_label = tkinter.Label(self.control_panel, text="In the editor:")
        self.editor_label.pack(side=tkinter.TOP)
        self.training_controls = tkinter.Frame(self.control_panel)
        self.training_controls.pack(side=tkinter.TOP)
        self.procure_training_data_button = tkinter.Button(
            self.training_controls,
            text="Procure training data",
            command=self.procure_training_data,
        )
        self.procure_training_data_button.pack(side=tkinter.LEFT)
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
                self.raw_view_image = detail
                self.draw_view()
        except Empty:
            pass
        self.root.after(QUEUE_POLL_INTERVAL, self.check_queue)

    def draw_view(self):
        if self.raw_view_image is not None:
            resized_image = self.raw_view_image.resize(
                (int(self.canvas["width"]), int(self.canvas["height"])), Image.LANCZOS
            )
            # Assign to self.view to prevent from being garbage collected
            self.view = ImageTk.PhotoImage(image=resized_image)
            self.canvas.create_image(0, 0, image=self.view, anchor=tkinter.NW)

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

    def show_view(self):
        step_value = self.selected_view_step.get()
        step = next(e for e in ImageProcessingStep if e.value == step_value)
        self.run_coroutine(self.bot.show_view(step))

    def toggle_view_size(self):
        if self.enlarged_view:
            self.enlarged_view = False
            self.canvas.configure(height=CANVAS_HEIGHT, width=CANVAS_WIDTH)
            self.toggle_view_size_button.configure(text="Enlarge view")
            self.draw_view()
        else:
            self.enlarged_view = True
            self.canvas.configure(height=LARGE_CANVAS_HEIGHT, width=LARGE_CANVAS_WIDTH)
            self.toggle_view_size_button.configure(text="Ensmall view")
            self.draw_view()

    def procure_training_data(self):
        self.run_coroutine(self.trainer.procure_training_data())
