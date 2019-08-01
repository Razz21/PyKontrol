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


async def timeout_callback():
    await asyncio.sleep(0.01)
    print("echo!")


async def main():
    stime = time.perf_counter()
    print("\nfirst example:")
    timer = Timer(2, timeout_callback)  # set timer for two seconds
    print("timer1", time.perf_counter() - stime)

    await asyncio.sleep(2.5)  # wait to see timer works
    print("timer2", time.perf_counter() - stime)
    print("\nsecond example:")

    timer = Timer(2, timeout_callback)  # set timer for two seconds
    print("timer3", time.perf_counter() - stime)
    await asyncio.sleep(1)

    print("timer4", time.perf_counter() - stime)
    timer.cancel()  # cancel it
    await asyncio.sleep(1.5)  # and wait to see it won't call callback


loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
try:
    loop.run_until_complete(main())
finally:
    loop.run_until_complete(loop.shutdown_asyncgens())
    loop.close()
