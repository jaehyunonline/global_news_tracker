import praw
from datetime import datetime, timedelta

# Reddit API에 접근하기 위한 설정
reddit = praw.Reddit(client_id='ca9Fu2aX5UjAuYXvYSLcjQ',
                     client_secret='bu6glVNKfUTcM9-QdacPKyIGnLguJg',
                     user_agent='redditcrawler')



MAX_RESULT_CNT = 5
MAX_BODY_CHAR_CNT = 120




result = {}
current_time = datetime.utcnow()
one_month_ago = current_time - timedelta(days=30)


def extract_text(text, keyword, context_length = MAX_BODY_CHAR_CNT):
    # 키워드 위치 찾기
    keyword_position = text.find(keyword)
    
    if keyword_position == -1:
        return "Keyword not found in the text."

    # 앞뒤로 context_length만큼 잘라내기
    start = max(keyword_position - context_length, 0)
    end = min(keyword_position + len(keyword) + context_length, len(text))

    # 잘라낸 텍스트 반환
    return text[start:end]


def get_result(keyword):
    # 'all' 서브레딧에서 특정 키워드로 가장 최근 게시물 검색
    subreddit = reddit.subreddit('all')
    recent_posts = subreddit.search(
            keyword, 
            sort='relevance', 
            time_filter='month', 
            limit=30
    )

    filtered_posts = [
    post for post in recent_posts 
    if datetime.utcfromtimestamp(post.created_utc) >= one_month_ago
    ]

    filtered_posts.sort(key=lambda x: x.created_utc, reverse=True)


    title = []
    body = []
    source = []
    issued_time = []
    url = []

    print('\n')

    idx = 0

    for post in filtered_posts:
        idx += 1
        # Unix 타임스탬프를 UTC datetime 객체로 변환
        created_time_utc = datetime.utcfromtimestamp(post.created_utc)
        # KST (UTC+9) 시간대로 변환
        created_time_kst = created_time_utc + timedelta(hours=9)
        # datetime 객체를 사람이 읽을 수 있는 형식으로 변환
        formatted_time = created_time_kst.strftime('%Y-%m-%d %H:%M:%S KST')
        
        # 게시물 내용 (selftext) 가져오기
        post_content = post.selftext if post.selftext else "본문 없음"

        #print(f'{post_content}\n')



        title.append(post.title)
        body.append(extract_text(post_content, keyword))
        source.append('reddit')
        issued_time.append(formatted_time)
        url.append(post.url)

        print (f'{post.title} {formatted_time} {post.url}')
        # print (f'{extract_text(post_content, keyword)}\n')
        print (f'{post_content}\n')

        #result = {'제목': [post.title], '언론사': ['reddit'], '발행시간': [formatted_time], '링크': [post.url]}

        if idx == MAX_RESULT_CNT:
            break
    
    result = {'제목': title, '본문' : body, '언론사': source, '발행시간': issued_time, '링크': url}

    # print(result)

    return result



# result = {'제목': 'test tweets', '언론사': 'twitter', '발행시간': '2024-08-29 14:45 +09:00', '링크': 'https://x.com/login'}
get_result('Youtube')

