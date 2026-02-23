# browser_engine.py

from selenium import webdriver
from selenium.webdriver.edge.options import Options


class EdgeEngine:
    _driver = None  # persistent shared driver

    @classmethod
    def get_driver(cls):
        if cls._driver is None:
            options = Options()
            options.add_argument("--start-maximized")

            # ⚠️ DO NOT use your real profile unless absolutely necessary
            # If you want persistence, create a clean automation folder instead:
            # options.add_argument(r"--user-data-dir=C:\EdgeAutomationProfile")

            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option("useAutomationExtension", False)

            cls._driver = webdriver.Edge(options=options)

        return cls._driver

    @classmethod
    def close_driver(cls):
        if cls._driver:
            cls._driver.quit()
            cls._driver = None