import os

#from selenium import webdriver
#from selenium.webdriver.chrome.options import Options


def every_downloads_chrome(driver):
    if not driver.current_url.startswith("chrome://downloads"):
        driver.get("chrome://downloads/")
    return driver.execute_script("""
        var items = document.querySelector('downloads-manager')
            .shadowRoot.getElementById('downloadsList').items;
        if (items.every(e => e.state === "COMPLETE"))
            return items.map(e => e.fileUrl || e.file_url);
        """)


def browser_function():
    driver_path = "./chromedriver"
    chr_options = Options()
    prefs = {"download.default_directory": os.getcwd() + "\\tmp"}
    chr_options.add_experimental_option("prefs", prefs)
    chr_options.add_experimental_option("detach", True)
    chr_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    chr_driver = webdriver.Chrome(driver_path, options=chr_options)
    return chr_driver
