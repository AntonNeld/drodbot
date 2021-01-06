import asyncio
import math

import numpy
import PIL
from PIL import ImageTk, Image
import tkinter
import traceback

from .util import tile_to_text

CANVAS_WIDTH = 88
CANVAS_HEIGHT = 88


class ClassificationTrainingApp(tkinter.Frame):
    def __init__(self, root, event_loop, classifier):
        super().__init__(root)
        self.root = root
        self.event_loop = event_loop
        self.classifier = classifier
        self.raw_data = []
        self.data = []
        self.data_index = None
        self.only_wrong = tkinter.BooleanVar(self)
        self.only_wrong.set(False)
        self.selected_debug_step = tkinter.StringVar(self)
        self.selected_debug_step.set("Raw tile")
        self.create_widgets()

    def create_widgets(self):
        self.tile_area = tkinter.Frame(self)
        self.tile_area.pack(side=tkinter.LEFT)
        self.canvas = tkinter.Canvas(
            self.tile_area, width=CANVAS_WIDTH, height=CANVAS_HEIGHT, bg="white"
        )
        self.canvas.pack(side=tkinter.TOP)
        self.browse_buttons = tkinter.Frame(self.tile_area)
        self.browse_buttons.pack(side=tkinter.TOP)
        self.next_tile_button = tkinter.Button(
            self.browse_buttons, text=">", state="disable", command=self.next_tile
        )
        self.next_tile_button.pack(side=tkinter.RIGHT)
        self.previous_tile_button = tkinter.Button(
            self.browse_buttons, text="<", state="disable", command=self.previous_tile
        )
        self.previous_tile_button.pack(side=tkinter.RIGHT)
        self.only_wrong_checkbox = tkinter.Checkbutton(
            self.tile_area,
            text="Only wrongly predicted",
            variable=self.only_wrong,
            command=self.filter_data,
        )
        self.only_wrong_checkbox.pack(side=tkinter.TOP)
        self.debug_step_dropdown = tkinter.OptionMenu(
            self.tile_area,
            self.selected_debug_step,
            "Raw tile",
            command=self.show_tile,
        )
        self.debug_step_dropdown.pack(side=tkinter.TOP)

        self.details_area = tkinter.Frame(self)
        self.details_area.pack(side=tkinter.LEFT)
        self.tile_file_name = tkinter.Label(self.details_area, text="")
        self.tile_file_name.pack(side=tkinter.TOP)
        self.tile_content_area = tkinter.Frame(self.details_area)
        self.tile_content_area.pack(side=tkinter.TOP)
        self.real_tile_content = tkinter.Label(self.tile_content_area, text="")
        self.real_tile_content.pack(side=tkinter.LEFT)
        self.predicted_tile_content = tkinter.Label(self.tile_content_area, text="")
        self.predicted_tile_content.pack(side=tkinter.LEFT)

        self.control_panel = tkinter.Frame(self)
        self.control_panel.pack(side=tkinter.LEFT)
        self.generate_training_data_button = tkinter.Button(
            self.control_panel,
            text="Generate training data",
            command=self.generate_training_data,
        )
        self.generate_training_data_button.pack(side=tkinter.TOP)
        self.load_training_data_button = tkinter.Button(
            self.control_panel,
            text="Load training data",
            command=self.load_training_data,
        )
        self.load_training_data_button.pack(side=tkinter.TOP)
        self.train_model_button = tkinter.Button(
            self.control_panel,
            text="Train model",
            command=self.train_model,
        )
        self.train_model_button.pack(side=tkinter.TOP)
        self.save_weights_button = tkinter.Button(
            self.control_panel, text="Save model weights", command=self.save_weights
        )
        self.save_weights_button.pack(side=tkinter.TOP)

    def set_data(self, data):
        self.raw_data = data
        self.filter_data()

    def filter_data(self):
        old_filenames = [tile["file_name"] for tile in self.data]
        if self.only_wrong.get():
            self.data = [
                t for t in self.raw_data if t["real_content"] != t["predicted_content"]
            ]
        else:
            self.data = self.raw_data
        if len(self.data) > 0:
            # Keep the index if it's the same files, since this means we're just
            # updating the data
            if [tile["file_name"] for tile in self.data] != old_filenames:
                self.data_index = 0
            self.show_tile()
        else:
            self.data_index = None
            self.canvas.delete("all")
            self.tile_file_name.config(text="")
            self.tile_content.config(text="")
        self.set_browse_button_state()

    def set_browse_button_state(self):
        if self.data_index is None:
            self.next_tile_button.config(state="disable")
            self.previous_tile_button.config(state="disable")
        else:
            self.next_tile_button.config(
                state="disable" if self.data_index == len(self.data) - 1 else "normal"
            )
            self.previous_tile_button.config(
                state="disable" if self.data_index == 0 else "normal"
            )

    def show_tile(self, *args):
        # Add *args because the dropdown gives an unused argument to this function
        index = self.data_index
        # Get the possible debug steps
        debug_steps = [name for name, image in self.data[index]["debug_images"]]
        if self.selected_debug_step.get() not in debug_steps:
            self.selected_debug_step.set("Raw tile")
        menu = self.debug_step_dropdown["menu"]
        menu.delete(0, "end")

        def selected_option(value):
            self.selected_debug_step.set(value)
            self.show_tile()

        for step in ["Raw tile", *debug_steps]:
            menu.add_command(
                label=step,
                command=lambda value=step: selected_option(value),
            )

        if self.selected_debug_step.get() == "Raw tile":
            raw_image = self.data[index]["image"]
        else:
            debug_index = debug_steps.index(self.selected_debug_step.get())
            raw_image = self.data[index]["debug_images"][debug_index][1]
            raw_image = (raw_image / math.sqrt(3)).astype(numpy.uint8)

        image = PIL.Image.fromarray(raw_image)
        resized_image = image.resize(
            (int(self.canvas["width"]), int(self.canvas["height"])), Image.NEAREST
        )
        # Assign to self.tile_image to prevent from being garbage collected
        self.tile_image = ImageTk.PhotoImage(image=resized_image)
        self.canvas.create_image(0, 0, image=self.tile_image, anchor=tkinter.NW)

        self.tile_file_name.config(
            text=f"File: {self.data[index]['file_name']} ({index+1}/{len(self.data)})"
        )
        self.real_tile_content.config(
            text="==Real content==\n" + tile_to_text(self.data[index]["real_content"])
        )
        self.predicted_tile_content.config(
            text="==Predicted content==\n"
            + tile_to_text(self.data[index]["predicted_content"])
        )

    def run_coroutine(self, coroutine):
        async def wrapped_coroutine():
            try:
                await coroutine
            except Exception:
                traceback.print_exc()

        asyncio.run_coroutine_threadsafe(wrapped_coroutine(), self.event_loop)

    def generate_training_data(self):
        self.run_coroutine(self.classifier.generate_training_data())

    def load_training_data(self):
        self.run_coroutine(self.classifier.load_training_data())

    def train_model(self):
        self.run_coroutine(self.classifier.train_model())

    def save_weights(self):
        self.run_coroutine(self.classifier.save_model_weights())

    def next_tile(self):
        self.data_index += 1
        self.show_tile()
        self.set_browse_button_state()

    def previous_tile(self):
        self.data_index -= 1
        self.show_tile()
        self.set_browse_button_state()
