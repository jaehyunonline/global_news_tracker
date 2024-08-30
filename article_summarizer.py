# 파일명: article_summarizer.py

import os
import openai
from typing import List, Dict

def get_api_key(key_name: str, file_path: str = ".openai_api_key") -> str:
    """OpenAI API 키를 가져오는 함수"""
    api_key = os.getenv(key_name)
    if api_key:
        return api_key
    
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            return file.read().strip()
    
    api_key = input(f"{key_name}를 입력하세요: ")
    save_option = input("API 키를 파일에 저장하시겠습니까? (y/n): ").lower()
    if save_option == 'y':
        with open(file_path, 'w') as file:
            file.write(api_key)
        print(f"API 키가 {file_path}에 저장되었습니다.")
    
    return api_key

def summarize_articles(articles: List[Dict[str, str]], api_key: str = None) -> Dict[str, str]:
    """
    여러 기사를 요약하는 함수
    
    :param articles: 기사 목록. 각 기사는 {'title': '기사 제목', 'content': '기사 내용'} 형식의 딕셔너리
    :param api_key: OpenAI API 키 (선택사항)
    :return: 요약 결과를 담은 딕셔너리
    """
    if not api_key:
        api_key = get_api_key("OPENAI_API_KEY")
    
    openai.api_key = api_key

    summaries = {}
    for article in articles:
        prompt = f"""
다음 기사를 요약해주세요:

제목: {article['title']}

내용: {article['content']}

다음 형식으로 요약해주세요:
핵심 요약: (50단어 이내)
주요 포인트:
- 포인트 1
- 포인트 2
- 포인트 3
"""

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes articles."},
                {"role": "user", "content": prompt}
            ]
        )

        summaries[article['title']] = response.choices[0].message['content']

    # 전체 요약 생성
    all_titles = "\n".join([f"- {title}" for title in summaries.keys()])
    overall_prompt = f"""
다음은 여러 기사의 제목 목록입니다:

{all_titles}

이 기사들의 개별 요약을 검토했다고 가정하고, 전체 기사들의 공통 주제와 트렌드에 대한 종합적인 요약을 100단어 이내로 제공해주세요.
"""

    overall_response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that provides overall summaries of multiple articles."},
            {"role": "user", "content": overall_prompt}
        ]
    )

    summaries["overall_summary"] = overall_response.choices[0].message['content']

    return summaries

if __name__ == "__main__":
    # 사용 예시
    articles = [
        {
            "title": "AI의 미래: 기회와 도전",
            "content": "AI 기술의 급속한 발전은 우리 사회에 큰 변화를 가져오고 있습니다. 한편으로는 생산성 향상과 새로운 일자리 창출의 기회를 제공하지만, 다른 한편으로는 기존 일자리의 대체와 윤리적 문제 등의 도전도 제기하고 있습니다. ..."
        },
        {
            "title": "기후 변화와 신재생 에너지",
            "content": "기후 변화 대응을 위한 신재생 에너지의 중요성이 날로 커지고 있습니다. 태양광, 풍력 등의 기술 발전으로 비용이 낮아지면서 화석 연료를 대체할 수 있는 현실적인 대안으로 부상하고 있습니다. 그러나 여전히 저장과 안정성 문제 등의 과제가 남아있습니다. ..."
        }
    ]

    summaries = summarize_articles(articles)
    
    for title, summary in summaries.items():
        print(f"\n{title}\n{'-'*len(title)}\n{summary}\n")