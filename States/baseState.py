import padKontrol as pk
import mido
import time
import operator
from functools import wraps


class StateBase:
    """Base object for concrete configuration states.

    Global variables:
        _KNOBS -- knobs sysEx description.
        _RESERVED_CONTROLLERS -- controllers for global actions.
        _context -- context object reference.
        _name -- state specyfic name displayed on led.
        _GLOBAL_COMBINATIONS -- global hotkeys combinations dictionary:
            key: controls combination, value: called function name (string).
    """

    _KNOBS = [pk.ROTARY_KNOB, pk.KNOB_1, pk.KNOB_2]
    _RESERVED_CONTROLLERS = [pk.BUTTON_KNOB_1_ASSIGN, pk.BUTTON_KNOB_2_ASSIGN]
    _context = None
    _name = "base"
    _GLOBAL_COMBINATIONS = {
        frozenset([pk.BUTTON_SETTING, pk.ROTARY_KNOB]): "hotkey_method"
    }

    def __init__(self):
        self.hotkeys = set()
        # self.
        self._LOCAL_COMBINATIONS = {}

    def __str__(self):
        return self.name

    def hotkey_method(self):
        print("hotkey found!!")

    def translate_to_led(self, msg):
        """
        create 3 characters message for PK controller`s led display
        """
        if not isinstance(msg, (int, str, float)):
            msg = self.name
        return f"{str(msg)[:3]:>3}"

    @property
    def name(self):
        return self.translate_to_led(self._name)

    @property
    def context(self):
        return self._context

    @context.setter
    def context(self, context):
        self._context = context

    def send_sysex(self, sysex):
        """Generic data send method for context`s PK controller handler

        Arguments:
            sysex {list} -- sysex data
        """
        self._context.send_sysex(sysex)

    def send_midi(self, data):
        """Generic data send method for context`s host/reciver handler
        
        Arguments:
            data {list} -- midi data
        """
        self._context.send_midi(data)

    def load_state(self):
        """Generic initialization method for context object handler
        """
        self.send_sysex(pk.led(self.name))
        self._start()

    def change_state(self, data: int) -> None:
        """Change state trigger for context object

        Arguments:
            data {int} -- direction of state change:
            1 - next_state, {other} - previous state

        Returns:
            None -- load new state
        """

        self._pause()
        if data == 1:
            self._context.next_state()
        else:
            self._context.previous_state()

    # ------------------------handle events ---------------------------

    def handle_default_action(self, sysEx):
        """Handle pre-defined global actions
        
        Arguments:
        sysEx {SysexEvent} -- sysEx message from PK controller
        """
        if sysEx.control == pk.ROTARY_KNOB:
            self.change_state(sysEx.data)

    def catch_combination(self, sysEx):
        """Catch combo or fire default global action for reserved knobs/buttons.
        Check action flow:
        global combination -> default global action -> modes actions

        Arguments:
            sysEx {SysexEvent} -- sysEx message from PK controller

        Returns:
            bool -- global or local hotkey combo found
        """

        catched = False

        if sysEx.state in (pk.NOTE_ON, 1):
            # catch combination if button pressed or knob turned
            self.hotkeys.add(sysEx.control)
            if frozenset(self.hotkeys) in self._GLOBAL_COMBINATIONS:
                combo_method = self._GLOBAL_COMBINATIONS[frozenset(self.hotkeys)]
                #  find and call method in class scope
                operator.attrgetter(combo_method)(self)()

                catched = True
            elif frozenset(self.hotkeys) in self._LOCAL_COMBINATIONS:
                self._GLOBAL_COMBINATIONS[frozenset(self.hotkeys)]()
                catched = True
            # else:
            #     self.handle_default_action(sysEx)
        else:
            # remove from hotkeys queue on release
            self.hotkeys.discard(sysEx.control)

        # knobs do not send on/off state,
        # controller must be removed from hotkey queue every turn
        if sysEx.control in self._KNOBS:
            self.hotkeys.discard(sysEx.control)

        return catched

    def handle_event(self, sysEx):
        """Base event handler for State Object.

        Catch global events / controller combinations:
        - change mode,
        - transpose notes,  #TODO
        - etc.              #TODO
        or dispatch to state specyfic handler.

        Arguments:
            sysEx {SysexEvent} -- sysEx message from PK controller
        """

        # global events take prevedence over state actions or combinations
        if sysEx.control in self._RESERVED_CONTROLLERS:
            self.handle_default_action(sysEx)

        # catch controllers combination
        elif self.catch_combination(sysEx):
            return

        # pass signal to active state handler
        else:
            self.handle_state_event(sysEx)

    def handle_state_event(self, sysEx):
        """State specyfic sysEx event handler

        Arguments:
            sysEx {SysexEvent} -- sysEx message from PK controller
        """
        method = getattr(self, "handle_%s" % sysEx.type)
        method(sysEx)

    def handle_pad(self, sysEx):
        pass

    def handle_button(self, sysEx):
        pass

    def handle_rotary(self, sysEx):
        pass

    def handle_knob(self, sysEx):
        pass

    def handle_xy_pad(self, sysEx):
        pass

    # ------------------------ state runtime methods --------------------------

    def _start(self):
        """
        Load configuration specyfic initialization methods.
        Should be used in threading-driven configuration
        to call threading's .start() method
        """
        pass

    def _pause(self):
        """
        Handle threading-driven configuration method.
        Should be overriden to stop current configuration`s thread on state change
        """
        pass

    # ------------------------ sysex lights messages --------------------------

    def led(self, msg):
        self.send_sysex(pk.led(self.translate_to_led(msg)))

    def led_blink(self, msg):
        self.send_sysex(pk.led(self.translate_to_led(msg), pk.LED_STATE_BLINK))

    def light_on(self, control):
        self.send_sysex(pk.light(control, pk.LIGHT_STATE_ON))

    def light_off(self, control):
        self.send_sysex(pk.light(control, pk.LIGHT_STATE_OFF))

    def light_blink(self, control):
        self.send_sysex(pk.light(control, pk.LIGHT_STATE_BLINK))

    def light_flash(self, control, duration=0.5):
        self.send_sysex(pk.light_flash(control, duration))

    # ------- decorator functions to handle common light sysex messages -------

    @staticmethod
    def press_light(func):
        """sysEx light decorator:
        Turn on light on button press and turn off on release
        """

        @wraps(func)
        def wrapped(self, *args, **kwargs):
            sysEx = args[0]
            if sysEx.state in (pk.NOTE_ON, 1):
                self.light_on(sysEx.control)
            else:
                self.light_off(sysEx.control)
            return func(self, *args, **kwargs)

        return wrapped

    @staticmethod
    def flash_light(duration=0.3):
        """sysEx light decorator:
        Oneshot light on button press
        
        Keyword Arguments:
            duration {float} -- range 0.0-1.0 (9ms - 279ms) (default: {0.3})
        """

        def wrapper(func):
            @wraps(func)
            def wrapped(self, *args, **kwargs):
                sysEx = args[0]
                if sysEx.state in (pk.NOTE_ON, 1):
                    self.light_flash(sysEx.control, duration)
                return func(self, *args, **kwargs)

            return wrapped

        return wrapper

    @staticmethod
    def blink_light(func):
        """sysEx light decorator:
        Blink light on button press

        Arguments:
            func {function} -- wrapped function

        Returns:
            function -- wrapped function
        """

        @wraps(func)
        def wrapped(self, *args, **kwargs):
            sysEx = args[0]
            if sysEx.state in (pk.NOTE_ON, 1):
                self.light_blink(sysEx.control)
            return func(self, *args, **kwargs)

        return wrapped

    @staticmethod
    def hold_light(func):
        """sysEx light decorator:
        Turn on light on button press and hold on release

        Arguments:
            func {function} -- wrapped function

        Returns:
            function -- wrapped function
        """

        @wraps(func)
        def wrapped(self, *args, **kwargs):
            sysEx = args[0]
            if sysEx.state in (pk.NOTE_ON, 1):
                self.light_on(sysEx.control)
            return func(self, *args, **kwargs)

        return wrapped

    @staticmethod
    def release_light(func):
        """sysEx light decorator:
        Turn off constant light on button press

        Arguments:
            func {function} -- wrapped function
        
        Returns:
            function -- wrapped function
        """

        @wraps(func)
        def wrapped(self, *args, **kwargs):
            sysEx = args[0]
            if sysEx.state in (pk.NOTE_ON, 1):
                self.light_off(sysEx.control)
            return func(self, *args, **kwargs)

        return wrapped

    @staticmethod
    def action_on_press(reset_led=False, led_msg=None):
        """sysEx event decorator:
        Call function only on button / pad press event
        and ignore release sysEx messages from same controller.

        Keyword Arguments:
            reset_led {bool} -- restet message on controller release (default: {False})
            led_msg {string} -- displayed message (default: {None})

        Returns:
            function -- wrapped function
        """

        def wrapper(func):
            @wraps(func)
            def wrapped(self, *args, **kwargs):
                sysEx = args[0]
                if sysEx.state in (pk.NOTE_ON, 1):
                    return func(self, *args, **kwargs)
                else:
                    if reset_led:
                        msg = self.translate_to_led(led_msg)
                        self.led(msg)

            return wrapped

        return wrapper
