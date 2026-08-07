import dotenv
dotenv.load_dotenv()

import reflex as rx

config = rx.Config(
    app_name="fantasy_football_dashboard", 
    plugins=[
        rx.plugins.TailwindV3Plugin(),
        rx.plugins.SitemapPlugin()
    ]
)
