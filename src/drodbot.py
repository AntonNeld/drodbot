import asyncio
import queue
import threading
import tkinter

from tile_classifier import TileClassifier
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
    classifier = TileClassifier(
        "training_data", "model_weights", editor_interface, window_queue
    )
    play_interface = PlayInterface(window_queue, classifier)
    bot = DrodBot(play_interface, window_queue)

    window = tkinter.Tk()
    app = GuiApp(
        root=window,
        event_loop=loop,
        queue=window_queue,
        bot=bot,
        play_interface=play_interface,
        classifier=classifier,
    )
    app.pack()
    try:
        app.mainloop()
    finally:
        loop.call_soon_threadsafe(loop.stop)
        asyncio_thread.join()
