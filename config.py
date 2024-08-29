import os
import logging
import pickle
import streamlit as st
import time
import pandas as pd
from datetime import datetime
import pytz


# 한국 시간대를 사용하여 시간 생성
class KSTFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        kst = pytz.timezone('Asia/Seoul')
        # record.created를 변경하지 않고, 변환된 시간을 생성
        created_time = datetime.fromtimestamp(record.created, kst)
        if datefmt:
            return created_time.strftime(datefmt)
        else:
            return created_time.strftime('%Y-%m-%d %H:%M:%S')


# 로그 포맷 설정 (한국 시간대 포함)
log_format = '%(asctime)s - %(levelname)s : %(message)s'

# 로깅 설정
# 로그 핸들러 설정
handler = logging.StreamHandler()
handler.setFormatter(KSTFormatter(log_format))

# 기본 로거 설정
logging.basicConfig(level=logging.INFO, handlers=[handler])


# # # # # # # # # # # # # # # # # # # #


import get_downdetector_web


# 파일명 등 각종 설정
AREA_LIST = ['US', 'JP']

DASHBOARD_US_PAGE = 'pages/dashboard_us.py'
DASHBOARD_JP_PAGE = 'pages/dashboard_jp.py'
NEWSBOT_PAGE = 'pages/news_bot_dd.py'
SNSBOT_PAGE = 'pages/sns_bot.py'

GEOLOC_CACHE_FILE = 'geolocation_cache.pkl'
TRANS_CACHE_FILE = 'trans_cache.pkl'
KEY_PATH = 'key.json'

COMPANIES_LIST_FILE = 'companies_list_dd.pkl'


# 색상 코드
GREEN = '#66FF66BB'
ORANGE = '#FFCC66BB'
RED = '#FF6666BB'


DEFAULT_COMPANIES_SET_DICT = {
    'US': {
        'Amazon',
        'Amazon Web Services',
        'AT&T',
        'Cloudflare',
        'Discord',
        'Disney+',
        'Facebook',

        'Gmail',
        'Google',
        # 'Google Calendar',
        'Google Cloud',
        'Google Drive',
        # 'Google Duo',
        'Google Maps',
        'Google Meet',
        'Google Play',
        # 'Google Public DNS',
        # 'Google Workspace',

        'iCloud',
        'Instagram',
        # 'Line',
        'Microsoft 365',
        # 'Minecraft',
        'Microsoft Azure',
        'Microsoft Teams',
        'Netflix',
        'OpenAI',
        # 'Paramount+',
        'Paypal',
        # 'Roblox',
        # 'Snapchat',
        # 'Spotify',
        'Starlink',
        'T-Mobile',
        'TikTok',
        # 'Twitch',
        'Verizon',
        # 'Whatsapp',
        'X (Twitter)',
        'Yahoo',
        'Yahoo Mail',
        'Youtube',
        # 'Zoom',
    },

    'JP': {
        'Akamai',
        'Amazon',
        'Amazon Web Services',
        'App Store',
        'Apple Store',
        'Cloudflare',
        'Dropbox',
        'Facebook',

        'Gmail',
        'Google',
        # 'Google Calendar',
        'Google Cloud',
        'Google Drive',
        # 'Google Duo',
        'Google Maps',
        'Google Meet',
        'Google Play',
        # 'Google Public DNS',
        # 'Google Workspace',

        'iCloud',
        'Instagram',
        'Line',
        'Microsoft 365',
        'Microsoft Azure',
        'Microsoft Teams',
        'Netflix',
        'NTT Docomo',
        'OpenAI',
        'SoftBank',
        'TikTok',
        # 'Whatsapp',
        'X (Twitter)',
        'Yahoo',
        'Yahoo Mail',
        'Youtube',
        'Zoom',
    }
}


# # # # # # # # # # # # # # #
# 전체 세션 정보 초기화
# # # # # # # # # # # # # # #


def init_session_state():
    # 세션 정보 초기화(공용)
    if 'selected_service_name' not in st.session_state:
        st.session_state.selected_service_name = None

    if 'selected_area' not in st.session_state:
        st.session_state.selected_area = None

    if "companies_list_dict" not in st.session_state:
        st.session_state.companies_list_dict = pickle_load_cache_file(COMPANIES_LIST_FILE, dict)

    # 세션 정보 초기화(대시보드)
    if 'dashboard_auto_tab_timer' not in st.session_state:
        st.session_state.dashboard_auto_tab_timer = 30

    if 'auto_tab_timer_cache' not in st.session_state:
        st.session_state.auto_tab_timer_cache = -1

    if 'status_df_dict' not in st.session_state:
        st.session_state.status_df_dict = dict()

    if 'game_df_dict' not in st.session_state:
        st.session_state.game_df_dict = dict()

    if 'target_service_set_dict' not in st.session_state:
        st.session_state.target_service_set_dict = DEFAULT_COMPANIES_SET_DICT

    if 'status_cache' not in st.session_state:
        st.session_state.status_cache = dict()

    if 'dashboard_refresh_timer' not in st.session_state:
        st.session_state.dashboard_refresh_timer = 5

    if 'refresh_timer_cache' not in st.session_state:
        st.session_state.refresh_timer_cache = -1

    if 'num_dashboard_columns' not in st.session_state:
        st.session_state.num_dashboard_columns = 8

    if 'display_chart' not in st.session_state:
        st.session_state.display_chart = True

    # 세션 정보 초기화(뉴스)
    if "geolocations_dict" not in st.session_state:
        st.session_state.geolocations_dict = pickle_load_cache_file(GEOLOC_CACHE_FILE, dict)

    if 'trans_text_list' not in st.session_state:
        st.session_state.trans_text_list = pickle_load_cache_file(TRANS_CACHE_FILE, list)

    if "news_list" not in st.session_state:
        st.session_state.news_list = []

    if 'search_interval_timer_cache' not in st.session_state:
        st.session_state.search_interval_timer_cache = -1

    if 'search_interval_min' not in st.session_state:
        st.session_state.search_interval_min = 5


# # # # # # # # # # # # # # #
# 피클 파일 로딩 함수
# # # # # # # # # # # # # # #


def pickle_load_cache_file(filename, default_type):
    if os.path.exists(filename):
        # 캐시 파일이 있으면 불러온다.
        with open(filename, 'rb') as pickle_f:
            loaded_object = pickle.load(pickle_f)
            logging.info('피클 캐시 파일 로딩 완료 : ' + filename)
            return loaded_object

    logging.info('피클 파일 없음! : ' + filename)
    return default_type()


# # # # # # # # # # # # # # #
# 서비스의 현재 상태 받아오기
# # # # # # # # # # # # # # #


def get_service_chart_df_by_url_list(area):
    if area is None:
        logging.info(f'{area=} 크롤링 미실행!')
        return None

    logging.info(f'===== {area} 전체 크롤링 시작 =====')

    if area.upper() == 'JP':
        postfix = 'jp'
    else:
        postfix = 'com'

    categories_list = [
        get_downdetector_web.TELECOM,
        get_downdetector_web.ONLINE_SERVICE,
        get_downdetector_web.SOCIAL_MEDIA,
        get_downdetector_web.FINANCE,
        get_downdetector_web.GAMING,
    ]

    # url_list = [  # f'https://downdetector.{postfix}/',
    #             f'https://downdetector.{postfix}/telecom/',
    #             f'https://downdetector.{postfix}/online-services/',
    #             f'https://downdetector.{postfix}/social-media/',
    #             f'https://downdetector.{postfix}/finance/',
    #             f'https://downdetector.{postfix}/gaming/',
    #             ]

    df_list = []
    for category_item in categories_list:
        url_item = f'https://downdetector.{postfix}/{category_item}/'
        df_ = get_downdetector_web.get_downdetector_df(url=url_item, area=area)
        if df_ is not None:
            df_[get_downdetector_web.CATEGORY] = category_item  # 종류 구분을 첨부해준다.
            df_list.append(df_)
        time.sleep(1)  # guard time

    if len(df_list) == 0:
        logging.error(f'===== {area} 전체 크롤링 실패!!! =====')
        return None

    total_df = (pd.concat(df_list, ignore_index=True)
                .drop_duplicates(subset=get_downdetector_web.NAME, keep='first'))

    logging.info(f'===== {area} 전체 크롤링 및 df 변환 완료 =====')
    return total_df


def refresh_status_and_save_companies(area):
    # 세션상태 방어 코드
    init_session_state()

    # 상태 받아오기
    st.session_state.status_df_dict[area] = get_service_chart_df_by_url_list(area)

    if st.session_state.status_df_dict[area] is None or len(st.session_state.status_df_dict[area]) == 0:
        logging.error(f'{area} status_df 갱신 실패!')
        return

    logging.info(f'{area} status_df 갱신 후 길이: {len(st.session_state.status_df_dict[area])}')

    # 회사 목록 파일 업데이트
    new_list = list(st.session_state.status_df_dict[area][get_downdetector_web.NAME])

    # 기존 회사 목록 불러오기
    # companies_list = pickle_load_cache_file(COMPANIES_LIST_FILE, dict)

    # 신규 목록 합치기
    st.session_state.companies_list_dict[area] = list(set(st.session_state.companies_list_dict.get(area, [])
                                                          + new_list))
    st.session_state.companies_list_dict[area].sort(key=lambda x: x.lower())  # 대소문자 구분없이 abc 순으로 정렬

    # logging.info(f'{area} 회사 목록:\n{st.session_state.companies_list_dict[area][:5]} ...')
    logging.info(f'{area} Total services count: {len(st.session_state.companies_list_dict[area])}')

    # 합쳐진 리스트를 다시 파일로 저장
    with open(COMPANIES_LIST_FILE, 'wb') as f_:
        pickle.dump(st.session_state.companies_list_dict, f_)
        logging.info(f'{area} 회사 목록 업데이트 & 파일 저장 완료')


def get_service_chart_mapdf(area, service_name=None, need_map=False):
    # 세션상태 방어 코드
    init_session_state()

    # 최초 로딩 시 또는 service_name None일 경우
    if st.session_state.status_df_dict.get(area) is None or service_name is None:
        logging.info(f'최초 로딩으로 예상 - 서비스 상태 크롤링 시작 {area=} {service_name=}')
        refresh_status_and_save_companies(area)

    # 단순 크롤링 목적의 호출일 경우
    if service_name is None:
        logging.info(f'크롤링 종료 - {area=}')
        return None, None, None

    # 크롤링에 실패했을 경우
    if st.session_state.status_df_dict.get(area) is None:
        logging.error(f'서비스 상태 크롤링 실패!!! {area=} {service_name=}')
        return None, None, None

    for i, row in st.session_state.status_df_dict[area].iterrows():
        if row[get_downdetector_web.NAME].upper() == service_name.upper() \
                and row[get_downdetector_web.AREA].upper() == area.upper():  # 대소문자 구분 없이 이름/지역 일치 찾음.
            # 서비스를 찾으면 클래스, 리포트 리스트, 지도를 리턴함.
            if row[get_downdetector_web.VALUES] is None:
                logging.info(f'{area} {service_name} 의 data_values 없음!')
                data_values = None
            else:
                data_values = [int(x) for x in row[get_downdetector_web.VALUES].strip('[]').split(', ')]
            return row[get_downdetector_web.CLASS], data_values, None

    # 서비스를 못찾았을 경우
    return None, None, None


# 현재 알람이 뜬 서비스 목록을 가져오는 함수
def get_current_alarm_service_list(area):
    # 세션상태 방어 코드
    init_session_state()

    if st.session_state.status_df_dict.get(area) is None:
        logging.info('현재 알람 상태 없어서 크롤링 시작')
        get_service_chart_mapdf(area)  # 현재 값이 없을 경우 강제 크롤링 1회 수행.

    if st.session_state.status_df_dict.get(area) is None:
        # 크롤링에 실패했을 경우.
        logging.error(f'크롤링 실패하여 현재 알람 상태 확인 불가!!!')
        return []

    alarm_list = []
    for i, row in st.session_state.status_df_dict[area].iterrows():
        # 해당 지역의 Red 알람이면서 게임/금융 알람이 아닌 것.
        if row[get_downdetector_web.CLASS] == get_downdetector_web.DANGER \
                and row[get_downdetector_web.AREA].upper() == area.upper() \
                and row[get_downdetector_web.CATEGORY] != get_downdetector_web.GAMING \
                and row[get_downdetector_web.CATEGORY] != get_downdetector_web.FINANCE:
            alarm_list.append(row[get_downdetector_web.NAME])

    logging.info(f'{area}의 Red 알람 서비스 목록: {alarm_list}')

    # game들은 제외.

    return alarm_list


def init_status_df():
    logging.info('status_df_dict 초기화!')
    st.session_state.status_df_dict = dict()
    get_downdetector_web.get_downdetector_df.clear()


def get_status_color(name, status):
    if status is None or status == get_downdetector_web.SUCCESS:
        color = 'green'
        color_code = GREEN
        icon = '☻'
    elif status == get_downdetector_web.WARNING:
        color = 'orange'
        color_code = ORANGE
        icon = '☁︎'
        # st.toast(f'**{name}** 서비스 문제 발생!', icon="🔔")
    else:  # get_downdetector_web.DANGER:
        color = 'red'
        color_code = RED
        icon = '☠︎'
        # st.toast(f'**{name}** 서비스 문제 발생!', icon="🚨")

    return color, color_code, icon

