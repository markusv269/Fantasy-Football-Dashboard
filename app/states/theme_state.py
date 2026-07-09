import reflex as rx


class ThemeState(rx.State):
    """Retains mobile sidebar state only. Color mode is handled by Reflex standard color mode."""

    mobile_sidebar_open: bool = False

    @rx.event
    def toggle_mobile_sidebar(self):
        self.mobile_sidebar_open = not self.mobile_sidebar_open

    @rx.event
    def close_mobile_sidebar(self):
        self.mobile_sidebar_open = False
