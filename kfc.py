import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from datetime import datetime
from selenium.webdriver import ActionChains
import time
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 현재 날짜 가져오기
current_date = datetime.now().strftime("%Y-%m-%d")
filename = f"lotte/lotte_{current_date}.json"

# ChromeOptions 객체 생성
chrome_options = ChromeOptions()
chrome_options.add_argument("--headless")  # 헤드리스 모드 사용
chrome_options.add_argument("--no-sandbox")  # 샌드박스 사용 안 함
chrome_options.add_argument("--disable-dev-shm-usage")  # 공유 메모리 사용 안 함
chrome_options.add_argument("--disable-gpu")  # GPU 사용 안 함
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

# ChromeDriver 경로 설정
service = ChromeService(executable_path=ChromeDriverManager().install())

# WebDriver 객체 생성
driver = webdriver.Chrome(service=service, options=chrome_options)

keyword = '롯데리아 DT점'
url = f'https://map.naver.com/p/search/{keyword}'
driver.get(url)
action = ActionChains(driver)

naver_res = pd.DataFrame(columns=['title', 'address'])
last_name = ''

def search_iframe():
    try:
        driver.switch_to.default_content()
        logger.info("Waiting for searchIframe to be available...")
        iframe_present = WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.ID, "searchIframe")))
        if iframe_present:
            driver.switch_to.frame(iframe_present)
            logger.info("Switched to searchIframe")
        else:
            logger.error("searchIframe not found")
    except Exception as e:
        logger.error(f"Error switching to iframe: {e}")

def entry_iframe():
    try:
        driver.switch_to.default_content()
        logger.info("Waiting for entryIframe to be available...")
        iframe_present = WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.ID, "entryIframe")))
        if iframe_present:
            driver.switch_to.frame(iframe_present)
            logger.info("Switched to entryIframe")
        else:
            logger.error("entryIframe not found")
    except Exception as e:
        logger.error(f"Error switching to entry iframe: {e}")

def chk_names():
    search_iframe()
    try:
        WebDriverWait(driver, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.place_bluelink')))
        elem = driver.find_elements(By.CSS_SELECTOR, '.place_bluelink')
        name_list = [e.text for e in elem]
        logger.info(f"Names found: {name_list}")
        return elem, name_list
    except Exception as e:
        logger.error(f"Error checking names: {e}")
        return [], []

def crawling_main(elem, name_list):
    global naver_res
    addr_list = []

    for e in elem:
        try:
            e.click()
            time.sleep(20)  # 페이지 로드 시간을 기다림
            entry_iframe()
            soup = BeautifulSoup(driver.page_source, 'html.parser')

            # append data
            try:
                addr_list.append(soup.select('span.LDgIH')[0].text)
            except IndexError:
                addr_list.append(float('nan'))

            search_iframe()
        except Exception as ex:
            logger.error(f"Error during main crawling: {ex}")

    naver_temp = pd.DataFrame({
       'title': name_list,
        'address': addr_list
    })
    naver_res = pd.concat([naver_res, naver_temp], ignore_index=True)

def save_to_json():
    naver_res.to_json(filename, orient='records', force_ascii=False, indent=4)
    logger.info(f"Data saved to {filename}")

page_num = 1

while True:
    time.sleep(20)
    elem, name_list = chk_names()
    
    if not name_list:
        logger.info("이름 리스트가 비어 있습니다.")
        break
    
    if last_name == name_list[-1]:
        break

    while True:
        try:
            action.move_to_element(elem[-1]).perform()
            time.sleep(2)  # 페이지 로드 시간을 조금 더 기다림
            elem, name_list = chk_names()

            if not name_list or last_name == name_list[-1]:
                break
            else:
                last_name = name_list[-1]
        except Exception as e:
            logger.error(f"Error during scrolling: {e}")
            break

    crawling_main(elem, name_list)

    # next page
    try:
        next_button = WebDriverWait(driver, 60).until(EC.element_to_be_clickable((By.XPATH, '//a[@class="eUTV2" and .//span[@class="place_blind" and text()="다음페이지"]]')))
        if next_button:
            next_button.click()
            logger.info(f"{page_num} 페이지 완료")
            page_num += 1
            WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.CLASS_NAME, 'place_bluelink')))
        else:
            logger.info("마지막 페이지에 도달했습니다.")
            break
    except Exception as e:
        logger.error(f"Error finding or clicking the next button: {e}")
        break

# JSON 파일로 저장
save_to_json()

# 브라우저 종료
driver.quit()
