# 파일명: deepl_translator.py

import requests
import os
from getpass import getpass

def get_api_key(key_name, file_path=None):
    """
    API 키를 가져오는 함수. 다음 순서로 API 키를 찾습니다:
    1. 환경 변수
    2. 지정된 파일
    3. 사용자 입력
    
    :param key_name: API 키의 이름 (예: 'DEEPL_API_KEY')
    :param file_path: API 키가 저장된 파일 경로 (선택사항)
    :return: API 키
    """
    # 1. 환경 변수에서 확인
    api_key = os.getenv(key_name)
    if api_key:
        return api_key
    
    # 2. 파일에서 확인
    if file_path:
        try:
            with open(file_path, 'r') as file:
                api_key = file.read().strip()
            if api_key:
                return api_key
        except FileNotFoundError:
            print(f"파일을 찾을 수 없습니다: {file_path}")
        except IOError:
            print(f"파일을 읽는 중 오류가 발생했습니다: {file_path}")
    
    # 3. 사용자 입력 요청
    api_key = getpass(f"{key_name}를 입력하세요: ")
    
    # API 키 저장 여부 확인
    save_option = input("API 키를 파일에 저장하시겠습니까? (y/n): ").lower()
    if save_option == 'y':
        save_path = file_path or ".deepl_api_key"
        try:
            with open(save_path, 'w') as file:
                file.write(api_key)
            print(f"API 키가 {save_path}에 저장되었습니다.")
        except IOError:
            print(f"파일에 API 키를 저장하는 중 오류가 발생했습니다: {save_path}")
    
    return api_key

def translate_text(text, target_language, api_key=None, key_file=".deepl_api_key"):
    """
    DeepL API를 사용하여 텍스트를 번역하는 함수
    
    :param text: 번역할 텍스트
    :param target_language: 대상 언어 코드 (예: 'KO', 'EN', 'JA' 등)
    :param api_key: DeepL API 키 (선택사항)
    :param key_file: API 키가 저장된 파일 경로 (기본값: '.deepl_api_key')
    :return: 번역된 텍스트
    """
    if not api_key:
        api_key = get_api_key("DEEPL_API_KEY", key_file)
    
    if not api_key:
        raise ValueError("API 키를 가져올 수 없습니다.")

    url = "https://api-free.deepl.com/v2/translate"
    
    payload = {
        "auth_key": api_key,
        "text": text,
        "target_lang": target_language
    }
    
    try:
        response = requests.post(url, data=payload)
        response.raise_for_status()  # HTTP 오류 발생 시 예외를 발생시킵니다.
        
        result = response.json()
        return result["translations"][0]["text"]
    except requests.exceptions.RequestException as e:
        return f"번역 중 오류가 발생했습니다: {str(e)}"

if __name__ == "__main__":
    print("이 파일을 직접 실행하면 이 메시지가 출력됩니다.")
    print("다른 파일에서 import하여 사용할 때는 이 부분이 실행되지 않습니다.")