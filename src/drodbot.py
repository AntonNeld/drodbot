import asyncio
import queue
import threading
import tkinter

from tile_classifier import TileClassifier
from drod_bot import DrodBot
from drod_interface import PlayInterface, EditorInterface
from apps import MainApp
from apps.backends import (
    ClassificationAppBackend,
    InterpretScreenAppBackend,
    PlayingAppBackend,
)


def main():
    window_queue = queue.Queue()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    asyncio_thread = threading.Thread(target=loop.run_forever)
    asyncio_thread.start()

    editor_interface = EditorInterface()
    classifier = TileClassifier()
    classifier.load_tile_data("tile_data")
    play_interface = PlayInterface(window_queue, classifier)
    bot = DrodBot(play_interface)

    classification_app_backend = ClassificationAppBackend(
        classifier, "tile_data", "training_data", editor_interface, window_queue
    )
    interpret_screen_app_backend = InterpretScreenAppBackend(
        window_queue, play_interface
    )
    playing_app_backend = PlayingAppBackend(bot, window_queue)

    window = tkinter.Tk()
    window.title("DRODbot")
    app = MainApp(
        root=window,
        event_loop=loop,
        queue=window_queue,
        playing_app_backend=playing_app_backend,
        interpret_screen_app_backend=interpret_screen_app_backend,
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
