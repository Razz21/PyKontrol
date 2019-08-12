from functools import wraps
from midi_ports import (
    led,
    led_blink,
    light_blink,
    light_flash,
    light_off,
    light_on,
    translate_to_led,
)
import padKontrol as pk


def press_light(func):
    """sysEx light decorator:
    Turn on light on button press and turn off on release
    """

    @wraps(func)
    def wrapped(*args, **kwargs):
        sysEx = args[1] if len(args) > 1 else args[0]
        if sysEx.state in (pk.NOTE_ON, 1):
            light_on(sysEx.control)
        else:
            light_off(sysEx.control)
        return func(*args, **kwargs)

    return wrapped


def flash_light(duration=0.3):
    """sysEx light decorator:
    Oneshot light on button press

    Keyword Arguments:
        duration {float} -- range 0.0-1.0 (9ms - 279ms) (default: {0.3})
    """

    def wrapper(func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            sysEx = args[1] if len(args) > 1 else args[0]
            if sysEx.state in (pk.NOTE_ON, 1):
                light_flash(sysEx.control, duration)
            return func(*args, **kwargs)

        return wrapped

    return wrapper


def blink_light(func):
    """sysEx light decorator:
    Blink light on button press

    """

    @wraps(func)
    def wrapped(*args, **kwargs):
        sysEx = args[1] if len(args) > 1 else args[0]
        if sysEx.state in (pk.NOTE_ON, 1):
            light_blink(sysEx.control)
        return func(*args, **kwargs)

    return wrapped


def hold_light(func):
    """sysEx light decorator:
    Turn on light on button press and hold on release

    """

    @wraps(func)
    def wrapped(*args, **kwargs):
        sysEx = args[1] if len(args) > 1 else args[0]
        if sysEx.state in (pk.NOTE_ON, 1):
            light_on(sysEx.control)
        return func(*args, **kwargs)

    return wrapped


def release_light(func):
    """sysEx light decorator:
    Turn off constant light on button press

    """

    @wraps(func)
    def wrapped(*args, **kwargs):
        sysEx = args[1] if len(args) > 1 else args[0]
        if sysEx.state in (pk.NOTE_ON, 1):
            light_off(sysEx.control)
        return func(*args, **kwargs)

    return wrapped


# ------- decorator functions to handle common events sysex messages ------


def action_on_press(reset_led=False, led_msg=None):
    """sysEx event decorator:
    Call function only on button / pad press event
    and ignore release sysEx messages from same controller.

    Keyword Arguments:
        reset_led {bool} -- reset message on button release (default: {False})
        led_msg {string} -- displayed message (default: {None})

    """

    def wrapper(func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            sysEx = args[1] if len(args) > 1 else args[0]
            if sysEx.state in (pk.NOTE_ON, 1):
                return func(*args, **kwargs)
            else:
                if reset_led:
                    m = led_msg
                    try:
                        m = getattr(args[0], led_msg)
                    except:
                        pass
                    msg = translate_to_led(m)
                    led(msg)

        return wrapped

    return wrapper
