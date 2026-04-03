"""
Creating a mental model for processing async data.

"""
from collections.abc import Iterator, Callable
from collections import deque
from time import sleep
from random import random, randint


# PRODUCER: PUSHES VALUES
def async_cyclic_iterator(pattern: list[int]) -> Iterator[int|None]:
    """Yields repeatedly over *pattern* simulating a incoming data
    with a random timing offset,
    and package loss."""
    i = 0
    while True:
        i += 1

        # JITTER:
        sleep(random())

        if randint(0, 5) >= 1:
            yield pattern[i % 10]
        else:
            # PACKAGE/DATA LOSS:
            yield None


# CONSUMER: PROCESSING BATCH OF DATA
def batch_process_data(buff: deque) -> list[int] | None:
    """
    Immediately returns *None* if *buff* is empty.
    
    If buff is not empty:
    
    Copies *buff* (a batch of data) to *b*,
    flushes *buff*,
    and returns a list of processed data.
    """
    if len(buff) == 0:
        return None

    b = buff.copy()
    buff.clear()

    return [b[_1] + 2 for _1 in range(len(b))]

# EGRESS / CONSUMER: PROCESSING DATA POINT (LAZY EVALUATION)
def buffer_handler(buff: deque) -> Iterator[int]:
    """
    Immediately returns *None* if *buff* is empty.
    
    If buff is not empty:
    
    Copies data into a working buffer,
    flushes buffer,
    and returns data stream in order.
    """
    if len(buff) == 0:
        return

    working_buffer = buff.copy()
    buff.clear()

    yield from working_buffer


def manipulate_data_point(p: int | None) -> int | None:
    """
    Returns processed data point *p* from a given stream.
    """
    if p is not None:
        return p + 2
    return None

# INGRESS / CALLBACK:
def append_to_buffer(buff: deque, stream: Callable[[], int | None]) -> None:
    """
    Appends one data point from *stream* to *buff*. 
    """
    data = stream()
    if data is not None:
        buff.append(data)

def fill_buffer(n: int, ring_buff: deque,
                stream: Callable[[], int | None]) -> None:
    """
    Filling the buffer *ring_buff* *n* times with data from *stream*.
    """
    for _ in range(n):
        append_to_buffer(ring_buff, stream)

def visualize_processed_data(stream: Iterator[int | None]) -> None:
    """
    Prints *data_point* to console line by line.
    """
    for data_point in stream:
        print(data_point)


if __name__ == "__main__":
    # SETUP:
    PATTERN: list[int] = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9,
                          9, 8, 7, 6, 5, 4, 3, 2, 1, 0]
    # FIFO: Adapt to Latency
    BUFFER_LENGTH = 10
    RING_BUFFER: deque = deque(maxlen=BUFFER_LENGTH)

    incoming = async_cyclic_iterator(PATTERN)
    stream_in = lambda: next(incoming)  # PULLS DATA

    # SERIAL LOOP
    count = 0

    while (count < 10):
        print(f"Iteration #{count}\n")
        print("Incoming Data:")
        print("______________________________")

        fill_buffer(BUFFER_LENGTH, RING_BUFFER, stream_in)

        print("______________________________")
        print("\n\n")


        print("Processed Data:")
        print("______________________________")

        raw_stream = buffer_handler(RING_BUFFER)

        # GENERATOR EXPRESSION (LAZY EVALUATION):
        mapped_stream = (manipulate_data_point(p) for p in raw_stream if p is not None)

        visualize_processed_data(mapped_stream)

        print("______________________________")
        print("\n\n")

        count += 1
