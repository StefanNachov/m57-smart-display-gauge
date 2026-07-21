"""Touchscreen UI: page manager + touch input handling for ILI9341 + XPT2046.

Renders via luma.lcd. Pages are defined in pages.py. Touch zones map to page
navigation and settings controls. This module is the integration point; the
rendering primitives depend on the chosen display library.
"""
from . import pages


class UI:
    def __init__(self, data, alerts, relay):
        self.data, self.alerts, self.relay = data, alerts, relay
        self.page_index = 0
        self.pages = pages.build_pages()

    def next_page(self):
        self.page_index = (self.page_index + 1) % len(self.pages)

    def render(self):
        """Draw the current page + any active alert banner."""
        page = self.pages[self.page_index]
        page.render(self.data, self.alerts.active)

    def on_touch(self, x, y):
        """Route a touch event to the active page's hit zones."""
        self.pages[self.page_index].on_touch(x, y, self)
