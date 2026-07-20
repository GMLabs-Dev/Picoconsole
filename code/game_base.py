EXIT = "EXIT_TO_LAUNCHER"


class Game:
    name = "Untitled Game"
    description = ""
    accent_color = None

    def on_enter(self, display, buttons):
        pass

    def update(self, display, buttons, dt_ms):
        raise NotImplementedError

    def on_exit(self):
        pass
