import shutil


from pathlib import Path

import patoolib
#from selenium.webdriver.support.wait import WebDriverWait

#from minibuilder.utils.download import browser_function, every_downloads_chrome

#chr_driver = browser_function()
#chr_driver.get('https://www.cgtrader.com/')


def download_cgt_file(product_id, product_name, file_id, dest_file):
    is_dl_path = Path(f"tmp/CGT/{product_id}/{file_id}")

    path_info = Path(dest_file)
    path_info.parent.mkdir(parents=True, exist_ok=True)
    file_name = path_info.name

    if not is_dl_path.is_dir():
        chr_driver.get("https://www.cgtrader.com/profile/purchases")
        chr_driver.implicitly_wait(0.5)
        search_bar = chr_driver.find_element_by_xpath('//*[@id="purchases_query_input"]')
        search_bar.send_keys(product_name)
        search_button = chr_driver.find_element_by_xpath('//button[@class="btn btn-transparent"]')
        search_button.click()

        for product in chr_driver.find_elements_by_xpath('//button[@class="button button--alt js-download u-mr10 u-mb10"]'):
            if product.get_attribute('data-href').startswith(f"/items/{product_id}"):
                #product.location_once_scrolled_into_view
                chr_driver.implicitly_wait(0.5)
                product.click()
                chr_driver.implicitly_wait(0.5)
                break

        is_zip = chr_driver.find_elements_by_xpath('//ul[@class="details-box__list"]/li')

        try:
            for i, file in enumerate(chr_driver.find_elements_by_xpath('//a[@rel="nofollow"]')):
                if file.get_attribute('href').startswith(f"https://www.cgtrader.com/items/{product_id}/downloads/{file_id}"):
                    file_name_dl = is_zip[i].text.split('\n')[0]
                    file.location_once_scrolled_into_view
                    chr_driver.implicitly_wait(0.5)
                    file.click()
                    paths = WebDriverWait(chr_driver, 120, 1).until(every_downloads_chrome)
                    print(f"{dest_file} is beeing downloaded from CGT !")
                    file_dl = Path(paths[0].replace("file:///", "").replace('%20', " "))
                    new_dest = Path(is_dl_path.__str__() + "/" + file_dl.name)
                    new_dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(file_dl, new_dest.parent)
                    break
        except Exception as e:
            print(e)

        if file_name_dl == file_name:
            pass
        elif file_name_dl.endswith('.rar'):
            try:
                patoolib.extract_archive(str(new_dest), outdir=str(new_dest.parent))
                shutil.move(str(new_dest.parent) + f"/{file_name}", dest_file)
                return True
            except Exception as e:
                print(e)
                return False
    else:
        try:
            shutil.move(f"tmp/CGT/{product_id}/{file_id}" + f"/{file_name}", dest_file)
            return True
        except Exception as e:
            print(e)
            return False

    product_id = 3584352
    product_name = "enclave trooper"
    file_id = 9776478