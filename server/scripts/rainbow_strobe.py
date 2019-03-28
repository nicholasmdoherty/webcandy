import time

from . import opc
from . import opcutil


def run(*args, **kwargs):
    client = opc.Client('localhost:7890')

    num_leds = 512
    colors = [(255, 0, 0),  # red
            (255, 127, 0),  # orange
            (255, 255, 0),  # yellow
            (0, 255, 0),  # green
            (0, 0, 255),  # blue
            (139, 0, 255)]  # violet
    pixels = opcutil.spread(colors, num_leds, 10)
    black = [(0, 0, 0)] * num_leds

    while True:
        client.put_pixels(pixels)
        time.sleep(0.05)
        pixels = opcutil.rotate_right(pixels, 2)
        client.put_pixels(black)
        time.sleep(0.05)


if __name__ == '__main__':
    run()
