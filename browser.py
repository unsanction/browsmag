from dataclasses import dataclass

import undetected_chromedriver as uc

from extension import BaseExtension


@dataclass
class Proxy:
    ip: str
    port: int
    login: str
    password: str


def init_driver(options) -> uc.Chrome:
    driver = uc.Chrome(options=options)
    driver.set_page_load_timeout(5000)
    return driver


def get_driver_options(options, extensions: list[BaseExtension], user_data_dir: str = None) -> uc.ChromeOptions:
    options.add_experimental_option("prefs", {
        "extensions.ui.developer_mode": True,  # Disable extension UI tab in browser on start
    })

    if extensions:
        options.add_argument(
            f"--load-extension=" + ",".join(
                [extension.dir for extension in extensions]
            )
        )

    if user_data_dir:
        options.add_argument(f"--user-data-dir={user_data_dir}")

    return options


def get_browser(extensions: list[BaseExtension], user_data_dir: str = None) -> uc.Chrome:
    return init_driver(get_driver_options(
        options=uc.ChromeOptions(),
        extensions=extensions,
        user_data_dir=user_data_dir,
    ))


