import padKontrol as pk
import mido
import time

from functools import wraps


class StateBase:
    _KNOBS = [pk.ROTARY_KNOB, pk.KNOB_1, pk.KNOB_2]
    _RESERVED_CONTROLLERS = [pk.BUTTON_KNOB_1_ASSIGN, pk.BUTTON_KNOB_2_ASSIGN]
    _context = None
    _name = "base"

    def __init__(self):
        self.hotkeys = set()
        self._GLOBAL_COMBINATIONS = {
            frozenset([pk.BUTTON_SETTING, pk.ROTARY_KNOB]): "handle_event"
        }
        self._LOCAL_COMBINATIONS = {}

    def __str__(self):
        return self.name

    def translate_to_led(self, msg):
        """
        create 3 characters message for PK controller`s led display
        """
        assert isinstance(msg, (int, str, float))
        return f"{str(msg)[:3]:>3}"

    @property
    def name(self):
        return self.translate_to_led(self._name)

    @property
    def context(self):
        """
        context object reference
        """
        return self._context

    @context.setter
    def context(self, context):
        """
        context object reference setter
        """
        self._context = context

    def send_sysex(self, sysex):
        """
        send data to context`s PK controller handler
        """
        self._context.send_sysex(sysex)

    def send_midi(self, data):
        """
        send data to context`s host/reciver handler
        """
        self._context.send_midi(data)

    def load_state(self):
        """
        run initialization methods
        """
        self.send_sysex(pk.led(self.name))
        self._start()

    def change_state(self, data: int) -> None:
        """
        send data
        1       - switch to next state
        int !=1 - switch to previous state
        """
        self._pause()
        if data == 1:
            self._context.next_state()
        else:
            self._context.previous_state()

    # ------------------------handle events ---------------------------

    def handle_default_action(self, sysEx):
        """
        global default actions here
        """
        if sysEx.control == pk.ROTARY_KNOB:
            self.change_state(sysEx.data)

    def catch_combination(self, sysEx):
        """
        Catch combo or fire default global action for reserved knobs/buttons.
        Check action flow:
        global combination -> default global action -> modes actions
        Return:
            True, global event is firing and blocks modes actions,
            False, global action not used, pass message to active mode
        """

        catched = False

        if sysEx.state:
            # catch combination if button pressed or knob turned
            self.hotkeys.add(sysEx.control)
            if frozenset(self.hotkeys) in self._GLOBAL_COMBINATIONS:
                self._GLOBAL_COMBINATIONS[frozenset(self.hotkeys)]()
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
        """
        handle global events / button combinations:
        - change mode,
        - transpose notes,  #TODO
        - etc.              #TODO
        or dispatch to state specyfic actions
        """
        if sysEx.control in self._RESERVED_CONTROLLERS:
            # global action not overwritable
            self.handle_default_action(sysEx)
        else:
            catched = self.catch_combination(sysEx)
            if not catched:
                # pass signal to active state handler
                self.handle_state_event(sysEx)

    def handle_state_event(self, sysEx):
        """
        configuration specyfic message handler
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
        load configuration specyfic initialization methods;

        should be used in threading-driven configuration
        to call threading's .start() method
        """
        pass

    def _pause(self):
        """
        method to handle threading-driven configuration
        should be overriden to stop current configuration`s thread
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

    def light_blink(self, control, duration=0.5):
        self.send_sysex(pk.light_flash(control, duration))

    # ------- decorator functions to handle common light sysex messages -------

    @staticmethod
    def press_light(func):
        """
        turn on light on button press and turn off on release
        """

        @wraps(func)
        def wrapped(self, *args, **kwargs):
            sysEx = args[0]
            if sysEx.state == pk.NOTE_ON:
                self.light_on(sysEx.control)
            else:
                self.light_off(sysEx.control)
            return func(self, *args, **kwargs)

        return wrapped

    @staticmethod
    def blink_light(duration=0.3):
        """
        blink light on button press
        duration: float in range 0.0-1.0
        """

        def wrapper(func):
            @wraps(func)
            def wrapped(self, *args, **kwargs):
                sysEx = args[0]
                if sysEx.state == pk.NOTE_ON:
                    self.light_blink(sysEx.control, duration)
                return func(self, *args, **kwargs)

            return wrapped

        return wrapper

    @staticmethod
    def hold_light(func):
        """
        turn on light on button press and hold on release
        """

        @wraps(func)
        def wrapped(self, *args, **kwargs):
            sysEx = args[0]
            if sysEx.state == pk.NOTE_ON:
                self.light_on(sysEx.control)
            return func(self, *args, **kwargs)

        return wrapped

    @staticmethod
    def release_light(func):
        """
        turn off hold light on button press
        """

        @wraps(func)
        def wrapped(self, *args, **kwargs):
            sysEx = args[0]
            if sysEx.state == pk.NOTE_ON:
                self.light_off(sysEx.control)
            return func(self, *args, **kwargs)

        return wrapped
