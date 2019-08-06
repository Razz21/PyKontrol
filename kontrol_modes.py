class ModeBase:
    def __init__(self, *args, **kwargs):
        self.name = ""
        self.__MODE_COMBINATIONS = []
        self.hotkeys = set()

    def __str__(self):
        return self.name

    def handle_event(self, msg):
        pass


class Mode1(ModeBase):
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.name = "md1"

    def handle_event(self, msg):
        group, symbol, state, *data = msg
        if group == "button":
            if state:
                send_sysex(pk.light(symbol, const.LIGHT_STATE_ON))
            else:
                send_sysex(pk.light(symbol, const.LIGHT_STATE_OFF))


class Mode2(ModeBase):
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.name = "md2"

    def handle_event(self, msg):
        group, symbol, state, *data = msg
        if group == "pad":
            if state:
                velocity = data
                send_sysex(pk.light_flash(symbol, 0.5))


class Mode3(ModeBase):
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.name = "md3"

    def handle_event(self, msg):
        group, symbol, state, *data = msg
        pass
