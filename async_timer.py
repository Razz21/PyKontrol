import asyncio
import time


class Timer:
    def __init__(self, timeout, callback):
        self._timeout = timeout
        self._callback = callback
        self._task = asyncio.ensure_future(self._job())

    async def _job(self):
        await asyncio.sleep(self._timeout)
        await self._callback()

    def cancel(self):
        self._task.cancel()


import rtmidi

midiout = rtmidi.MidiOut()
available_ports = midiout.get_ports()

if available_ports:
    midiout.open_port(5)
else:
    midiout.open_virtual_port("My virtual output")


async def send_midi():
    midiout.send_message([0x90, 60, 112])
    await asyncio.sleep(0.4)
    midiout.send_message([0x80, 60, 0])


async def timeout_callback():
    stime = time.perf_counter()
    for x in range(16):
        task1 = asyncio.create_task(send_midi())
        task2 = asyncio.create_task(asyncio.sleep(0.5))
        await task1
        await task2
        print(f"beat {x} ", time.perf_counter() - stime)

    # time.sleep(0.5)


async def main():
    stime = time.perf_counter()
    timer = None

    # async def iteration(x):
    timer = Timer(0.5, timeout_callback)  # set timer for two seconds
        # print(f"beat {x}", time.perf_counter() - stime)

    # coros = [iteration(x) for x in range(16)]
    # await asyncio.gather(*coros)
    # # print("timer2", ti me.perf_counter() - stime)

    await asyncio.sleep(4)  # and wait to see it won't call callback
    print("timer3", time.perf_counter() - stime)
    timer.cancel()  # cancel it
    # await asyncio.sleep(0.5)  # and wait to see it won't call callback


loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
try:
    loop.run_until_complete(main())
finally:
    loop.run_until_complete(loop.shutdown_asyncgens())
    loop.close()
