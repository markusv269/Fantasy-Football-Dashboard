import dotenv
dotenv.load_dotenv()

import reflex as rx

config = rx.Config(
    app_name="stoned_lack_leagues", 
    plugins=[
        rx.plugins.TailwindV3Plugin(),
        rx.plugins.SitemapPlugin()
    ]
)
