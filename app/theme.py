import reflex as rx
from app.states.theme_state import ThemeState

BRAND_RED = "#DC2626"
BRAND_RED_HOVER = "#B91C1C"
BRAND_BLUE = "#5B7BA5"
DARK_BG_PAGE = "#0F1119"
DARK_BG_SIDEBAR = "#161926"
DARK_BG_CARD = "#1C2033"
DARK_BORDER = "gray-800"
DARK_TEXT_PRIMARY = "white"
DARK_TEXT_SECONDARY = "gray-400"
DARK_TEXT_MUTED = "gray-500"
LIGHT_BG_PAGE = "#F8F9FC"
LIGHT_BG_SIDEBAR = "white"
LIGHT_BG_CARD = "white"
LIGHT_BORDER = "gray-200"
LIGHT_TEXT_PRIMARY = "gray-900"
LIGHT_TEXT_SECONDARY = "gray-500"
LIGHT_TEXT_MUTED = "gray-400"


def t(dark: str, light: str) -> rx.Var:
    """Theme-aware class selector. Returns rx.cond that picks dark or light classes."""
    return rx.cond(ThemeState.is_dark, dark, light)


PAGE_BG = t(f"bg-[{DARK_BG_PAGE}]", f"bg-[{LIGHT_BG_PAGE}]")
CARD = t(
    f"bg-[{DARK_BG_CARD}] border border-{DARK_BORDER} shadow-sm rounded-2xl",
    f"bg-{LIGHT_BG_CARD} border border-{LIGHT_BORDER} shadow-sm rounded-2xl",
)
TEXT_PRIMARY = t(f"text-{DARK_TEXT_PRIMARY}", f"text-{LIGHT_TEXT_PRIMARY}")
TEXT_SECONDARY = t(f"text-{DARK_TEXT_SECONDARY}", f"text-{LIGHT_TEXT_SECONDARY}")
TEXT_MUTED = t(f"text-{DARK_TEXT_MUTED}", f"text-{LIGHT_TEXT_MUTED}")
H1 = t("text-3xl font-bold text-white", "text-3xl font-bold text-gray-900")
H2 = t("text-2xl font-bold text-white", "text-2xl font-bold text-gray-800")
H3 = t("text-lg font-bold text-white", "text-lg font-bold text-gray-800")
INPUT = t(
    f"w-full px-4 py-2 bg-[{DARK_BG_PAGE}] text-white border border-gray-700 rounded-xl focus:ring-2 focus:ring-[{BRAND_RED}] outline-none",
    f"w-full px-4 py-2 bg-white text-gray-900 border border-gray-300 rounded-xl focus:ring-2 focus:ring-[{BRAND_RED}] outline-none",
)
TABLE_CONTAINER = t(
    f"bg-[{DARK_BG_CARD}] rounded-2xl border border-{DARK_BORDER} shadow-sm overflow-hidden overflow-x-auto",
    f"bg-{LIGHT_BG_CARD} rounded-2xl border border-{LIGHT_BORDER} shadow-sm overflow-hidden overflow-x-auto",
)
TABLE_HEADER_ROW = t(
    f"bg-[{DARK_BG_SIDEBAR}] border-b border-{DARK_BORDER}",
    f"bg-gray-50 border-b border-{LIGHT_BORDER}",
)
TABLE_HEADER_CELL = t(
    f"text-xs font-bold text-{DARK_TEXT_SECONDARY} uppercase tracking-wider",
    f"text-xs font-bold text-{LIGHT_TEXT_SECONDARY} uppercase tracking-wider",
)
TABLE_ROW = t(
    f"border-b border-{DARK_BORDER} hover:bg-[{DARK_BG_SIDEBAR}] transition-colors",
    f"border-b border-gray-100 hover:bg-gray-50 transition-colors",
)
BTN_PRIMARY = f"bg-[{BRAND_RED}] hover:bg-[{BRAND_RED_HOVER}] text-white font-bold py-3 rounded-xl transition-colors shadow-sm"
BTN_SECONDARY = t(
    f"bg-gray-800 border border-gray-700 text-gray-300 hover:bg-gray-700 rounded-xl transition-colors",
    "bg-gray-100 border border-gray-200 text-gray-700 hover:bg-gray-200 rounded-xl transition-colors",
)
BADGE_SUBTLE = t(
    "bg-gray-800 border border-gray-700 text-gray-400 text-xs font-medium px-2 py-1 rounded-md",
    "bg-gray-50 border border-gray-200 text-gray-600 text-xs font-medium px-2 py-1 rounded-md",
)
EMPTY_STATE = t(
    f"flex flex-col items-center justify-center py-20 bg-[{DARK_BG_CARD}] rounded-3xl border border-{DARK_BORDER} border-dashed",
    f"flex flex-col items-center justify-center py-20 bg-white rounded-3xl border border-{LIGHT_BORDER} border-dashed",
)
SELECT = t(
    f"appearance-none bg-[{DARK_BG_CARD}] border border-gray-700 text-white text-sm rounded-lg focus:ring-[{BRAND_RED}] focus:border-[{BRAND_RED}] block w-full p-2.5 outline-none font-medium",
    f"appearance-none bg-white border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-[{BRAND_RED}] focus:border-[{BRAND_RED}] block w-full p-2.5 outline-none font-medium",
)