#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import argparse
import io
from collections import deque
from select import select
from time import time
import re
import matplotlib.pyplot as plt


def read_timeout(stream, timeout):
    """Read a character from stream.
    Return '' on timeout or EOF.
    """
    rlist, _, _ = select([stream], [], [], timeout)
    if rlist:
        return stream.read(1)
    else:
        return ""


def blocking_readline(stream, timeout):
    """Read a line from stream.
    The line may not end with '\\n' on timeout or EOF.
    """
    line = []
    line.append(read_timeout(stream, timeout))
    while line[-1] != "\n":
        if len(line[-1]) == 0:
            return "".join(line)
        line.append(read_timeout(stream, timeout))
    return "".join(line)


class AnalogPlot:
    def __init__(self, stream, num_series, max_len):
            # open serial port
            self.stream = stream
            self.num_series = num_series
            self.max_len = max_len
            self.xdata = range(max_len)
            self.data = []
            for _ in range(num_series):
                self.data.append(deque([0.0] * max_len))

    def add_to_series(self, serie_num, val):
        buf = self.data[serie_num]
        if len(buf) >= self.max_len:
            buf.popleft()
        buf.append(val)

    def add(self, data):
        assert len(data) == self.num_series
        for i, value in enumerate(data):
            self.add_to_series(i, value)

    def read_data(self, duration):
        start_time = time()

        # Read data from stdin, until timeout or EOF
        while time() - start_time < duration:
            line = blocking_readline(self.stream, duration)

            # Detect EOF
            if not line:
                break

            print(line, end="")

            # Check and store data
            data = [
                float(val) for val in
                re.findall("[-+]?[0-9]*\.?[0-9]+", line, re.DOTALL)
            ]
            if (len(data) == self.num_series):
                self.add(data)

    def update_plot(self, ax, lines):
        ymin = float("+inf")
        ymax = float("-inf")
        for i, l in enumerate(lines):
            l.set_data(self.xdata, self.data[i])
            if l.get_visible():
                ymin = min(ymin, min(self.data[i]))
                ymax = max(ymax, max(self.data[i]))
        ax.set_ylim([ymin, ymax])


def get_args():
    parser = argparse.ArgumentParser(description="Plot data from stdin")
    parser.add_argument(
        "-n", "--number",
        type = int,
        help = "Set number of columns",
        required = True
    )
    parser.add_argument(
        "-l", "--labels",
        nargs = "+",
        help = "Set column labels"
    )
    parser.add_argument(
        "--xlen",
        type = int,
        help = "Set length of x history (default is 1000)",
        default = 1000
    )
    return parser.parse_args()


def handle_close(evt):
    print("(*) Exiting...", file=sys.stderr)
    sys.exit(0)


def main():
    # parse args
    args = get_args()

    # plot parameters
    input_stream = io.TextIOWrapper(sys.stdin.buffer, errors="ignore")
    analog_plot = AnalogPlot(input_stream, args.number, args.xlen)

    # Set plot to animated
    plt.ion()

    # Set up plot
    fig = plt.figure()
    fig.canvas.mpl_connect("close_event", handle_close)
    ax = plt.axes(
        title = "",
        xlim = (0, args.xlen),
        ylim = (-1000, 1000),
        xlabel = "Time",
        ylabel = "Value"
    )

    # Prepare data lines
    lines = []
    for i in range(args.number):
        l, = ax.plot([], [], label=args.labels[i] if args.labels else i)
        lines.append(l)

    # Prepare legend
    leg = ax.legend(loc="upper left", fancybox=True, framealpha=0.7)

    lined = dict()
    for leg_line, orig_line in zip(leg.get_lines(), lines):
        leg_line.set_picker(7)  # tolerance in pts
        lined[leg_line] = orig_line

    def onpick(event):
        # Find the orig line corresponding to the legend proxy line,
        # and toggle the visibility
        leg_line = event.artist
        orig_line = lined[leg_line]
        vis = not orig_line.get_visible()
        orig_line.set_visible(vis)
        # Change the alpha on the line in the legend
        if vis:
            print("(*) Show line...", file=sys.stderr)
            leg_line.set_alpha(1.0)
        else:
            print("(*) Hide line...", file=sys.stderr)
            leg_line.set_alpha(0.2)
        fig.canvas.draw()

    fig.canvas.mpl_connect("pick_event", onpick)

    plt.tight_layout()

    # Draw and update plot
    print("(*) Drawing...", file=sys.stderr)
    while True:
        analog_plot.read_data(1/50)
        analog_plot.update_plot(ax, lines)
        plt.pause(0.0001)


if __name__ == "__main__":
    main()
