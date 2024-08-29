# pip install selenium
# pip install webdriver-manager
# pip install undetected-chromedriver
# pip install selenium_stealth
import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType
from selenium_stealth import stealth
import pandas as pd
import sys
import logging
import matplotlib.pyplot as plt

# 필드명
NAME = 'Name'
VALUES = "Values"
CLASS = "Class"
AREA = "Area"
CATEGORY = "Category"

# 클래스명
DANGER = "danger"
WARNING = 'warning'
SUCCESS = 'success'

# 카테고리명
TELECOM = 'telecom'
ONLINE_SERVICE = 'online-services'
SOCIAL_MEDIA = 'social-media'
FINANCE = 'finance'
GAMING = 'gaming'


# 로깅 설정
# logging.basicConfig(level=logging.INFO)


# # # # # # # # # # # # # # # # # # # #


logging.info('CHROME_DRIVER 초기화 시작')


@st.cache_resource
def get_driver():
    logging.info(f'{sys.platform=}')
    if sys.platform == 'win32' or sys.platform == 'darwin':
        # 윈도우 또는 맥일 경우
        new_driver = webdriver.Chrome(
            service=ChromeService(ChromeDriverManager().install()),
            options=options
        )
    else:
        # 리눅스 서버일 경우
        new_driver = webdriver.Chrome(
            service=ChromeService(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install()),
            options=options,
        )

    stealth(new_driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
            )

    return new_driver


# Selenium 설정
options = Options()
options.add_argument("start-maximized")
options.add_argument("--disable-gpu")
# options.add_argument("--headless")
# options.add_argument("--headless=new")  # 최신 헤드리스 모드를 사용

# options.add_argument("--no-sandbox")
# options.add_argument("--disable-dev-shm-usage")

options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)

# verify=False 관련 설정
options.add_argument('--ignore-certificate-errors')
options.add_argument('--disable-web-security')
options.add_argument('--allow-running-insecure-content')


# # # # # # # # # #
# 드라이버 초기화
# # # # # # # # # #


logging.info('CHROME_DRIVER 초기화 시작')
CHROME_DRIVER = get_driver()
logging.info('CHROME_DRIVER 초기화 완료')


# # # # # # # # # # # # # # # # # # # #


# 임팩트 클래스를 숫자 등급으로 변환
def get_impact_order(impact_class):
    if impact_class == DANGER:
        return 3
    elif impact_class == WARNING:
        return 2
    elif impact_class == SUCCESS:
        return 1
    else:
        return 0  # 예외 처리


# 다운디텍터 크롤링
@st.cache_data(show_spinner='서비스 상태 업데이트 중...')
def get_downdetector_df(url, area, service_name=None):
    global CHROME_DRIVER

    logging.info(f'다운디텍터 크롤링 시작 - {url} {area}')

    # if service_name:
    # https://downdetector.com/status/{service_name}/

    try:
        CHROME_DRIVER.get(url)
    except Exception as e:
        logging.error(f'크롬 get 에러 발생!!! - {url} - {area}')
        logging.error(f"{e}")

        logging.info('CHROME_DRIVER 초기화 시작')
        CHROME_DRIVER.quit()

        get_driver.clear()  # 캐시 삭제

        CHROME_DRIVER = get_driver()
        logging.info('CHROME_DRIVER 초기화 완료')

        logging.info('1회 재시도!!!')
        try:
            CHROME_DRIVER.get(url)
        except Exception as e:
            logging.error(f'재시도 get도 에러 발생!!! - {url} - {area}')
            logging.error(f"{e}")
            logging.error('None 리턴!')
            return None

    # 페이지 로딩 대기
    try:
        WebDriverWait(CHROME_DRIVER, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".caption")))
    except Exception as e:
        logging.error(f"{e}")
        logging.error('최대 시간 동안 기다려도 페이지 로딩에 실패한 경우 - 그대로 처리한다.')

    logging.info(f'다운디텍터 크롤링 완료 - {url} {area}')

    # 서비스명, data-values, 영향도 클래스 추출
    services = CHROME_DRIVER.find_elements(By.CSS_SELECTOR, ".caption")
    data = []

    for service in services:
        try:
            name = service.find_element(By.TAG_NAME, "h5").text
            data_values = service.find_element(By.CLASS_NAME, "sparkline").get_attribute("data-values")
            sparkline_classes = service.find_element(By.CLASS_NAME, "sparkline").get_attribute("class").split()
            impact_class = SUCCESS
            for item in sparkline_classes:
                if item in [DANGER, WARNING, SUCCESS]:
                    impact_class = item
                    break

            data.append({NAME: name, VALUES: data_values, CLASS: impact_class})

        except Exception as e:
            logging.error(f"Error extracting data for a service: {e}\n{url} - {area} - {service}")

    # 브라우저 종료
    # CHROME_DRIVER.quit()

    df_ = pd.DataFrame(data)

    # 크롤링 실패 또는 비정상일 경우 None 리턴.
    if df_ is None or len(df_) == 0:
        return None

    df_sorted = df_.sort_values(by=CLASS, key=lambda x: x.map(get_impact_order), ascending=False)
    df_sorted = df_sorted.reset_index(drop=True)
    df_sorted[AREA] = area  # 지역 컬럼 추가

    # for debug
    logging.debug(str(df_sorted))

    # log_str = f'\n---------- {url} ----------\n'
    # for i, row in df_sorted.iterrows():
    #     log_str += f'{row[NAME]}\t{row[AREA]}\t{row[CLASS]}\t{row[VALUES]}\n'
    # log_str += '------------------------------\n\n'
    # logging.info(log_str)

    return df_sorted


def make_plot(df_):
    # 색상 매핑 딕셔너리
    color_map = {DANGER: 'red', WARNING: 'orange', SUCCESS: 'green'}

    # 서브플롯 그리기
    fig, axs = plt.subplots(len(df_), figsize=(10, 8))

    # 각 행에 대해 서브플롯 그리기
    for i, row in df_.iterrows():
        # 각 impact_class에 해당하는 색상 선택
        color = color_map.get(row[CLASS], 'blue')  # 없는 경우 기본값으로 파란색 지정
        data_values = [int(x) for x in row[VALUES].strip('[]').split(', ')]
        axs[i].plot(data_values, color=color)  # 색상 적용
        axs[i].set_title(row[NAME])

    plt.tight_layout()
    plt.show()


if __name__ == '__main__':
    # test code
    df = get_downdetector_df(url='https://downdetector.com/telecom/', area='US')
    if df is not None:
        df_sample = df.head(5).reset_index(drop=True)
        make_plot(df_sample)
    # CHROME_DRIVER.quit()  # 테스트일 경우엔 종료해준다.


