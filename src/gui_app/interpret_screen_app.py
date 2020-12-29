import asyncio
import PIL
from PIL import ImageTk, Image
import tkinter
import traceback

from common import ImageProcessingStep

# The DROD room size is 836x704, use half that for canvas to preserve aspect ratio
CANVAS_WIDTH = 418
CANVAS_HEIGHT = 352
LARGE_CANVAS_WIDTH = 836
LARGE_CANVAS_HEIGHT = 704


class InterpretScreenApp(tkinter.Frame):
    def __init__(self, root, event_loop, bot):
        super().__init__(root)
        self.root = root
        self.event_loop = event_loop
        self.bot = bot
        self.selected_view_step = tkinter.StringVar(self)
        self.selected_view_step.set(list(ImageProcessingStep)[-1].value)
        self.enlarged_view = False
        self.raw_view_image = None
        self.create_widgets()

    def create_widgets(self):
        self.canvas = tkinter.Canvas(
            self, width=CANVAS_WIDTH, height=CANVAS_HEIGHT, bg="white"
        )
        self.canvas.pack(side=tkinter.LEFT)
        self.control_panel = tkinter.Frame(self)
        self.control_panel.pack(side=tkinter.RIGHT)
        self.toggle_view_size_button = tkinter.Button(
            self.control_panel, text="Enlarge view", command=self.toggle_view_size
        )
        self.toggle_view_size_button.pack(side=tkinter.BOTTOM)
        self.get_view = tkinter.Button(
            self.control_panel, text="Get view", command=self.show_view
        )
        self.get_view.pack(side=tkinter.BOTTOM)
        self.view_step_dropdown = tkinter.OptionMenu(
            self.control_panel,
            self.selected_view_step,
            *[s.value for s in ImageProcessingStep]
        )
        self.view_step_dropdown.pack(side=tkinter.BOTTOM)

    def set_image(self, image):
        self.raw_view_image = PIL.Image.fromarray(image)
        self.draw_view()

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
