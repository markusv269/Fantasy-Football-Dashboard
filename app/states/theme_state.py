import reflex as rx


class ThemeState(rx.State):
    color_mode: str = rx.LocalStorage("light", name="sl_color_mode")
    mobile_sidebar_open: bool = False

    @rx.event
    def toggle_color_mode(self):
        if self.color_mode == "light":
            self.color_mode = "dark"
        else:
            self.color_mode = "light"

    @rx.event
    def toggle_mobile_sidebar(self):
        self.mobile_sidebar_open = not self.mobile_sidebar_open

    @rx.event
    def close_mobile_sidebar(self):
        self.mobile_sidebar_open = False

    @rx.var
    def is_dark(self) -> bool:
        return self.color_mode == "dark"