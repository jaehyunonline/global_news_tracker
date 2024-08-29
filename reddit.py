import praw

# Reddit API에 접근하기 위한 설정
reddit = praw.Reddit(client_id='ca9Fu2aX5UjAuYXvYSLcjQ',
                     client_secret='bu6glVNKfUTcM9-QdacPKyIGnLguJg',
                     user_agent='redditcrawler')

# 서브레딧에서 인기 게시물 가져오기
subreddit = reddit.subreddit('all')
top_posts = subreddit.top(limit=10)  # 상위 10개의 인기 게시물

for post in top_posts:
    print(f"Title: {post.title}")
    print(f"Score: {post.score}")
    print(f"URL: {post.url}")
    print("--------")