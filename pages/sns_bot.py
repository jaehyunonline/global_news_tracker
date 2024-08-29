import logging
import requests
import pandas as pd
import pickle
import os
import time
from geopy.geocoders import Nominatim
import feedparser
from datetime import datetime, timedelta
import pytz
import re
import streamlit as st
from google.cloud import translate_v2 as translate  # pip install google-cloud-translate==2.0.1
from google.oauth2 import service_account
import config


# 로깅 설정
# logging.basicConfig(level=logging.INFO)


# 세션상태 방어 코드
config.init_session_state()


# Set verbose if needed
# globals.set_debug(True)


# # # # # # # # # #
# 구글 뉴스 가져오기 #
# # # # # # # # # #


def get_google_outage_news(keyword_):
    query = keyword_
    if and_keyword:
        query += ' ' + and_keyword[0]

    url = f"https://news.google.com/rss/search?q={query}+when:{search_hour}h"
    url += f'&hl=en-US&gl=US&ceid=US:en'
    url = url.replace(' ', '%20')

    title_list = []
    source_list = []
    pubtime_list = []
    link_list = []

    try:
        res = requests.get(url)  # , verify=False)
        logging.info('원본 링크: ' + url)

        if res.status_code == 200:
            datas = feedparser.parse(res.text).entries
            for data in datas:
                title = data.title
                logging.info('구글뉴스제목(원본): ' + title)

                minus_index = title.rindex(' - ')
                title = title[:minus_index].strip()

                # 기사 제목에 검색 키워드가 없으면 넘긴다.
                if keyword_.lower() not in title.lower():
                    continue

                title_list.append(title)
                source_list.append(data.source.title)
                link_list.append(data.link)

                pubtime = datetime.strptime(data.published, "%a, %d %b %Y %H:%M:%S %Z")
                # GMT+9 (Asia/Seoul)으로 변경
                gmt_plus_9 = pytz.FixedOffset(540)  # 9 hours * 60 minutes = 540 minutes
                pubtime = pubtime.replace(tzinfo=pytz.utc).astimezone(gmt_plus_9)

                pubtime_str = pubtime.strftime('%Y-%m-%d %H:%M:%S')
                pubtime_list.append(pubtime_str)

        else:
            logging.error("Google 뉴스 수집 실패! Error Code: " + str(res.status_code))
            logging.error(str(res))
            return None

    except Exception as e:
        logging.error(e)
        logging.error("Google 뉴스 RSS 피드 조회 오류 발생!")
        return None

    # 결과를 dict 형태로 저장
    result = {'제목': title_list, '언론사': source_list, '발행시간': pubtime_list, '링크': link_list}

    df = pd.DataFrame(result)
    return df


def display_news_df(ndf, keyword_):
    # st.divider()
    kst = pytz.timezone('Asia/Seoul')
    current_time = datetime.now(kst).strftime('%Y-%m-%d %H:%M:%S')

    if ndf is None or len(ndf) == 0:
        st.write(f'✅ 검색된 뉴스 없습니다. ({current_time})')
        return

    # st.write('뉴스 검색 결과')

    disp_cnt = 0
    for i, row in ndf.iterrows():
        # 이미 출력했던 뉴스라면 스킵한다.
        if row['제목'] in st.session_state.news_list:
            logging.info('뉴스 스킵!!! - ' + row['제목'])
            continue

        # 출력한 뉴스 리스트에 추가한다.
        st.session_state.news_list.append(row['제목'])
        disp_cnt += 1

        # title = row['제목'].replace(keyword_, f':yellow-background[{keyword_}]')
        # logging.info('keyword: ' + keyword_)
        # logging.info('before: ' + row['제목'])
        title = re.sub(keyword_, f':blue-background[{keyword_}]', row['제목'], flags=re.IGNORECASE)
        if and_keyword:
            title = re.sub(and_keyword[0], f':blue-background[{and_keyword[0]}]', title, flags=re.IGNORECASE)
        # logging.info('after : ' + title)

        # 제목 번역
        korean_title = translate_eng_to_kor(row['제목'])

        with st.container(border=True):
            st.markdown(f'**{title}**')
            st.caption(f'{korean_title}')
            st.markdown(f'- {row["언론사"]}, {row["발행시간"]} <a href="{row["링크"]}" target="_blank">📝</a>',
                        unsafe_allow_html=True)
        # st.write(' - 언론사: ' + row['언론사'] + '  - 발행시각: ' + row['발행시간'])

    if disp_cnt > 0:
        st.write(f'✅ 뉴스 표시 완료 ({current_time})')
    else:
        st.write(f'✅ 신규 뉴스 없습니다. ({current_time})')


def fetch_news(keyword_, infinite_loop=False):
    with st.spinner('뉴스 검색중...'):
        news_df_ = get_google_outage_news(keyword_)
        # st.write(news_df_)
        display_news_df(news_df_, keyword_)

    while infinite_loop:
        time.sleep(st.session_state.search_interval_min * 60)
        with st.spinner('뉴스 검색중...'):
            news_df_ = get_google_outage_news(keyword_)
            # st.write(news_df_)
            display_news_df(news_df_, keyword_)


# # # # # # # # # # # # # # #
# 영어 번역
# # # # # # # # # # # # # # #


def translate_eng_to_kor(text):
    # 캐시를 먼저 뒤져본다.
    cache_text = load_trans_cache(text)
    if cache_text:
        logging.info('trans cache hit! - ' + text + ' : ' + cache_text)
        return cache_text  # 캐시힛!

    # 캐시에 없으면 구글 api로 번역을 한다.
    if not os.path.exists(config.KEY_PATH):
        return ''

    credential_trans = service_account.Credentials.from_service_account_file(config.KEY_PATH)
    translate_client = translate.Client(credentials=credential_trans)

    result = translate_client.translate(text, target_language='ko')
    # print(names)
    translated_text = result['translatedText'].replace('&amp;', '&')

    # 캐시에 저장한다.
    save_trans_cache(text, translated_text)

    return translated_text


def save_trans_cache(eng_text, kor_text):
    if len(st.session_state.trans_text_list) >= 100:  # 100개 이하로 유지한다.
        st.session_state.trans_text_list.pop(0)

    st.session_state.trans_text_list.append((eng_text, kor_text))  # 번역 튜플을 리스트에 삽입
    # 캐시 파일에 저장
    with open(config.TRANS_CACHE_FILE, 'wb') as f_:
        pickle.dump(st.session_state.trans_text_list, f_)
        logging.info('번역 캐시 파일 업데이트 완료')


def load_trans_cache(eng_text):
    for e_txt, k_txt in st.session_state.trans_text_list:
        if eng_text == e_txt:
            return k_txt  # 캐시 힛
    return None


# # # # # # # # # # # # # # #
# 시간대 변환
# # # # # # # # # # # # # # #


def get_korean_time():
    # 차트 시간대 보정
    now = datetime.now() - timedelta(minutes=5)
    before_10unit_minute = int(now.minute / 10) * 10
    new_time = now.replace(minute=before_10unit_minute, second=0, microsecond=0)

    # 4시간 간격으로 이전 여섯개의 시각을 저장할 리스트
    previous_times = [new_time]

    # 4시간 간격으로 이전 시간들을 계산
    for i in range(1, 7):
        previous_time = new_time - timedelta(hours=4 * i)
        previous_times.append(previous_time)

    # 결과 출력
    logging.info(str(previous_times))

    previous_times.reverse()
    return previous_times


# # # # # # # # # #
# 위경도 받아오기
# # # # # # # # # #


def save_loc_cache(loc, lat, lon):
    st.session_state.geolocations_dict[loc] = {'lat': lat, 'lon': lon}
    # 새로운 위경도 정보를 캐시 파일에 저장
    with open(config.GEOLOC_CACHE_FILE, 'wb') as f_:
        pickle.dump(st.session_state.geolocations_dict, f_)
        logging.info('위경도 캐시 파일 업데이트 완료')


def load_loc_cache(loc):
    return st.session_state.geolocations_dict.get(loc)


def get_geo_location(map_df_):
    geolocator = Nominatim(user_agent="jason")
    map_df_['lat'] = None
    map_df_['lon'] = None
    map_df_['color'] = '#ff000077'  # 빨강, 살짝 투명.

    for i, row in map_df_.iterrows():
        # 세션 캐시를 먼저 살펴본다.
        cache = load_loc_cache(row['Location'])
        if cache:
            logging.info('geo cache hit! - ' + row['Location'])
            map_df_.loc[i, 'lat'] = cache['lat']
            map_df_.loc[i, 'lon'] = cache['lon']
            continue

        # 세션 캐시에 없으면 위경도 api를 써서 불러온다.
        geo = geolocator.geocode(row['Location'])

        if geo:
            map_df_.loc[i, 'lat'] = geo.latitude
            map_df_.loc[i, 'lon'] = geo.longitude
            save_loc_cache(row['Location'], geo.latitude, geo.longitude)
        else:
            # retry
            geo = geolocator.geocode(row['Location'].split(',')[0])

            if geo:
                map_df_.loc[i, 'lat'] = geo.latitude
                map_df_.loc[i, 'lon'] = geo.longitude
                save_loc_cache(row['Location'], geo.latitude, geo.longitude)
            else:
                # retry까지 실패할 경우.
                logging.error('Geo ERROR!!! :' + str(geo))

        time.sleep(0.2)
    return map_df_


def get_multiple(values_sr):
    max_report = values_sr.max()
    multiple_ = int(500000 / max_report)
    logging.info(f'{max_report=} {multiple_=}')
    return multiple_


# # # # # # # # # #
# 웹 페이지 구성
# # # # # # # # # #


# st.title('뉴스 검색 봇')


# # # # # # # # # # # # # # #
# 사이드바
# # # # # # # # # # # # # # #


# st.sidebar.header('Global Service News Tracker')

total_services_list = []
for area in st.session_state.companies_list_dict:
    total_services_list += st.session_state.companies_list_dict[area]

total_services_list = list(set(total_services_list))
total_services_list.sort(key=lambda x: x.lower())

if 'selected_service_name' in st.session_state and st.session_state.selected_service_name is not None:
    if st.session_state.selected_service_name not in total_services_list:
        total_services_list.append(st.session_state.selected_service_name)
    item_index = total_services_list.index(st.session_state.selected_service_name)
else:
    item_index = None

service_code_name = st.sidebar.selectbox(
    "검색을 원하는 서비스는?",
    total_services_list,
    index=item_index,
    placeholder="서비스 이름 선택...",
)


search_hour = st.sidebar.number_input('최근 몇시간의 뉴스를 검색할까요?', value=1, format='%d')

and_keyword = st.sidebar.multiselect("뉴스 검색 추가 키워드", options=['outage', 'blackout', 'failure'], default=['outage'])

st.session_state.search_interval_min = st.sidebar.number_input('새로고침 주기(분)',
                                                               value=st.session_state.search_interval_min,
                                                               format='%d')

st.sidebar.divider()
st.sidebar.write('❓ https://downdetector.com')


if not os.path.exists(config.KEY_PATH):
    uploaded_file = st.sidebar.file_uploader('API Key File', type=['json'], accept_multiple_files=False)
else:
    logging.info('API key 파일은 로컬 저장된 파일 사용합니다.')
    uploaded_file = None


# key json 파일 업로드 처리
if uploaded_file is not None:
    # 파일을 로컬에 저장
    with open(config.KEY_PATH, "wb") as file:
        file.write(uploaded_file.getbuffer())

    st.toast(f"API key file has been saved successfully!")


# # # # # # # # # # # # # # #
# 메인 화면
# # # # # # # # # # # # # # #


# 서비스 선택시 처리
if service_code_name:
    # 본문 화면 구성
    title_placeholder = st.empty()
    col1, col2 = st.columns(2)

    # 빈 공간을 생성하여 나중에 내용을 업데이트할 준비
    col1_placeholder = col1.empty()
    col2_placeholder = col2.empty()

    with st.spinner('서비스 상태 조회중...'):
        status, report_list, _ = config.get_service_chart_mapdf(area=st.session_state.selected_area,
                                                                service_name=service_code_name)

        if status is None:
            with title_placeholder.container():
                st.subheader(f'**{service_code_name}**')
        else:
            # 상태
            color, color_code, icon = config.get_status_color(service_code_name, status)

            with title_placeholder.container():
                st.subheader(f'**{service_code_name}**  :{color}[{icon}]')

    # 컬럼2 - 차트
    with col2_placeholder.container():
        if report_list is not None:
            st.write('📈 Live Report Chart (Last 24 hours)')

            with st.container():
                chart_data = pd.DataFrame(report_list, columns=["Report Count"])
                st.line_chart(chart_data, color=color_code)
        else:
            st.write('')  # no report chart

    # 컬럼1 - 뉴스
    with col1_placeholder.container():
        st.session_state.news_list = []  # 뉴스 세션 클리어
        st.write('📰 News List')
        fetch_news(service_code_name)


# 주기적으로 페이지를 새로고침한다.
# 사이드바에 타이머 표기
st.sidebar.divider()

# 타이머를 표시할 위치 예약
timer_placeholder = st.sidebar.empty()

# 카운트다운 초 계산
if service_code_name:
    if st.session_state.search_interval_timer_cache <= 0:
        st.session_state.search_interval_timer_cache = st.session_state.search_interval_min * 60

    # 타이머 실행
    while st.session_state.search_interval_timer_cache >= 0:
        # 타이머 갱신
        timer_placeholder.markdown(f"⏳ 재검색까지 {st.session_state.search_interval_timer_cache}초")

        # 1초 대기
        time.sleep(1)

        # 타이머 감소
        st.session_state.search_interval_timer_cache -= 1

    # 타이머 완료 메시지
    timer_placeholder.markdown("⏰ 카운트다운 완료! 서비스 상태 재검색!")

    logging.info('재검색!!!')
    config.init_status_df()  # 서비스 상태 초기화
    st.rerun()
