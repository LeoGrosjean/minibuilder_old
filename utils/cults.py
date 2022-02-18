from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from pathlib import Path
import zipfile, io

def browser_function():
    driver_path = "chromedriver"
    chr_options = Options()
    chr_options.add_experimental_option("detach", True)
    chr_driver = webdriver.Chrome(driver_path, options=chr_options)
    return chr_driver

print("cults3d")
chr_driver = browser_function()
chr_driver.get('https://cults3d.com/en/users/sign-in')


def download_cults_file(url, dest_file):
    import requests
    chr_driver.get(url)
    button_dl = chr_driver.find_element_by_xpath('//button[@class="btn-group btn-group--large a-down-child-on-hover"]')
    button_dl.click()
    to_download = chr_driver.find_element_by_xpath('//a[text()="Download your files"]')
    headers = {
        "User-Agent":
            "Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36"
    }
    s = requests.session()
    s.headers.update(headers)

    for cookie in chr_driver.get_cookies():
        c = {cookie['name']: cookie['value']}
        s.cookies.update(c)

    r = s.get(to_download.get_attribute("href"))
    z = zipfile.ZipFile(io.BytesIO(r.content))
    path_info = Path(dest_file)
    file_name = path_info.name
    for file in z.filelist:
        if file_name == file.filename.split('/')[-1]:
            file.filename = file.filename.split('/')[-1]
            z.extract(file, str(path_info.parent))
            print(f"File has been downloaded from Cults3d to {dest_file} !")
            return True
    return False