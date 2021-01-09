import asyncio
import queue
import threading
import tkinter

from tile_classifier import ComparisonTileClassifier, ClassifierAppBackend
from drod_bot import DrodBot
from drod_interface import PlayInterface, EditorInterface
from gui_app import GuiApp


if __name__ == "__main__":
    window_queue = queue.Queue()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    asyncio_thread = threading.Thread(target=loop.run_forever)
    asyncio_thread.start()

    editor_interface = EditorInterface()
    classifier = ComparisonTileClassifier()
    classifier.load_tile_data("tile_data")
    classifier_app_backend = ClassifierAppBackend(
        classifier, "tile_data", "training_data", editor_interface, window_queue
    )
    play_interface = PlayInterface(window_queue, classifier)
    bot = DrodBot(play_interface, window_queue)

    window = tkinter.Tk()
    window.title("DRODbot")
    app = GuiApp(
        root=window,
        event_loop=loop,
        queue=window_queue,
        bot=bot,
        play_interface=play_interface,
        classifier_app_backend=classifier_app_backend,
    )
    app.pack()
    try:
        app.mainloop()
    finally:
        loop.call_soon_threadsafe(loop.stop)
        asyncio_thread.join()
