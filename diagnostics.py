"""Non-destructive Replit/browser diagnostics for the project.

This script does not submit account credentials. It verifies that Python can
start Chromium/ChromeDriver and that the public Google sign-in page loads.
"""

import shutil
import sys

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

import config
from device_simulator import create_device_profile


def main() -> int:
    chromium = (
        shutil.which("chromium")
        or shutil.which("chromium-browser")
        or shutil.which("google-chrome")
        or shutil.which("google-chrome-stable")
    )
    chromedriver = shutil.which("chromedriver")

    print("Python:", sys.version.split()[0])
    print("Chromium:", chromium or "NOT FOUND")
    print("ChromeDriver:", chromedriver or "NOT FOUND")

    if not chromium or not chromedriver:
        print("ERROR: Chromium/ChromeDriver is not available on PATH.")
        return 2

    profile = create_device_profile()
    options = Options()
    options.binary_location = chromium
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=390,844")
    options.add_argument(f"--user-agent={profile.user_agent}")

    driver = None
    try:
        driver = webdriver.Chrome(
            service=Service(executable_path=chromedriver),
            options=options,
        )
        driver.set_page_load_timeout(config.PAGE_LOAD_TIMEOUT)
        driver.get(config.GMAIL_LOGIN_URL)

        inputs = driver.find_elements(By.TAG_NAME, "input")
        visible_inputs = []
        for element in inputs:
            try:
                if element.is_displayed():
                    visible_inputs.append(
                        {
                            "type": element.get_attribute("type"),
                            "name": element.get_attribute("name"),
                            "id": element.get_attribute("id"),
                            "aria-label": element.get_attribute("aria-label"),
                        }
                    )
            except Exception:
                pass

        print("URL:", driver.current_url)
        print("Title:", driver.title)
        print("Visible inputs:", visible_inputs)

        has_identifier = any(
            item.get("id") == "identifierId"
            or item.get("name") == "identifier"
            or item.get("type") == "email"
            for item in visible_inputs
        )
        print("Google identifier field detected:", "YES" if has_identifier else "NO")
        return 0 if has_identifier else 3
    except Exception as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}")
        return 1
    finally:
        if driver is not None:
            try:
                driver.quit()
            except Exception:
                pass


if __name__ == "__main__":
    raise SystemExit(main())
