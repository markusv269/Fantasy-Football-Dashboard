import dotenv
dotenv.load_dotenv()

import reflex as rx

config = rx.Config(app_name="app", plugins=[rx.plugins.TailwindV3Plugin()])
