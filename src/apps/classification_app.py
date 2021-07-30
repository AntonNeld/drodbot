import asyncio

import numpy
import PIL
from PIL import ImageTk, Image
import tkinter
import traceback

from .util import apparent_tile_to_text, ScrollableFrame

_CANVAS_WIDTH = 88
_CANVAS_HEIGHT = 88


class ClassificationApp(tkinter.Frame):
    """This app is used to manage the tile classifier.

    It generates tile data to use in classification, and sample data
    to test the classifier. You can browse the sample data and see
    the classification steps.

    Parameters
    ----------
    root
        The parent of the tkinter Frame.
    event_loop
        The asyncio event loop for the backend thread.
    backend
        The backend that generates the data and contains the classifier.
    """

    def __init__(self, root, event_loop, backend):
        super().__init__(root)
        self._event_loop = event_loop
        self._backend = backend
        self._raw_data = []
        self._data = []
        self._data_index = None
        self._only_wrong = tkinter.BooleanVar(self)
        self._only_wrong.set(False)
        self._radio_buttons = []
        self._selected_debug_step = tkinter.StringVar(self)
        self._selected_debug_step.set("Raw tile")

        # Create widgets
        self._tile_area = tkinter.Frame(self)
        self._tile_area.pack(side=tkinter.LEFT)
        self._canvas = tkinter.Canvas(
            self._tile_area, width=_CANVAS_WIDTH, height=_CANVAS_HEIGHT, bg="white"
        )
        self._canvas.pack(side=tkinter.TOP)
        self._browse_buttons = tkinter.Frame(self._tile_area)
        self._browse_buttons.pack(side=tkinter.TOP)
        self._next_tile_button = tkinter.Button(
            self._browse_buttons, text=">", state="disable", command=self._next_tile
        )
        self._next_tile_button.pack(side=tkinter.RIGHT)
        self._previous_tile_button = tkinter.Button(
            self._browse_buttons, text="<", state="disable", command=self._previous_tile
        )
        self._previous_tile_button.pack(side=tkinter.RIGHT)
        self._only_wrong_checkbox = tkinter.Checkbutton(
            self._tile_area,
            text="Only wrongly predicted",
            variable=self._only_wrong,
            command=self._filter_data,
        )
        self._only_wrong_checkbox.pack(side=tkinter.TOP)
        self._debug_step_frame = ScrollableFrame(self._tile_area)
        self._debug_step_frame.pack(side=tkinter.TOP)
        self._set_debug_steps()

        self._details_area = tkinter.Frame(self)
        self._details_area.pack(side=tkinter.LEFT)
        self._tile_file_name = tkinter.Label(self._details_area, text="")
        self._tile_file_name.pack(side=tkinter.TOP)
        self._tile_content_area = tkinter.Frame(self._details_area)
        self._tile_content_area.pack(side=tkinter.TOP)
        self._real_tile_content = tkinter.Label(self._tile_content_area, text="")
        self._real_tile_content.pack(side=tkinter.LEFT)
        self._predicted_tile_content = tkinter.Label(self._tile_content_area, text="")
        self._predicted_tile_content.pack(side=tkinter.LEFT)

        self._control_panel = tkinter.Frame(self)
        self._control_panel.pack(side=tkinter.LEFT)
        self._tile_data_button = tkinter.Button(
            self._control_panel,
            text="Generate all tile data",
            command=self._generate_tile_data,
        )
        self._tile_data_button.pack(side=tkinter.TOP)
        self._only_tile_button = tkinter.Button(
            self._control_panel,
            text="Generate only individual elements",
            command=self._generate_individual_elements,
        )
        self._only_tile_button.pack(side=tkinter.TOP)
        self._only_textures_button = tkinter.Button(
            self._control_panel,
            text="Generate only textures",
            command=self._generate_textures,
        )
        self._only_textures_button.pack(side=tkinter.TOP)
        self._only_shadows_button = tkinter.Button(
            self._control_panel,
            text="Generate only shadows",
            command=self._generate_shadows,
        )
        self._only_shadows_button.pack(side=tkinter.TOP)
        self._only_characters_button = tkinter.Button(
            self._control_panel,
            text="Generate only character images",
            command=self._generate_characters,
        )
        self._only_characters_button.pack(side=tkinter.TOP)
        self._generate_sample_data_button = tkinter.Button(
            self._control_panel,
            text="Generate sample data",
            command=self._generate_sample_data,
        )
        self._generate_sample_data_button.pack(side=tkinter.TOP)
        self._load_sample_data_button = tkinter.Button(
            self._control_panel,
            text="Load sample data",
            command=self._load_sample_data,
        )
        self._load_sample_data_button.pack(side=tkinter.TOP)

    def set_data(self, data):
        """Set the sample data to show in the app.

        Parameters
        ----------
        data
            A list of dicts, each containing the data for a tile.
        """
        self._raw_data = data
        self._filter_data()

    def _filter_data(self):
        old_filenames = [tile["file_name"] for tile in self._data]
        if self._only_wrong.get():
            self._data = [
                t for t in self._raw_data if t["real_content"] != t["predicted_content"]
            ]
        else:
            self._data = self._raw_data
        if len(self._data) > 0:
            # Keep the index if it's the same files, since this means we're just
            # updating the data
            if [tile["file_name"] for tile in self._data] != old_filenames:
                self._data_index = 0
            self._set_debug_steps()
            self._show_tile()
        else:
            self._data_index = None
            self._canvas.delete("all")
            self._tile_file_name.config(text="")
            self._real_tile_content.config(text="")
            self._predicted_tile_content.config(text="")
            self._set_debug_steps()
        self._set_browse_button_state()

    def _set_browse_button_state(self):
        if self._data_index is None:
            self._next_tile_button.config(state="disable")
            self._previous_tile_button.config(state="disable")
        else:
            self._next_tile_button.config(
                state="disable" if self._data_index == len(self._data) - 1 else "normal"
            )
            self._previous_tile_button.config(
                state="disable" if self._data_index == 0 else "normal"
            )

    def _show_tile(self, *args):
        # Add *args because the radio button gives an unused argument to this function
        index = self._data_index

        if self._selected_debug_step.get() == "Raw tile":
            raw_image = self._data[index]["image"]
        else:
            debug_index = [
                name for name, image in self._data[index]["debug_images"]
            ].index(self._selected_debug_step.get())
            raw_image = self._data[index]["debug_images"][debug_index][1]
            raw_image = raw_image.astype(numpy.uint8)

        image = PIL.Image.fromarray(raw_image)
        resized_image = image.resize(
            (int(self._canvas["width"]), int(self._canvas["height"])), Image.NEAREST
        )
        # Assign to self._tile_image to prevent from being garbage collected
        self._tile_image = ImageTk.PhotoImage(image=resized_image)
        self._canvas.create_image(0, 0, image=self._tile_image, anchor=tkinter.NW)

        self._tile_file_name.config(
            text=f"File: {self._data[index]['file_name']} ({index+1}/{len(self._data)})"
        )
        self._real_tile_content.config(
            text="==Real content==\n"
            + apparent_tile_to_text(self._data[index]["real_content"])
        )
        self._predicted_tile_content.config(
            text="==Predicted content==\n"
            + apparent_tile_to_text(self._data[index]["predicted_content"])
        )

    def _set_debug_steps(self):
        # Add *args because the dropdown gives an unused argument to this function
        index = self._data_index
        # Get the possible debug steps
        if index is not None:
            debug_steps = [name for name, image in self._data[index]["debug_images"]]
        else:
            debug_steps = []
        if self._selected_debug_step.get() not in debug_steps:
            self._selected_debug_step.set("Raw tile")

        for radio_button in self._radio_buttons:
            radio_button.pack_forget()
        self._radio_buttons = [
            tkinter.Radiobutton(
                self._debug_step_frame.scrollable_frame,
                text=step,
                value=step,
                variable=self._selected_debug_step,
                command=self._show_tile,
            )
            for step in ["Raw tile", *debug_steps]
        ]
        for radio_button in self._radio_buttons:
            radio_button.pack(side=tkinter.TOP)

    def _run_coroutine(self, coroutine):
        async def wrapped_coroutine():
            try:
                await coroutine
            except Exception:
                traceback.print_exc()

        asyncio.run_coroutine_threadsafe(wrapped_coroutine(), self._event_loop)

    def _generate_sample_data(self):
        self._run_coroutine(self._backend.generate_sample_data())

    def _load_sample_data(self):
        self._run_coroutine(self._backend.load_sample_data())

    def _generate_tile_data(self):
        self._run_coroutine(self._backend.generate_tile_data())

    def _generate_individual_elements(self):
        self._run_coroutine(self._backend.generate_individual_element_images())

    def _generate_textures(self):
        self._run_coroutine(self._backend.generate_textures())

    def _generate_shadows(self):
        self._run_coroutine(self._backend.generate_shadows())

    def _generate_characters(self):
        self._run_coroutine(self._backend.generate_characters())

    def _next_tile(self):
        self._data_index += 1
        self._set_debug_steps()
        self._show_tile()
        self._set_browse_button_state()

    def _previous_tile(self):
        self._data_index -= 1
        self._set_debug_steps()
        self._show_tile()
        self._set_browse_button_state()
