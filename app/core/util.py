import random
import string
import datetime

def generate_random_string(length: int = 6) -> str:
    """
    지정된 길이의 랜덤 문자열(대소문자 알파벳 + 숫자)을 생성합니다.
    
    Args:
        length (int): 생성할 문자열의 길이 (기본값: 6)
        
    Returns:
        str: 생성된 랜덤 문자열
    """
    # string.ascii_letters: 모든 대소문자 알파벳 (a-z, A-Z)
    # string.digits: 모든 숫자 (0-9)
    characters = string.ascii_letters + string.digits
    
    # random.choices(시퀀스, k=개수)를 사용하여 시퀀스에서 지정된 개수만큼 무작위 선택
    random_string = ''.join(random.choices(characters, k=length))
    
    return random_string


def get_current_time_string() -> str:
    """
    현재 시간을 'YYYY-MM-DD HH:MM:SS' 형식의 문자열로 반환합니다.
    """
    # 현재 날짜와 시간 가져오기
    now = datetime.datetime.now()
    
    # 원하는 형식으로 포맷팅 (strftime 사용)
    # %Y: 4자리 연도, %m: 2자리 월, %d: 2자리 일
    # %H: 24시간 형식의 시, %M: 2자리 분, %S: 2자리 초
    time_string = now.strftime("%Y-%m-%d %H:%M:%S")
    
    return str(time_string)