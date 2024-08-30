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
import reddit_bot
import twitter_bot
from deepl_translator import translate_text
from article_summarizer import summarize_articles, get_api_key



# 로깅 설정
# logging.basicConfig(level=logging.INFO)


# 세션상태 방어 코드
config.init_session_state()


# Set verbose if needed
# globals.set_debug(True)


# # # # # # # # # #
# 구글 SNS 가져오기 #
# # # # # # # # # #

def get_sns_outage_twitter(keyword_):
    ##크롤링~~~
    #logging.info('get_sns_outage_news')
    # twitter_bot.twitter_login()
    # logging.info('트위터 로그인 완료')

    tweets_text, tweets_date, tweets_link, tweets_src = twitter_bot.search_tweets_once(keyword_)

    result = {'제목': tweets_text, '언론사': tweets_src, '발행시간': tweets_date, '링크': tweets_link}
    df = pd.DataFrame(result)
    return df

def get_sns_outage_reddit(keyword_):
    ##크롤링~~~
    logging.info('get_sns_outage_reddit')
    result = reddit_bot.get_result(keyword_)
    df = pd.DataFrame(result)
    return df


def display_reddit_df(ndf, keyword_):
    # st.divider()
    kst = pytz.timezone('Asia/Seoul')
    current_time = datetime.now(kst).strftime('%Y-%m-%d %H:%M:%S')

    if ndf is None or len(ndf) == 0:
        st.write(f'✅ 검색된 SNS 없습니다. ({current_time})')
        return

    # st.write('SNS 검색 결과')

    disp_cnt = 0
    for i, row in ndf.iterrows():
        # 이미 출력했던 SNS라면 스킵한다.
        if row['제목'] in st.session_state.news_list:
            logging.info('SNS 스킵!!! - ' + row['제목'])
            continue

        # 출력한 SNS 리스트에 추가한다.
        st.session_state.news_list.append(row['제목'])
        disp_cnt += 1
 
        # title = row['제목'].replace(keyword_, f':yellow-background[{keyword_}]')
        # logging.info('keyword: ' + keyword_)
        # logging.info('before: ' + row['제목'])
        title = re.sub(keyword_, f':blue-background[{keyword_}]', row['제목'], flags=re.IGNORECASE)
        body = re.sub(keyword_, f':blue-background[{keyword_}]', row['본문'], flags=re.IGNORECASE)
        if and_keyword:
            title = re.sub(and_keyword[0], f':blue-background[{and_keyword[0]}]', title, flags=re.IGNORECASE)
            body = re.sub(and_keyword[0], f':blue-background[{and_keyword[0]}]', body, flags=re.IGNORECASE)
        # logging.info('after : ' + title)

        # 제목 번역
        korean_title = translate_eng_to_kor(row['제목'])
        
        with st.container(border=True):
            st.markdown(f'**{title}**')
            st.caption(f'{korean_title}')
            st.markdown(f'{body}')
            logging.info(f'바디내용: {body}')
            st.markdown(f'- {row["언론사"]}, {row["발행시간"]} <a href="{row["링크"]}" target="_blank">📝</a>',
                        unsafe_allow_html=True)
        # st.write(' - 언론사: ' + row['언론사'] + '  - 발행시각: ' + row['발행시간'])

    if disp_cnt > 0:
        st.write(f'✅ SNS 표시 완료 ({current_time})')
    else:
        st.write(f'✅ 신규 SNS 없습니다. ({current_time})')


def display_news_df(ndf, keyword_):
    # st.divider()
    kst = pytz.timezone('Asia/Seoul')
    current_time = datetime.now(kst).strftime('%Y-%m-%d %H:%M:%S')

    if ndf is None or len(ndf) == 0:
        st.write(f'✅ 검색된 SNS 없습니다. ({current_time})')
        return

    # st.write('SNS 검색 결과')

    disp_cnt = 0
    for i, row in ndf.iterrows():
        # 이미 출력했던 SNS라면 스킵한다.
        if row['제목'] in st.session_state.news_list:
            logging.info('SNS 스킵!!! - ' + row['제목'])
            continue

        # 출력한 SNS 리스트에 추가한다.
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
        st.write(f'✅ SNS 표시 완료 ({current_time})')
    else:
        st.write(f'✅ 신규 SNS 없습니다. ({current_time})')



def fetch_sns_reddit(keyword_, infinite_loop=False):
    with st.spinner('Reddit SNS 검색 및 번역 중...'):
        news_df_ = get_sns_outage_reddit(keyword_)
        
        # 번역 적용
        news_df_['translated_title'] = news_df_['제목'].apply(lambda x: translate_text(x, 'KO'))
        
        display_reddit_df(news_df_, keyword_)

    while infinite_loop:
        time.sleep(st.session_state.search_interval_min * 60)
        with st.spinner('Reddit SNS 검색 및 번역 중...'):
            news_df_ = get_sns_outage_reddit(keyword_)
            
            # 번역 적용
            news_df_['translated_title'] = news_df_['제목'].apply(lambda x: translate_text(x, 'KO'))
            
            display_reddit_df(news_df_, keyword_)

def fetch_sns_twitter(keyword_, infinite_loop=False):
    with st.spinner('Twitter SNS 검색 및 번역 중...'):
        news_df_ = get_sns_outage_twitter(keyword_)
        
        # 번역 적용
        news_df_['translated_title'] = news_df_['제목'].apply(lambda x: translate_text(x, 'KO'))
        
        display_news_df(news_df_, keyword_)

    while infinite_loop:
        time.sleep(st.session_state.search_interval_min * 60)
        with st.spinner('Twitter SNS 검색 및 번역 중...'):
            news_df_ = get_sns_outage_twitter(keyword_)
            
            # 번역 적용
            news_df_['translated_title'] = news_df_['제목'].apply(lambda x: translate_text(x, 'KO'))
            
            display_news_df(news_df_, keyword_)

def fetch_and_summarize_sns(keyword_, sns_type):
    with st.spinner(f'{sns_type} SNS 검색, 번역 및 요약 중...'):
        if sns_type == 'Reddit':
            news_df_ = get_sns_outage_reddit(keyword_)
        else:  # Twitter
            news_df_ = get_sns_outage_twitter(keyword_)
        
        # 번역 적용
        news_df_['translated_title'] = news_df_['제목'].apply(lambda x: translate_text(x, 'KO'))
        
        # 요약을 위한 기사 리스트 생성
        articles = [{'title': row['제목'], 'content': row['translated_title']} for _, row in news_df_.iterrows()]
        
        # OpenAI API 키 가져오기
        api_key = get_api_key("OPENAI_API_KEY")
        
        # articles가 비어있는지 확인
        if not articles:
            st.warning(f"검색된 {sns_type} 게시물이 없습니다.")
            return None, None
        
        # 요약 생성
        try:
            summaries = summarize_articles(articles, api_key)
        except Exception as e:
            st.error(f"요약 생성 중 오류 발생: {str(e)}")
            return None, None
        
        return summaries, news_df_

def display_summary(summaries: dict, sns_type: str):
    """
    요약된 내용을 표시하는 함수
    
    :param summaries: 요약된 내용을 담은 딕셔너리
    :param sns_type: SNS 유형 (예: 'Reddit', 'Twitter')
    """
    st.subheader(f"📊 {sns_type} 내용 요약")
    
    if not summaries:
        st.warning("요약할 내용이 없습니다.")
        return
    
    # 전체 요약 표시
    with st.expander("전체 요약", expanded=True):
        st.write(summaries.get("overall_summary", "전체 요약을 생성하지 못했습니다."))
    
    # 개별 게시물 요약 표시
    with st.expander("개별 게시물 요약", expanded=False):
        for title, summary in summaries.items():
            if title != "overall_summary":
                st.markdown(f"**{title}**")
                st.write(summary)
                st.divider()
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


# st.title('SNS 검색 봇')


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


search_hour = st.sidebar.number_input('최근 몇시간의 SNS를 검색할까요?', value=1, format='%d')

and_keyword = st.sidebar.multiselect("SNS 검색 추가 키워드", options=['outage', 'blackout', 'failure','not working'], default=['outage'])

st.session_state.search_interval_min = st.sidebar.number_input('새로고침 주기(분)',
                                                               value=st.session_state.search_interval_min,
                                                               format='%d')

search_button = st.sidebar.button('검색')

st.sidebar.divider()
st.sidebar.write('❓ https://downdetector.com')
try:
    twitter_bot.twitter_login()
    logging.info('트위터 로그인 완료')
except Exception as e:
    logging.info(e)
    pass

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
if search_button:
    search_button = False
    
    # 본문 화면 구성
    st.title(f"{service_code_name} SNS 분석")
    
    # Reddit과 Twitter 요약 및 데이터 가져오기
    reddit_summaries, reddit_df = fetch_and_summarize_sns(service_code_name + " " + and_keyword[0] if and_keyword else service_code_name, 'Reddit')
    twitter_summaries, twitter_df = fetch_and_summarize_sns(service_code_name + " " + and_keyword[0] if and_keyword else service_code_name, 'Twitter')
    


    # SNS 게시물 섹션
    st.header("SNS 게시물")
    col3, col4 = st.columns(2)

    with col3:
        st.subheader("Reddit 게시물")
        if reddit_df is not None:
            st.session_state.news_list = []  # SNS 세션 클리어
            display_news_df(reddit_df, service_code_name)
        else:
            st.write("Reddit 게시물을 가져오지 못했습니다.")
    
    with col4:
        st.subheader("Twitter 게시물")
        if twitter_df is not None:
            st.session_state.news_list = []  # SNS 세션 클리어
            display_news_df(twitter_df, service_code_name)
        else:
            st.write("Twitter 게시물을 가져오지 못했습니다.")

    # reddit_df, twitter_df 받아와서 번역

    # 요약 섹션
    st.header("SNS 내용 요약")
    col1, col2 = st.columns(2)
    
    with col1:
        if reddit_summaries:
            display_summary(reddit_summaries, 'Reddit')
    
    with col2:
        if twitter_summaries:
            display_summary(twitter_summaries, 'Twitter')
    

    

# # 주기적으로 페이지를 새로고침한다.
# # 사이드바에 타이머 표기
# st.sidebar.divider()

# # 타이머를 표시할 위치 예약
# timer_placeholder = st.sidebar.empty()

# # 카운트다운 초 계산
# if service_code_name:
#     if st.session_state.search_interval_timer_cache <= 0:
#         st.session_state.search_interval_timer_cache = st.session_state.search_interval_min * 60

#     # 타이머 실행
#     while st.session_state.search_interval_timer_cache >= 0:
#         # 타이머 갱신
#         timer_placeholder.markdown(f"⏳ 재검색까지 {st.session_state.search_interval_timer_cache}초")

#         # 1초 대기
#         time.sleep(1)

#         # 타이머 감소
#         st.session_state.search_interval_timer_cache -= 1

#     # 타이머 완료 메시지
#     timer_placeholder.markdown("⏰ 카운트다운 완료! 서비스 상태 재검색!")

#     logging.info('재검색!!!')
#     config.init_status_df()  # 서비스 상태 초기화
#     st.rerun()
