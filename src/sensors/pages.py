"""Display page definitions. Each page renders a subset of ECUData."""


class Page:
    def __init__(self, name):
        self.name = name

    def render(self, data, active_alerts):
        raise NotImplementedError

    def on_touch(self, x, y, ui):
        ui.next_page()   # default: tap advances page


class LiveEnginePage(Page):
    def render(self, data, active_alerts):
        # boost actual vs target (auto-scaled), RPM, temps, rail, gear
        ...


class EngineHealthPage(Page):
    def render(self, data, active_alerts):
        # rail pressure trend, fuel rate, voltage, oil status, fault count
        ...


class TimersPage(Page):
    def render(self, data, active_alerts):
        # 0-100, 0-200, 100-200, peak boost
        ...


class TransmissionPage(Page):
    def render(self, data, active_alerts):
        # gear, fluid temp, TCC lockup, shift quality
        ...


def build_pages():
    return [LiveEnginePage("Live Engine"),
            EngineHealthPage("Engine Health"),
            TimersPage("Timers"),
            TransmissionPage("Transmission")]
