import mido
import time
import padKontrol as pk


PADKONTROL_OUTPUT_PORT = "padKONTROL 1 CTRL 2"
PADKONTROL_INPUT_PORT = "padKONTROL 1 PORT A 1"

DATA_MIDI_PORT = "KorgLoopMidi 5"


_midi_in = None
_midi_out = None
_midi_out_data = None


def get_padkontrol_input(PADKONTROL_INPUT_PORT=PADKONTROL_INPUT_PORT):
    global _midi_in
    if not _midi_in:
        _midi_in = mido.open_input(PADKONTROL_INPUT_PORT)
    return _midi_in


def get_padkontrol_output(PADKONTROL_OUTPUT_PORT=PADKONTROL_OUTPUT_PORT):
    global _midi_out
    if not _midi_out:
        _midi_out = mido.open_output(PADKONTROL_OUTPUT_PORT)
    return _midi_out


def get_midi_out_data(DATA_MIDI_PORT=DATA_MIDI_PORT):
    global _midi_out_data
    if not _midi_out_data:
        _midi_out_data = mido.open_output(DATA_MIDI_PORT)
    return _midi_out_data


def get_midi_ports():
    midi_in = get_padkontrol_input()
    midi_out = get_padkontrol_output()
    midi_out_data = get_midi_out_data()
    return midi_in, midi_out, midi_out_data


def connect(
    midi_in=PADKONTROL_INPUT_PORT,
    midi_out=PADKONTROL_OUTPUT_PORT,
    midi_data=DATA_MIDI_PORT,
):
    _midi_in = get_padkontrol_input(midi_in)
    _midi_out = get_padkontrol_output(midi_out)
    _midi_out_data = get_midi_out_data(midi_data)
    _midi_in._rt.ignore_types(True, True, True)


def start_native(callback):
    send_sysex(pk.SYSEX_NATIVE_MODE_OFF)
    send_sysex(pk.SYSEX_NATIVE_MODE_ON)
    send_sysex(pk.SYSEX_NATIVE_MODE_ENABLE_OUTPUT)
    send_sysex(pk.SYSEX_NATIVE_MODE_INIT)
    send_sysex(pk.SYSEX_NATIVE_MODE_TEST)
    # these sysex messages are device specyfic and input port must ignore them
    # wait some time to avoid conflicts between I/O ports
    time.sleep(0.5)
    set_callback(callback)


def close_native():
    send_sysex(pk.SYSEX_NATIVE_MODE_OFF)
    disconnect()


def disconnect():
    global _midi_in, _midi_out, _midi_out_data
    _midi_in.close()
    _midi_out.close()
    _midi_out_data.close()


def set_callback(callback):
    global _midi_in
    if _midi_in:
        _midi_in.callback = callback
        _midi_in._rt.ignore_types(False, False, False)


def send_sysex(sysex):
    global _midi_out
    sysex = mido.parse(sysex)
    _midi_out.send(sysex)


def send_midi(data):
    global _midi_out_data
    if not isinstance(data, mido.Message):
        data = mido.Message(**data)
        _midi_out_data.send(data)


def translate_to_led(msg):
    """
    create 3 characters message for 7-segment led display
    """
    return f"{str(msg)[:3]:>3}"


def led(msg):
    send_sysex(pk.led(translate_to_led(msg)))


def led_blink(msg):
    send_sysex(pk.led(translate_to_led(msg), pk.LED_STATE_BLINK))


def light_on(control):
    send_sysex(pk.light(control, pk.LIGHT_STATE_ON))


def light_off(control):
    send_sysex(pk.light(control, pk.LIGHT_STATE_OFF))


def light_blink(control):
    send_sysex(pk.light(control, pk.LIGHT_STATE_BLINK))


def light_flash(control, duration=0.5):
    send_sysex(pk.light_flash(control, duration))


def group_light_on(buttons_or_pads: list) -> None:
    for btn_or_pad in buttons_or_pads:
        light_on(btn_or_pad)


def group_light_off(buttons_or_pads: list) -> None:
    for btn_or_pad in buttons_or_pads:
        light_off(btn_or_pad)
