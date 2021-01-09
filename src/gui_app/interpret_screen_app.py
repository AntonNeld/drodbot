import asyncio

import PIL
from PIL import ImageTk, Image
import tkinter
import traceback

from common import (
    ImageProcessingStep,
    TILE_SIZE,
)
from .util import tile_to_text, annotate_room_image_with_tile_contents

# The DROD room size is 836x704, use half that for canvas to preserve aspect ratio
CANVAS_WIDTH = 418
CANVAS_HEIGHT = 352
LARGE_CANVAS_WIDTH = 836
LARGE_CANVAS_HEIGHT = 704


class InterpretScreenApp(tkinter.Frame):
    def __init__(self, root, event_loop, interface):
        super().__init__(root)
        self.event_loop = event_loop
        self.interface = interface
        self.selected_view_step = tkinter.StringVar(self)
        self.selected_view_step.set(list(ImageProcessingStep)[-1].value)
        self.enlarged_view = False
        self.raw_view_image = None
        self.room = None
        self.create_widgets()

    def create_widgets(self):
        self.canvas = tkinter.Canvas(
            self, width=CANVAS_WIDTH, height=CANVAS_HEIGHT, bg="white"
        )
        self.canvas.bind("<Button-1>", self.clicked_canvas)
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
        self.tile_content = tkinter.Label(self.control_panel, text="")
        self.tile_content.pack(side=tkinter.BOTTOM)

    def set_data(self, image, room=None):
        self.raw_view_image = image
        self.room = room
        self.draw_view()

    def draw_view(self):
        if self.raw_view_image is not None:
            if self.room is not None:
                # Let's assume the image is of the room here. If that is not the case,
                # the below function will produce weird results.
                image = annotate_room_image_with_tile_contents(
                    self.raw_view_image, self.room
                )
            else:
                image = self.raw_view_image
            pil_image = PIL.Image.fromarray(image)
            resized_image = pil_image.resize(
                (int(self.canvas["width"]), int(self.canvas["height"])), Image.NEAREST
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
        self.run_coroutine(self.interface.show_view_step(step))

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

    def clicked_canvas(self, event):
        if self.enlarged_view:
            x = event.x // TILE_SIZE
            y = event.y // TILE_SIZE
        else:
            x = event.x // (TILE_SIZE // 2)
            y = event.y // (TILE_SIZE // 2)
        if self.room is not None:
            tile = self.room.get_tile((x, y))
            self.tile_content.config(text=tile_to_text(tile))
        elif self.raw_view_image.shape == (32, 38, 3):
            # This is probably the minimap, so showing the color is nice
            color = self.raw_view_image[y, x, :]
            self.tile_content.config(text=str(color))
