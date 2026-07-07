import reflex as rx


class ThemeState(rx.State):
    color_mode: str = rx.LocalStorage("light", name="sl_color_mode")
    mobile_sidebar_open: bool = False

    @rx.event
    def toggle_color_mode(self):
        if self.color_mode == "dark":
            self.color_mode = "light"
        else:
            self.color_mode = "dark"

    @rx.event
    def set_light_mode(self):
        self.color_mode = "light"

    @rx.event
    def set_dark_mode(self):
        self.color_mode = "dark"

    @rx.event
    def toggle_mobile_sidebar(self):
        self.mobile_sidebar_open = not self.mobile_sidebar_open

    @rx.event
    def close_mobile_sidebar(self):
        self.mobile_sidebar_open = False

    @rx.var
    def is_dark(self) -> bool:
        return self.color_mode == "dark"

    @rx.var
    def appearance(self) -> str:
        return "dark" if self.color_mode == "dark" else "light"

    @rx.var
    def shell_class(self) -> str:
        return (
            "font-['Inter'] text-white bg-[#0F1119]"
            if self.color_mode == "dark"
            else "font-['Inter'] text-gray-900 bg-[#F8F9FC]"
        )
