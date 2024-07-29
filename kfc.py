# import package
import pandas as pd
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
import time
from bs4 import BeautifulSoup
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from datetime import datetime
import json

# 현재 날짜 가져오기
current_date = datetime.now().strftime("%Y-%m-%d")
filename = f"kfc_{current_date}.json"

# run webdriver
driver = webdriver.Chrome()
keyword = 'KFC DT점'
url = f'https://map.naver.com/p/search/{keyword}'
driver.get(url)
action = ActionChains(driver)

naver_res = pd.DataFrame(columns=['title', 'address'])
last_name = ''

def search_iframe():
    driver.switch_to.default_content()
    driver.switch_to.frame("searchIframe")

def entry_iframe():
    driver.switch_to.default_content()
    WebDriverWait(driver, 2).until(EC.presence_of_element_located((By.XPATH, '//*[@id="entryIframe"]')))

    for i in range(5):
        time.sleep(.5)

        try:
            driver.switch_to.frame(driver.find_element(By.XPATH, '//*[@id="entryIframe"]'))
            break
        except:
            pass

def chk_names():
    search_iframe()
    elem = driver.find_elements(By.CSS_SELECTOR, '.place_bluelink')
    name_list = [e.text for e in elem]

    return elem, name_list

def crawling_main():
    global naver_res
    addr_list = []

    for e in elem:
        e.click()
        entry_iframe()
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # append data
        try:
            addr_list.append(soup.select('span.LDgIH')[0].text)
        except:
            addr_list.append(float('nan'))

        search_iframe()

    naver_temp = pd.DataFrame({
       'title': name_list,
        'address': addr_list
    })
    naver_res = pd.concat([naver_res, naver_temp])

def save_to_json():
    # 데이터를 JSON 파일로 저장
    naver_res.to_json(filename, orient='records', force_ascii=False, indent=4)

page_num = 1

while True:
    time.sleep(1.5)
    search_iframe()
    elem, name_list = chk_names()
    
    if not name_list:
        print("이름 리스트가 비어 있습니다.")
        break
    
    if last_name == name_list[-1]:
        break

    while True:
        # auto scroll
        action.move_to_element(elem[-1]).perform()
        time.sleep(1)  # 페이지 로드 시간을 조금 더 기다림
        elem, name_list = chk_names()

        if not name_list or last_name == name_list[-1]:
            break
        else:
            last_name = name_list[-1]

    crawling_main()

    # next page
    next_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//a[@class="eUTV2" and .//span[@class="place_blind" and text()="다음페이지"]]')))
            
    if next_button:
        next_button.click()
        print(f"{page_num} 페이지 완료")
        page_num += 1
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'place_bluelink')))
    else:
        print("마지막 페이지에 도달했습니다.")
        break

# JSON 파일로 저장
save_to_json()

# 브라우저 종료
driver.quit()


