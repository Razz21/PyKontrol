#!/usr/bin/env python

import padKontrol as pk
import rtmidi
from rtmidi.midiutil import open_midioutput, open_midiinput
import asyncio
from sequence import Sequencer
import time
import pkconstants as const
from rtmidi.midiconstants import (
    ALL_SOUND_OFF,
    BANK_SELECT_LSB,
    BANK_SELECT_MSB,
    CHANNEL_VOLUME,
    CONTROL_CHANGE,
    NOTE_ON,
    PROGRAM_CHANGE,
)


# from async_timer import Timer

OUTPUT_MIDI_PORT = 2

INPUT_MIDI_PORT = 1

active_pads = {}

midi_out, _ = open_midioutput(
    OUTPUT_MIDI_PORT,
    api=rtmidi.API_WINDOWS_MM,
    client_name="padkontrol",
    port_name="MIDI Out",
)


def send_sysex(sysex):
    midi_out.send_message(sysex)


async def send_sysex_async(sysex):
    await asyncio.sleep(0)
    x = midi_out.send_message(sysex)
    return x


# GLOBALS
is_sequenced = True
pk_print = None
midi_in = None
midiout = None

seq = Sequencer()

stage = seq.get_stage_or_create(1)


async def change_sequence():
    global is_sequenced
    is_sequenced = not is_sequenced


class PadKontrolPrint(pk.PadKontrolInput):
    current_stage = stage
    main_clock = 120  # BPM

    def lightning(self):
        for pad in range(16):
            if pad in self.current_stage.active_steps:
                send_sysex(pk.light(pad, True))
            else:
                send_sysex(pk.light(pad, False))

    def on_pad_down(self, pad, velocity):

        if pad in self.current_stage.active_steps:
            current = False
            self.current_stage.remove_step(pad)
        else:
            self.current_stage.add_steps(pad)
            current = True
        send_sysex(pk.light(pad, current))

        print("pad #%d down, velocity %d/127" % (pad, velocity))

    # def on_pad_down(self, pad, velocity):
    #     midiout.send_message([0x90, 127, 127])
    #     send_sysex(pk.light(pad, const.LIGHT_STATE_ON))
    #     print("pad #%d down, velocity %d/127" % (pad, velocity))

    def on_pad_up(self, pad):
        # midiout.send_message([0x80, 127, 0])
        # send_sysex(pk.light(pad, const.LIGHT_STATE_OFF))
        print("pad #%d up" % pad)

    def on_button_down(self, button):
        global is_sequenced

        if button == const.BUTTON_FLAM:
            print("flam button down")
        else:
            if button == 34:
                self.current_stage = seq.get_stage_or_create(2)
                self.lightning()
                print("stage up")
            elif button == 32:
                self.current_stage = seq.get_stage_or_create(1)
                self.lightning()
                print("stage down")
            elif button == 24:
                is_sequenced = not is_sequenced
                print(is_sequenced)

            print("button #%d down" % button)

    def on_button_up(self, button):
        if button == const.BUTTON_MESSAGE:
            print("message button up")
        else:
            print("button #%d up" % button)

    def on_knob(self, knob, value):
        print("knob #%d value = %d, %s" % (knob, value, str(self.current_stage)))

    def on_rotary_left(self):
        self.main_clock -= 1
        x = str(self.main_clock).zfill(3)
        val = pk.string_to_sysex(x)
        send_sysex(pk.led(val))
        print("rotary turned left", self.main_clock)

    def on_rotary_right(self):
        self.main_clock += 1
        x = str(self.main_clock).zfill(3)
        val = pk.string_to_sysex(x)
        send_sysex(pk.led(val))
        print("rotary turned right", self.main_clock)

    def on_x_y(self, x, y):
        print("x/y pad (x = %d, y = %d)" % (x, y))


def initializer():
    send_sysex(const.SYSEX_NATIVE_MODE_OFF)
    input("Press enter to enable native mode.")
    send_sysex(const.SYSEX_NATIVE_MODE_ON)
    send_sysex(const.SYSEX_NATIVE_MODE_ENABLE_OUTPUT)
    send_sysex(const.SYSEX_NATIVE_MODE_INIT)
    send_sysex(const.SYSEX_NATIVE_MODE_TEST)
    input("Native mode ON")


initializer()

midi_in, _ = open_midiinput(
    INPUT_MIDI_PORT,
    api=rtmidi.API_WINDOWS_MM,
    client_name="padkontrol",
    port_name="MIDI In",
)

pk_print = PadKontrolPrint()


midiout = rtmidi.MidiOut()
available_ports = midiout.get_ports()

if available_ports:
    midiout.open_port(5)
else:
    midiout.open_virtual_port("My virtual output")

input("Input Port initizlied! Click Enter to enable sequencer mode.")


def midi_in_callback(message, data):
    sysex_buffer = []
    for byte in message[0]:
        sysex_buffer.append(byte)

        if byte == 0xF7:
            pk_print.process_sysex(sysex_buffer)
            del sysex_buffer[:]  # empty list


midi_in.ignore_types(False, False, False)
midi_in.set_callback(midi_in_callback)

channels = range(1, 17)
on = range(144, 160)
off = range(128, 144)

channels_ON = dict(zip(channels, on))
channels_OFF = dict(zip(channels, off))


async def send_midi(note, channel, velocity):
    # signal_on = channels_ON.get(channel)
    # signal_off = channels_OFF.get(channel)
    midiout.send_message([NOTE_ON | channel, note, velocity])
    # midiout.send_message([signal_on, 127, 127])
    # await asyncio.sleep(0.01)
    # midiout.send_message([NOTE_ON | channel, note, 0])
    # midiout.send_message([signal_off, 127, 0])


async def send_to_channel(channel, pad, note):
    c = seq.get_stage_or_create(channel)
    if pad in c.active_steps:
        noteon = asyncio.create_task(send_midi(note, channel, velocity=100))
        hold = asyncio.create_task(asyncio.sleep(0.01))
        noteoff = asyncio.create_task(send_midi(note, channel, velocity=0))
        result = await asyncio.gather([noteon, hold, noteoff])
    await asyncio.sleep(0)


async def sequence(steps=16):
    while True:
        # stime = time.perf_counter()
        for x in range(steps):
            flash = asyncio.create_task(send_sysex_async(pk.light_flash(x, 0.05)))

            time_task = asyncio.create_task(asyncio.sleep(60 / pk_print.main_clock / 4))

            send_task1 = asyncio.create_task(send_to_channel(1, x, 36))  # port 1
            send_task2 = asyncio.create_task(send_to_channel(2, x, 38))  # port 2
            stats = [flash, time_task, send_task1, send_task2]

            resuls = await asyncio.gather(*stats)
            # await send_task1
            # await send_task2
            # await flash
            # await time_task


async def mmm():
    midi_in.set_callback(midi_in_callback)
    await asyncio.sleep(0)


async def monitor(evt):
    while True:
        if is_sequenced:
            print("reset!")

            evt.set()
        await asyncio.sleep(1)


async def get_midi_in(s):
    midi_in.set_callback(midi_in_callback)
    while True:
        # await mmm()
        if is_sequenced:
            # print("restarting coroutine1")
            s.start()
        else:
            # print("stopping coroutine1")
            s.stop()
        await asyncio.sleep(1)


from utils import Stoppable


async def coroutine2(s):
    i = 0
    while True:
        i += 1
        if i == 3:
            print("stopping coroutine1")
            s.stop()
        elif i == 6:
            input("restarting coroutine1, press ENTER")
            s.start()
        print("coroutine2: " + str(i))
        await asyncio.sleep(2)


# async def main():
#     loop = asyncio.get_event_loop()
#     reset_evt = asyncio.Event()
#     loop.create_task(monitor(reset_evt))
#     while True:
#         workers = []
#         workers.append(loop.create_task(sequence()))
#         workers.append(loop.create_task(get_midi_in()))
#         await reset_evt.wait()
#         reset_evt.clear()
#         for t in workers:
#             t.cancel()

# async def main():
#     count = loop.create_task(sequence())
#     buffer = loop.create_task(get_midi_in())
#     await asyncio.wait([count, buffer])
#     return count, buffer


async def main():
    loop = asyncio.get_event_loop()
    s = Stoppable(sequence())
    fut1 = asyncio.ensure_future(s)
    # task2 = loop.create_task(coroutine2(s))
    task2 = loop.create_task(get_midi_in(s))
    done, pending = await asyncio.wait([fut1, task2], return_when=asyncio.ALL_COMPLETED)


loop = asyncio.get_event_loop()

try:
    loop.run_until_complete(main())

except (asyncio.CancelledError, KeyboardInterrupt) as e:
    print("")

finally:
    loop.run_until_complete(loop.shutdown_asyncgens())
    loop.close()

    # input("Press enter to exit")

    send_sysex(const.SYSEX_NATIVE_MODE_OFF)

    midi_in.close_port()
    midi_out.close_port()
    del midiout

