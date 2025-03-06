import requests
from bs4 import BeautifulSoup
import os
import time

# 설정값
URL = "https://www.fmkorea.com/search.php?mid=hotdeal&category=&listStyle=webzine&search_keyword=%EB%B8%94%EB%A3%A8%EC%8A%A4%EC%B9%B4%EC%9D%B4&search_target=title_content"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"}
STORED_IDS_FILE = "post_ids.txt"
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")  # Heroku에서 설정
CHAT_ID = os.getenv("CHAT_ID")  # Heroku에서 설정

# 페이지에서 글 목록 가져오기
def get_posts():
    response = requests.get(URL, headers=HEADERS)
    soup = BeautifulSoup(response.text, "html.parser")
    # FMKorea 페이지 구조에 맞게 조정 (개발자 도구로 확인 필요)
    post_elements = soup.select("div.hotdeal_list li")  # 예시 선택자
    posts = []
    for post in post_elements:
        a_tag = post.find("a")
        if a_tag:
            title = a_tag.text.strip()
            link = "https://www.fmkorea.com" + a_tag["href"]
            post_id = link.split("/")[-1]
            posts.append((post_id, title, link))
    return posts

# 저장된 글 ID 읽기
def read_stored_ids():
    if not os.path.exists(STORED_IDS_FILE):
        return set()
    with open(STORED_IDS_FILE, "r") as f:
        return set(f.read().splitlines())

# 글 ID 저장
def write_ids_to_file(ids):
    with open(STORED_IDS_FILE, "w") as f:
        for id in ids:
            f.write(str(id) + "\n")

# 텔레그램 알림 전송
def send_telegram_notification(title, link):
    message = f"새로운 글: {title}\n{link}"
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage?chat_id={CHAT_ID}&text={message}"
    requests.get(url)

# 메인 로직 (무한 루프)
while True:
    try:
        current_posts = get_posts()
        current_ids = {post[0] for post in current_posts}
        if not os.path.exists(STORED_IDS_FILE):
            write_ids_to_file(current_ids)
        else:
            stored_ids = read_stored_ids()
            new_posts = [post for post in current_posts if post[0] not in stored_ids]
            for post in new_posts:
                send_telegram_notification(post[1], post[2])
            write_ids_to_file(current_ids)
        print("체크 완료, 15분 대기 중...")
        time.sleep(900)  # 15분 대기
    except Exception as e:
        print("에러 발생:", e)
        time.sleep(60)  # 에러 시 1분 대기 후 재시도