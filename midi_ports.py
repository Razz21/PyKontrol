import mido
import time
import padKontrol as pk

# should be named 'padKONTROL 1 CTRL' or similar.
PADKONTROL_OUTPUT_PORT = "padKONTROL 1 CTRL 2"
# should be named 'padKONTROL 1 PORT A' or similar
PADKONTROL_INPUT_PORT = "padKONTROL 1 PORT A 1"

# external midi port to send midi messages
DATA_MIDI_PORT = "KorgLoopMidi 4"


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
        _midi_out_data = mido.open_output(DATA_MIDI_PORT, autoreset=True)
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
    # these sysex messages are device specyfic and input port must ignore them.
    # wait some time to avoid conflicts between I/O midi ports
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


def ascii_to_led(char, pos=0):
    """translate non supported ascii characters to SysEx message for
        7 segment led display

    Arguments:
        char {string} -- ASCII symbol
        pos {integer} -- led character (1,2 or 3)

    Returns:
        list -- SysEx symbol representation
    """

    chars = {"#": [pk.FIRST_A, pk.FIRST_B, pk.FIRST_F, pk.FIRST_G]}
    symbol = chars.get(char, None)
    if symbol:
        # SysEx symbols in reverse order
        symbol = [x - (8 * pos) for x in symbol]
    return symbol


def translate_to_led(msg):
    """
    create 3 characters message for 7-segment led display
    """
    s = ""
    custom = []
    msg = f"{str(msg)[:3]:>3}"
    for idx, char in enumerate(msg):
        c = ascii_to_led(char, idx)
        if c:
            custom.append(c)
            s += " "  # empty space - string must be 3 chars long
        else:
            s += char
    return s, custom


def led(msg, led_state=pk.LED_STATE_ON):
    """Set led message

    Arguments:
        msg {string} -- message to display (or first 3 characters of string)
    """
    msg, custom = translate_to_led(msg)
    send_sysex(pk.led(msg, led_state))  # send valid characters as string
    if custom:
        # unsupported characters must be created segment by segment
        light_state = pk.LIGHT_STATE_ON
        if led_state == pk.LED_STATE_BLINK:
            light_state = pk.LIGHT_STATE_BLINK
        for char in custom:
            for c in char:
                send_sysex(pk.light(c, light_state))


def led_reset():
    """Clear led display
    """
    send_sysex(pk.led([0x29, 0x29, 0x29]))


def led_blink(msg):
    led(msg, pk.LED_STATE_BLINK)


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
