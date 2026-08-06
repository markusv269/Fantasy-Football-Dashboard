import reflex as rx

from app.components.fantasyboerse import fantasyboerse_page_content
from app.components.layout import layout


def fantasyboerse_page() -> rx.Component:
    return layout(fantasyboerse_page_content(), full_width=True)
