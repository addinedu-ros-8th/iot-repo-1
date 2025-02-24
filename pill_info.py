from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
class Pill_info():
    def __init__(self):
        super().__init__()
        self.options= webdriver.ChromeOptions()

        self.prefs={'download.default_directory':'/home/sang/dev_ws/eda/data',
            'download.prompt_for_download':False}
        self.options.add_experimental_option('prefs',self.prefs)

        self.driver=webdriver.Chrome(service=Service('./driver/chromedriver/chromedriver'),
                                options=self.options)
        
        self.search_pill('vitamin c')
        time.sleep(3)
        self.collect_text()
        time.sleep(3)
        self.collect_translate()

    def search_pill(self,text):
        url='https://examine.com/'

        self.driver.get(url)
        search = self.driver.find_element(By.CSS_SELECTOR, ".rounded-md.border-gray-400")
        search.send_keys(text)
        self.driver.find_element(By.CSS_SELECTOR, ".size-5.fill-white.lg\\:size-6").click()
        time.sleep(1)
        self.driver.find_element(By.CSS_SELECTOR, "body > div:nth-child(3) > article > section > section > section > div:nth-child(1) > div > div > a.inline.cursor-pointer.py-2.align-middle.font-medium.text-examine-purple-400.hover\:underline.md\:text-lg.lg\:hover\:text-primary.xl\:text-2xl").click()

    def collect_text(self):
        self.pill_info_list=[]
        info = self.driver.find_elements(By.CSS_SELECTOR, '.summary.leading-7.-tracking-2.xl\\:text-xl.xl\\:leading-9')[:4]
        #print(len(info))

        for i in info:
            print(i.text)
            self.pill_info_list.append(i.text)
        self.driver.close()

    def collect_translate(self):
        url='https://translate.google.co.kr/?sl=auto&tl=en&op=translate&hl=ko'
        self.driver=webdriver.Chrome(service=Service('./driver/chromedriver/chromedriver'),
                                options=self.options)

        self.driver.get(url)
        self.translate_result_list = []

        for idx,i in enumerate(self.pill_info_list):
            trans=self.driver.find_element(By.CLASS_NAME,'er8xn')
            trans.click()
            time.sleep(2)
            trans.send_keys(i)
            time.sleep(2)
            if idx==0:
                korean_btn = self.driver.find_element(By.ID,'i16')
                korean_btn.click()

            time.sleep(2)
            
            translate_result = self.driver.find_elements(By.CLASS_NAME,'ryNqvb')
            for result in translate_result:
                print(result.text)
                self.translate_result_list.append(result.text)
            self.driver.find_element(By.CLASS_NAME,'DVHrxd').click()
        self.driver.close()
if __name__ == "__main__":
    myWindows = Pill_info()