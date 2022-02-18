from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from pathlib import Path
import zipfile, io
import os


def browser_function():
    driver_path = "chromedriver"
    chr_options = Options()
    prefs = {"download.default_directory": os.getcwd() + "\\tmp"}
    chr_options.add_experimental_option("prefs", prefs)
    chr_options.add_experimental_option("detach", True)
    chr_driver = webdriver.Chrome(driver_path, options=chr_options)
    return chr_driver


print("cgtrader")
chr_driver = browser_function()
chr_driver.get('https://www.cgtrader.com/')


def download_cgt_file(product_id, product_name, file_id, dest_file):
    path_info = Path(dest_file)
    file_name = path_info.name

    import requests
    chr_driver.get("https://www.cgtrader.com/profile/purchases")
    chr_driver.implicitly_wait(0.5)
    search_bar = chr_driver.find_element_by_xpath('//*[@id="purchases_query_input"]')
    search_bar.send_keys(product_name)
    search_button = chr_driver.find_element_by_xpath('//button[@class="btn btn-transparent"]')
    search_button.click()

    for product in chr_driver.find_elements_by_xpath('//button[@class="button button--alt js-download u-mr10 u-mb10"]'):
        if product.get_attribute('data-href').startswith(f"/items/{product_id}"):
            product.click()
            break

    is_zip = chr_driver.find_elements_by_xpath('//ul[@class="details-box__list"]/li')

    for i, file in enumerate(chr_driver.find_elements_by_xpath('//a[@rel="nofollow"]')):
        if file.get_attribute('href').startswith(f"/items/{product_id}/downloads/{file_id}"):
            break

    if is_zip[i].text.split('\n')[0] == file_name:
        headers = {
            "User-Agent":
                "Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36"
        }
        s = requests.session()
        s.headers.update(headers)

        for cookie in chr_driver.get_cookies():
            c = {cookie['name']: cookie['value']}
            s.cookies.update(c)
        # TODO
    else:
        headers = {
            "User-Agent":
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.82 Safari/537.36",
            #":path": file.get_attribute("href").replace('https://www.cgtrader.com', ""),
            "upgrade-insecure-requests": "1",
            "sec-fetch-user": "?1",
            "sec-fetch-site": "same-origin",
            "sec-fetch-mode": "navigate",
            "sec-fetch-dest": "document",
            "sec-ch-ua-platform": "Windows",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua": 'Not A;Brand";v="99", "Chromium";v="98", "Google Chrome";v="98"',
            "referer": f"https://www.cgtrader.com/profile/purchases?query={product_name.replace(' ', '+')}&page=1",
            "origin": "https://www.cgtrader.com",
            "content-type": "application/x-www-form-urlencoded",
            "content-length": "128",
            "cache-control": "max-age=0",
            "accept-language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
            "accept-encoding": "gzip, deflate, br",
            #"cookie":"ahoy_visitor=3a7fe06c-9020-4b62-b1ba-a662b2302c1b; _cgtrader_cookies_check=true; _cgtrader_f1r57v=2021-06-26+18%3A41%3A09+UTC; _cgtrader_uuid=78057227; ahoy_track=true; _cgtrader_auid99=eaef9174-3494-4c75-8903-251e17000ca5; _cgtrader_673cc0=36; ahoy_visit=467de547-205f-4c7c-86dc-ef946de17b9a; _cgtrader_cpsa48=true; _cgtrader_389537=120; _cgtrader_utoken=cHIyK1dVZXo3N3NzRVduL2tDZW5NbVFiQlI2MExFaFkwU0hyL2FaWHZLcz0tLWV0YXNRR1dsdlR0TXRacFZPZmlHUnc9PQ%3D%3D--8d1621559358f580b66463887ddca1fad1b8603d; _cgtrader_euid=fb17edeac9b2bd985e6e7cc826c93a6758f3ea29; _cgtrader_session_id=23da1d87836c842564c4e3b064e517b1; screen_width=1083; _cgtrader_98e316=%04%08%7B%09%3A%0Fpage_viewsiV%3A%0Bvisitsi%0C%3A%0Ftotal_timei%04%FF%287%01%3A%0Flast_visitl%2B%07%C4%9D%0Eb",
            #":authority": "www.cgtrader.com",
            #":scheme": "https",

        }
        s = requests.session()
        s.headers.update(headers)

        for cookie in chr_driver.get_cookies():
            c = {cookie['name']: cookie['value']}
            s.cookies.update(c)


        r = s.post(file.get_attribute("href"), allow_redirects=True)

        z = zipfile.ZipFile(io.BytesIO(r.content))

        for file in z.filelist:
            if file_name == file.filename.split('/')[-1]:
                file.filename = file.filename.split('/')[-1]
                z.extract(file, str(path_info.parent))
                print(f"File has been downloaded from Cults3d to {dest_file} !")
                return True
        return False

    product_id = 3584352
    product_name = "enclave trooper"
    file_id = 9776478