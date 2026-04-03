"""
Creating a mental model for processing async data.

"""
import asyncio
from collections.abc import AsyncIterator, Iterator
from collections import deque
from random import random, randint


# PRODUCER: PUSHES VALUES
async def async_cyclic_iterator(pattern: list[int]) -> AsyncIterator[int|None]:
    """Yields repeatedly over *pattern* simulating a incoming data
    with a random timing offset,
    and package loss."""
    length = len(pattern)

    i = 0
    while True:
        i += 1

        # JITTER:
        await asyncio.sleep(random() / 10)

        if randint(0, 5) >= 1:
            yield pattern[i % length]
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
async def append_to_buffer(buff: deque, stream: AsyncIterator) -> None:
    """
    Appends one data point from *stream* to *buff*. 
    """
    try:
        data = await anext(stream)
        if data is not None:
            buff.append(data)
            # print(data)
    except StopAsyncIteration:
        pass


async def fill_buffer(ring_buff: deque,
                      stream: AsyncIterator[int | None]) -> None:
    """
    Filling the buffer *ring_buff* *n* times with data from *stream*.
    """
    while True:
        await append_to_buffer(ring_buff, stream)


async def visualize_processed_data(
        stream: Iterator[int | None]) -> None:
    """
    Prints *data_point* to console line by line.
    """
    for data_point in stream:
        print(data_point)
        await asyncio.sleep(0.1)

async def view_loop(ring_buff: deque) -> None:
    """Periodically checks the buffer,
    and pushes data through the pipeline."""
    while True:
        # PULL FROM BUFFER
        raw_stream = buffer_handler(ring_buff)

        if raw_stream:
            # GENERATOR EXPRESSION (LAZY EVALUATION):
            mapped_stream = (manipulate_data_point(p)
                             for p in raw_stream if p is not None)
            await visualize_processed_data(mapped_stream)
        await asyncio.sleep(0.1)


async def main() -> None:
    """
    idk
    """
    # SETUP:
    pattern: list[int] = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9,
                          9, 8, 7, 6, 5, 4, 3, 2, 1, 0]
    # FIFO: Adapt to Latency
    ring_buffer: deque = deque(maxlen=10)

    incoming_stream = async_cyclic_iterator(pattern)

    print("Live Stream...")


    await asyncio.gather(
        fill_buffer(ring_buffer, incoming_stream),
        view_loop(ring_buffer)
    )


if __name__ == "__main__":
    asyncio.run(main())
