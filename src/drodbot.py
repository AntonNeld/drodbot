import asyncio
import threading
import tkinter

import room_simulator
from tile_classifier import TileClassifier
from room_interpreter import RoomInterpreter
from drod_bot import DrodBot
from drod_interface import PlayInterface, EditorInterface
from apps import (
    MainApp,
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
    play_interface = PlayInterface()
    play_interface.load_character_images("tile_data")
    classifier = TileClassifier()
    classifier.load_tile_data("tile_data")
    interpreter = RoomInterpreter(classifier, play_interface)
    bot = DrodBot("bot_state.json", "test_rooms", play_interface, interpreter)

    classification_app_backend = ClassificationAppBackend(
        classifier, "tile_data", "sample_tiles", editor_interface
    )
    interpret_screen_app_backend = InterpretScreenAppBackend(
        play_interface, interpreter
    )
    playing_app_backend = PlayingAppBackend(bot, loop)
    room_solver_app_backend = RoomSolverAppBackend(play_interface, interpreter, bot)

    window = tkinter.Tk()
    window.title("DRODbot")
    app = MainApp(
        root=window,
        event_loop=loop,
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
