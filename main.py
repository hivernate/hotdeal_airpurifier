import requests
from bs4 import BeautifulSoup
import os
import time
from datetime import datetime, UTC

URL = "https://www.fmkorea.com/search.php?mid=hotdeal&category=&listStyle=webzine&search_keyword=%EB%B8%94%EB%A3%A8%EC%8A%A4%EC%B9%B4%EC%9D%B4&search_target=title_content"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"}
STORED_IDS_FILE = "post_ids.txt"
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
LOG_FILE = "log.txt"

def log(message):
    with open(LOG_FILE, "a") as f:
        f.write(f"{datetime.now(UTC)}: {message}\n")

def get_posts():
    response = requests.get(URL, headers=HEADERS)
    soup = BeautifulSoup(response.text, "html.parser")
    post_elements = soup.select("div.hotdeal_list li")
    posts = []
    for post in post_elements:
        a_tag = post.find("a")
        if a_tag:
            title = a_tag.text.strip()
            link = "https://www.fmkorea.com" + a_tag["href"]
            post_id = link.split("/")[-1]
            posts.append((post_id, title, link))
    return posts

def read_stored_ids():
    if not os.path.exists(STORED_IDS_FILE):
        return set()
    with open(STORED_IDS_FILE, "r") as f:
        return set(f.read().splitlines())

def write_ids_to_file(ids):
    with open(STORED_IDS_FILE, "w") as f:
        for id in ids:
            f.write(str(id) + "\n")

def send_telegram_notification(title, link):
    message = f"새로운 글: {title}\n{link}"
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage?chat_id={CHAT_ID}&text={message}"
    try:
        response = requests.get(url)
        if response.status_code != 200:
            log(f"텔레그램 전송 실패: {response.status_code}, {response.text}")
            print(f"텔레그램 전송 실패: {response.status_code}, {response.text}")
        else:
            log("텔레그램 전송 성공")
            print("텔레그램 전송 성공")
    except Exception as e:
        log(f"텔레그램 전송 중 에러: {e}")
        print(f"텔레그램 전송 중 에러: {e}")

while True:
    now = datetime.now(UTC)
    log(f"현재 UTC 시간: {now}")
    print(f"현재 UTC 시간: {now}")
    if now.hour == 22 and now.minute == 0:
        try:
            current_posts = get_posts()
            current_ids = {post[0] for post in current_posts}
            if not os.path.exists(STORED_IDS_FILE):
                write_ids_to_file(current_ids)
                send_telegram_notification("첫 체크 - 새 글 없음", URL)
            else:
                stored_ids = read_stored_ids()
                new_posts = [post for post in current_posts if post[0] not in stored_ids]
                if new_posts:
                    for post in new_posts:
                        send_telegram_notification(post[1], post[2])
                else:
                    send_telegram_notification("새 글 없음", URL)
                write_ids_to_file(current_ids)
            log("체크 완료")
            print("체크 완료:", datetime.now(UTC))
        except Exception as e:
            log(f"에러 발생: {e}")
            print("에러 발생:", e)
    time.sleep(60)