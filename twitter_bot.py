from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from webdriver_manager.core.os_manager import ChromeType
from selenium_stealth import stealth

from urllib.parse import quote  # URL 인코딩을 위한 모듈
import time
import get_downdetector_web 
from datetime import datetime, timezone, timedelta

import logging
import time

# Twitter 로그인 페이지 URL
TWITTER_URL = "https://twitter.com/login"

def load_credentials(file_path):
    """파일에서 사용자 이름과 비밀번호를 읽어오는 함수."""
    with open(file_path, 'r') as file:
        lines = file.readlines()
        username = lines[0].strip()
        password = lines[1].strip()
        phone_number= lines[2].strip()
    return username, password,phone_number

def slow_typing(element, text, delay=0.05):
    """문자를 천천히 타이핑하는 함수."""
    for char in text:
        element.send_keys(char)
        time.sleep(delay)

def convert_to_kst(utc_datetime_str):
    # 문자열을 datetime 객체로 변환
    utc_time = datetime.strptime(utc_datetime_str, "%Y-%m-%dT%H:%M:%S.%fZ")

    # UTC 시간을 KST로 변환 (KST는 UTC+9)
    kst_time = utc_time.replace(tzinfo=timezone.utc).astimezone(timezone(timedelta(hours=9)))

    # KST 시간 문자열로 변환하여 반환
    return kst_time.strftime('%Y-%m-%d %H:%M:%S')

# # def twitter_login(driver, username, password):
# def twitter_login():
#     driver.get(TWITTER_URL)
#     logging.info(f"{TWITTER_URL} 접속 완료")
#     time.sleep(3)
    
#     # 사용자 이름 입력
#     username_input = WebDriverWait(driver, 30).until(
#         EC.presence_of_element_located((By.NAME, "text"))
#     )
#     slow_typing(username_input, username)
#     username_input.send_keys(Keys.RETURN)
    

#     # 비밀번호 입력
#     password_input = WebDriverWait(driver, 30).until(
#         EC.presence_of_element_located((By.NAME, "password"))
#     )
#     slow_typing(password_input, password)
#     password_input.send_keys(Keys.RETURN)
#     time.sleep(3)
def twitter_login():
    driver.get(TWITTER_URL)
    logging.info(f"{TWITTER_URL} 접속 완료")
    time.sleep(3)
    
    # 이미 로그인된 상태인지 확인
    if driver.current_url == "https://x.com/home":
        logging.info("이미 로그인 감지: 로그인 시도 중단")
        return
    
    try:
        # 사용자 이름 또는 전화번호 입력
        username_input = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.NAME, "text"))
        )
        slow_typing(username_input, phone_number)
        username_input.send_keys(Keys.RETURN)
        time.sleep(3)
        
        # 비정상 로그인이 감지되어 트위터 아이디를 입력해야 하는 상황 체크
        try:
            user_identifier_input = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.NAME, "text"))
            )
            slow_typing(user_identifier_input, username)
            user_identifier_input.send_keys(Keys.RETURN)
            time.sleep(3)
        except TimeoutException:
            logging.info("비정상 로그인 감지 없이 비밀번호 입력 화면으로 이동")

        # 비밀번호 입력
        password_input = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.NAME, "password"))
        )
        slow_typing(password_input, password)
        password_input.send_keys(Keys.RETURN)
        time.sleep(3)

    except TimeoutException:
        logging.error("요소를 찾을 수 없습니다.")
        return

# def twitter_login():
#     driver.get(TWITTER_URL)
#     logging.info(f"{TWITTER_URL} 접속 완료")
#     time.sleep(3)
    
#     # 리다이렉트 체크
#     if driver.current_url == "https://x.com/home":
#         logging.info("이미 로그인 감지: 로그인 시도 중단")
#         return
    
#     # 사용자 이름 입력
#     try:
#         username_input = WebDriverWait(driver, 30).until(
#             EC.presence_of_element_located((By.NAME, "text"))
#         )
#         slow_typing(username_input, username)
#         username_input.send_keys(Keys.RETURN)

#         # 비밀번호 입력
#         password_input = WebDriverWait(driver, 30).until(
#             EC.presence_of_element_located((By.NAME, "password"))
#         )
#         slow_typing(password_input, password)
#         password_input.send_keys(Keys.RETURN)
#         time.sleep(3)

#     except TimeoutException:
#         logging.error("요소를 찾을 수 없습니다.")
#         return

def scroll_down(driver, scroll_pause_time=2):
    """페이지를 아래로 스크롤하는 함수."""
    last_height = driver.execute_script("return document.body.scrollHeight")
    
    while True:
        # 페이지의 끝까지 스크롤 다운
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        
        # 새로운 내용이 로드될 때까지 대기
        time.sleep(scroll_pause_time)
        
        # 스크롤 후 새로운 높이 계산
        new_height = driver.execute_script("return document.body.scrollHeight")
        
        # 더 이상 스크롤할 내용이 없으면 종료
        if new_height == last_height:
            break
        
        last_height = new_height

# def search_tweets_once(driver, query):
def search_tweets_once(query):
    """한 번만 검색하여 트윗을 가져오는 함수."""
    # URL 인코딩
    logging.info(f"{query} 검색합니다.")
    encoded_query = quote(query)
    
    # 트위터 검색 URL 생성
    search_url = f"https://x.com/search?q={encoded_query}&src=typed_query&f=live"
    driver.get(search_url)
    logging.info(f"{query} 검색 완료")

    # 트윗 요소가 로드될 때까지 대기
    WebDriverWait(driver, 20).until(
        EC.presence_of_all_elements_located((By.XPATH, '//article[@role="article"]'))
    )

    tweets = driver.find_elements(By.XPATH, '//article[@role="article"]')
    tweets_text = []
    tweets_date = []
    tweets_link = []
    tweets_src = []
    
    all_tweets = []
    for tweet in tweets:
        try:
            tweet_text = tweet.find_element(By.XPATH, './/div[@data-testid="tweetText"]').text
            tweet_date = convert_to_kst(tweet.find_element(By.XPATH, './/time').get_attribute('datetime'))
            tweet_link = tweet.find_element(By.XPATH, './/a[@href]').get_attribute('href')

            tweets_text.append(tweet_text)
            tweets_date.append(tweet_date)
            tweets_link.append(tweet_link)
            tweets_src.append("twitter")

            all_tweets.append((tweet_text, tweet_date))
        except Exception as e:
            print(f"Error extracting tweet: {e}")
    return tweets_text, tweets_date, tweets_link, tweets_src
    # for idx, (tweet_text, tweet_date) in enumerate(all_tweets, start=1):
    #     print(f"Tweet {idx} [{tweet_date}]: {tweet_text}\n")

def search_tweets_scroll(driver, query, max_tweets=50):
    """스크롤 다운을 통해 여러 번 검색하여 트윗을 가져오는 함수."""
    # URL 인코딩
    encoded_query = quote(query)
    
    # 트위터 검색 URL 생성
    search_url = f"https://x.com/search?q={encoded_query}&src=typed_query&f=live"
    driver.get(search_url)

    # 트윗 요소가 로드될 때까지 대기
    WebDriverWait(driver, 20).until(
        EC.presence_of_all_elements_located((By.XPATH, '//article[@role="article"]'))
    )

    tweets_collected = 0
    all_tweets = []

    while tweets_collected < max_tweets:
        scroll_down(driver)
        
        # 현재까지 로드된 트윗을 수집
        tweets = driver.find_elements(By.XPATH, '//article[@role="article"]')
        for tweet in tweets[tweets_collected:]:
            try:
                tweet_text = tweet.find_element(By.XPATH, './/div[@data-testid="tweetText"]').text
                tweet_date = tweet.find_element(By.XPATH, './/time').get_attribute('datetime')
                all_tweets.append((tweet_text, tweet_date))
                tweets_collected += 1
                
                if tweets_collected >= max_tweets:
                    break
            except Exception as e:
                print(f"Error extracting tweet: {e}")
    
    for idx, (tweet_text, tweet_date) in enumerate(all_tweets, start=1):
        print(f"Tweet {idx} [{tweet_date}]: {tweet_text}\n")

# 크레덴셜 파일 경로
credentials_file = 'twitter_info.txt'

# # 사용자 이름과 비밀번호 로드
username, password, phone_number = load_credentials(credentials_file)
driver = get_downdetector_web.CHROME_DRIVER

logging.info('driver 불러오기 완료')
# twitter_login(driver, username, password)
# logging.info('트위터 로그인 완료')


def main():
    # 크레덴셜 파일 경로
    credentials_file = 'twitter_credentials.txt'

    # 사용자 이름과 비밀번호 로드
    username, password, phone_number = load_credentials(credentials_file)

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

    try:
        twitter_login(driver, username, password)
        
        # 한 번 검색하는 함수 호출
        query = "AT&T Outage"  # 검색할 트윗 주제 (예시)
        search_tweets_once(driver, query)

        # 스크롤 다운을 통해 여러 번 검색하는 함수 호출
        # search_tweets_scroll(driver, query, max_tweets=50)

    finally:
        driver.quit()
        
# if __name__ == "__main__":
#     main()