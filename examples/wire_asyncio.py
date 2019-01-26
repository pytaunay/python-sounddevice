#!/usr/bin/env python3
import asyncio
import queue

import numpy as np
import sounddevice as sd


async def stream_generator(blocksize, pre_fill_blocks=10, **kwargs):
    channels = 1
    assert blocksize != 0

    q_in = asyncio.Queue()
    q_out = queue.Queue()
    loop = asyncio.get_event_loop()

    def callback(indata, outdata, frame_count, time_info, status):
        loop.call_soon_threadsafe(q_in.put_nowait, (indata.copy(), status))
        outdata[:] = q_out.get_nowait()

    # pre-fill output queue
    for _ in range(pre_fill_blocks):
        q_out.put(np.zeros((blocksize, channels), dtype='float32'))

    stream = sd.Stream(blocksize=blocksize, callback=callback, dtype='float32',
                       channels=channels, **kwargs)
    with stream:
        while True:
            indata, status = await q_in.get()
            outdata = np.empty((blocksize, channels), dtype='float32')
            yield indata, outdata, status
            q_out.put_nowait(outdata)


async def wire_coro(**kwargs):
    async for indata, outdata, status in stream_generator(**kwargs):
        if status:
            print(status)
        outdata[:] = indata


async def main(**kwargs):
    print('starting wire ...')
    # Use asyncio.ensure_future() if you have Python < 3.7
    audio_task = asyncio.create_task(wire_coro(**kwargs))
    # You can do whatever you want here, this is just placeholder code:
    iterations = 10
    for i in range(iterations, 0, -1):
        print(i)
        await asyncio.sleep(1)
    audio_task.cancel()
    try:
        await audio_task
    except asyncio.CancelledError:
        print('wire was cancelled')


if __name__ == "__main__":
    asyncio.run(main(blocksize=1024))
