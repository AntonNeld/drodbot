import asyncio
import queue
import threading
import tkinter

import room_simulator
from tile_classifier import TileClassifier
from room_interpreter import RoomInterpreter
from drod_bot import DrodBot
from drod_interface import PlayInterface, EditorInterface
from apps import MainApp
from apps.backends import (
    ClassificationAppBackend,
    InterpretScreenAppBackend,
    PlayingAppBackend,
    RoomSolverAppBackend,
)


def main():
    # It should be fine to initialize the room simulator in this thread,
    # we only have one right now so no race conditions.
    room_simulator.initialize()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    asyncio_thread = threading.Thread(target=loop.run_forever)
    asyncio_thread.start()

    editor_interface = EditorInterface()
    classifier = TileClassifier()
    classifier.load_tile_data("tile_data")
    play_interface = PlayInterface(classifier)
    interpreter = RoomInterpreter(classifier, play_interface)
    bot = DrodBot("bot_state.json", play_interface)

    window_queue = queue.Queue()
    classification_app_backend = ClassificationAppBackend(
        classifier, "tile_data", "sample_tiles", editor_interface, window_queue
    )
    interpret_screen_app_backend = InterpretScreenAppBackend(
        play_interface, interpreter, window_queue
    )
    playing_app_backend = PlayingAppBackend(bot, window_queue)
    room_solver_app_backend = RoomSolverAppBackend(play_interface, bot, window_queue)

    window = tkinter.Tk()
    window.title("DRODbot")
    app = MainApp(
        root=window,
        event_loop=loop,
        queue=window_queue,
        playing_app_backend=playing_app_backend,
        interpret_screen_app_backend=interpret_screen_app_backend,
        room_solver_app_backend=room_solver_app_backend,
        classification_app_backend=classification_app_backend,
    )
    app.pack()
    try:
        app.mainloop()
    finally:
        loop.call_soon_threadsafe(loop.stop)
        asyncio_thread.join()


if __name__ == "__main__":
    main()
