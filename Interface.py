import mido
import time
import padKontrol as pk
import pkconstants as const
import logging
import pkconstants as const
from collections import deque

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s,%(msecs)d %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)


keys_combination = {}


class PadKontrolPrint(pk.PadKontrolInput):
    def __init__(self, queue=None):
        super().__init__()
        self.__observers = None
        self.message = None
        self.queue = queue
        if queue is None:
            self.queue = deque()

    def on_pad_down(self, pad, velocity):
        # print("pad #%d down, velocity %d/127" % (pad, velocity))
        # self.send_sysex(pk.light(pad, const.LIGHT_STATE_ON))
        # sysex = pk.light(pad, const.LIGHT_STATE_ON)
        data = ("pad", "down", pad, velocity)
        self.sendNewMessage(data)

    def on_pad_up(self, pad):
        # print("pad #%d up" % pad)
        # self.send_sysex(pk.light(pad, const.LIGHT_STATE_OFF))
        # msg = pk.light(pad, const.LIGHT_STATE_OFF)
        data = ("pad", "up", pad)
        self.sendNewMessage(data)
        # return sysex

    def on_button_down(self, button):
        # if button == const.BUTTON_FLAM:
        #     print("flam button down")
        # else:
        #     print("button #%d down" % button)
        data = ("button", "down", button)
        self.sendNewMessage(data)

    def on_button_up(self, button):
        # if button == const.BUTTON_MESSAGE:
        #     print("message button up")
        # else:
        #     print("button #%d up" % button)
        if button != 48:  # x/y pad
            data = ("button", "up", button)
            self.sendNewMessage(data)

    def on_knob(self, knob, value):
        # print("knob #%d value = %d" % (knob, value))
        data = ("knob", "", knob, value)
        self.sendNewMessage(data)

    def on_rotary_left(self):
        # print("rotary turned left")
        data = ("rotary", "left")
        self.sendNewMessage(data)

    def on_rotary_right(self):
        # print("rotary turned right")
        data = ("rotary", "right")
        self.sendNewMessage(data)

    def on_x_y(self, x, y):
        # print("x/y pad (x = %d, y = %d)" % (x, y))
        data = ("x/y", "", x, y)
        self.sendNewMessage(data)

    # -----------------------
    def register(self, observerObj):
        self.__observers = observerObj

    def unregister(self, observerObj):
        # not should be empty
        self.__observers = observerObj

    def notifyAll(self):
        # for obs in self.__observers:
        self.__observers.notify(self.message)

    def sendNewMessage(self, message):
        # self.message = message
        # self.notifyAll()
        self.__observers.notify(message)


class Mode1:
    def notify(self, msg):
        print(msg)


class Kontrol:
    def __init__(self):
        self.midi_out = None
        self.midi_in = None
        self.midi_data = None
        self.__connected = False
        self.__native = False
        self.__midi_input_port = "padKONTROL 1 PORT A 1"
        self.__midi_output_port = "padKONTROL 1 CTRL 2"
        self.__midi_data_port = "KorgLoopMidi 5"
        self.mode = Mode1()
        self.padkontrol = PadKontrolPrint()

    def _midi_in_callback(self, message):
        sysex_buffer = []
        for byte in message.bytes():
            sysex_buffer.append(byte)

            if byte == 0xF7:
                self.padkontrol.process_sysex(sysex_buffer)
                del sysex_buffer[:]

    def _open_ports(self):
        if self.__midi_output_port:
            try:
                self.midi_out = mido.open_output(self.__midi_output_port)
                # self.midi_in = mido.open_input(self.__midi_input_port)
                self.__connected = True
                logging.info("connected")
            except:
                port_list = Kontrol.get_ports()
                return port_list
        else:
            port_list = Kontrol.get_ports()
            return port_list

    def _native_on(self):
        if self.__connected:
            self.send_sysex(const.SYSEX_NATIVE_MODE_OFF)
            time.sleep(0.5)  # need some time to initialize native mode
            # input('press enter')
            self.send_sysex(const.SYSEX_NATIVE_MODE_ON)
            self.send_sysex(const.SYSEX_NATIVE_MODE_ENABLE_OUTPUT)
            self.send_sysex(const.SYSEX_NATIVE_MODE_INIT)
            self.send_sysex(const.SYSEX_NATIVE_MODE_TEST)
            logging.info("Native Mode ON")

        else:
            return "midi port not connected, call open_port(`port name`) to create connection"

    def open_input(self):
        self.midi_in = mido.open_input(
            self.__midi_input_port, callback=self._midi_in_callback
        )
        self.midi_data = mido.open_output(self.__midi_data_port)
        logging.info(f"Input port open")

    def _close_ports(self):
        if self.__native:
            return "Native Mode is running, can not close this port"
        else:
            if self.__connected:
                self.midi_out.close()
                if self.midi_in:
                    self.midi_in.close()
                self.__connected = False
                logging.info(f"MIDI port closed.")
            else:
                return "midi port not connected, call open_port(`port name`) to create connection"

    def _native_off(self):
        if self.__native:
            self.send_sysex(const.SYSEX_NATIVE_MODE_OFF)
            self.__native = False
        logging.info(f"Native Mode OFF")

    def send_sysex(self, sysex):
        if self.__connected:
            msg = mido.parse(sysex)
            print(msg)
            self.midi_out.send(msg)

    def notify(self, msg):
        print(msg)
        # self.send_sysex(msg)

        # self.midi_data.send(data)

    def listen_data(self):
        print(self.midi_in)
        if self.midi_in:
            try:
                for msg in self.midi_in.poll():
                    print(msg)
            except Exception:
                pass

    @staticmethod
    def get_ports():
        return mido.get_output_names()

    _ANS = get_ports.__func__()

    def start(self):
        self._open_ports()
        self._native_on()
        time.sleep(0.5)
        self.open_input()
        self.padkontrol.register(self)
        time.sleep(1)
        self.__native = True
        self.listen_data()

    def stop(self):
        self._native_off()
        self._close_ports()


class Manager:
    def __init__(self):
        self._kontrol = None
        self.mode = None
        self._running = False

    def _midi_in_callback(self, message):
        # self.mode.process_sysex(message.bytes())
        sysex_buffer = []
        for byte in message.bytes():
            sysex_buffer.append(byte)
            if byte == 0xF7:
                self.mode.process_sysex(sysex_buffer)
                del sysex_buffer[:]

    def set_callback(self):
        self._kontrol.midi_in.callback = self._midi_in_callback

    def start(self):
        if not self._running:
            self._kontrol = Kontrol()
            self.mode = Mode1()
            # time.sleep(1)
            self._kontrol.start()
            self.set_callback()

            self.mode.midi_in = self._kontrol.midi_in
            self.mode.midi_out = self._kontrol.midi_out
            self._running = True

    def stop(self):
        self._kontrol.stop()
        self._running = False

    def notify(self, msg):
        print(msg)

    # def send_sysex(self, sysex):
    #     if self._running:
    #         self.mode.send_sysex()


def main():
    import sys, keyboard

    k = Kontrol()
    k.start()

    try:
        keyboard.wait("esc")
    except:
        print("")
    finally:
        k.stop()


if __name__ == "__main__":
    main()
