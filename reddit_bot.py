import praw
from datetime import datetime, timedelta

# Reddit API에 접근하기 위한 설정
reddit = praw.Reddit(client_id='ca9Fu2aX5UjAuYXvYSLcjQ',
                     client_secret='bu6glVNKfUTcM9-QdacPKyIGnLguJg',
                     user_agent='redditcrawler')



'''
# 검색할 키워드 입력
keyword = 'earthquake'

# 'all' 서브레딧에서 특정 키워드로 가장 최근 게시물 검색
subreddit = reddit.subreddit('all')
recent_posts = subreddit.search(keyword, sort='new', limit=1)

# 최근 게시물 가져오기
for post in recent_posts:
    # Unix 타임스탬프를 UTC datetime 객체로 변환
    created_time_utc = datetime.utcfromtimestamp(post.created_utc)
    # KST (UTC+9) 시간대로 변환
    created_time_kst = created_time_utc + timedelta(hours=9)
    # datetime 객체를 사람이 읽을 수 있는 형식으로 변환
    formatted_time = created_time_kst.strftime('%Y-%m-%d %H:%M:%S KST')
    
    # 게시물 내용 (selftext) 가져오기
    post_content = post.selftext if post.selftext else "No content available"

    # 결과 출력
    print(f"Title: {post.title}")
    print(f"URL: {post.url}")
    print(f"Created at: {formatted_time}")
    print(f"Content: {post_content[:1000]}...")  # 내용이 길 경우 일부만 출력)
'''

result = {}



def get_result(keyword):
    # 'all' 서브레딧에서 특정 키워드로 가장 최근 게시물 검색
    subreddit = reddit.subreddit('all')
    recent_posts = subreddit.search(keyword, sort='new', limit=1)

    for post in recent_posts:
        # Unix 타임스탬프를 UTC datetime 객체로 변환
        created_time_utc = datetime.utcfromtimestamp(post.created_utc)
        # KST (UTC+9) 시간대로 변환
        created_time_kst = created_time_utc + timedelta(hours=9)
        # datetime 객체를 사람이 읽을 수 있는 형식으로 변환
        formatted_time = created_time_kst.strftime('%Y-%m-%d %H:%M:%S KST')
        
        # 게시물 내용 (selftext) 가져오기
        post_content = post.selftext if post.selftext else "No content available"
        result = {'제목': [post.title], '언론사': ['reddit'], '발행시간': [formatted_time], '링크': [post.url]}
    
    print(result)

    return result



# result = {'제목': 'test tweets', '언론사': 'twitter', '발행시간': '2024-08-29 14:45 +09:00', '링크': 'https://x.com/login'}


