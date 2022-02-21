from pathlib import Path
import zipfile, io

from utils.download import browser_function

chr_driver = browser_function()
chr_driver.get('https://cults3d.com/en/users/sign-in')


def download_cults_file(url, dest_file):
    path_zip = Path(f"tmp/cults3d/{url.replace('/', '_').split('__cults3d.com_')[-1]}.zip")
    path_info = Path(dest_file)
    file_name = path_info.name

    if not path_zip.parent.is_dir():
        path_zip.parent.mkdir(parents=True, exist_ok=True)
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
        with open(path_zip, "wb") as f:
            f.write(r.content)

        for file in z.filelist:
            if file_name == file.filename.split('/')[-1]:
                file.filename = file.filename.split('/')[-1]
                z.extract(file, str(path_info.parent))
                print(f"File has been downloaded from Cults3d to {dest_file} !")
                return True
        return False
    else:
        z = zipfile.ZipFile(path_zip)
        for file in z.filelist:
            if file_name == file.filename.split('/')[-1]:
                file.filename = file.filename.split('/')[-1]
                z.extract(file, str(path_info.parent))
                print(f"File has been move from Cults3d cache to {dest_file} !")
                return True
        return False