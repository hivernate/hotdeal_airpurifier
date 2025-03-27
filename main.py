import requests
from bs4 import BeautifulSoup
import os
import time
from datetime import datetime, UTC

URL = "https://www.fmkorea.com/search.php?mid=hotdeal&category=&listStyle=webzine&search_keyword=%EB%B8%94%EB%A3%A8%EC%8A%A4%EC%B9%B4%EC%9D%B4&search_target=title_content"
HEADERS = {
    "User-Agent":
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
}
STORED_IDS_FILE = "post_ids.txt"
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
LOG_FILE = "log.txt"


def log(message):
    with open(LOG_FILE, "a") as f:
        f.write(f"{datetime.now(UTC)}: {message}\n")


def get_posts():
    for attempt in range(3):
        try:
            response = requests.get(URL, headers=HEADERS, timeout=10)
            response.raise_for_status()
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
        except Exception as e:
            log(f"get_posts 재시도 {attempt + 1}/3: {e}")
            time.sleep(5)
    log("get_posts 완전 실패")
    return []


def read_stored_ids():
    if not os.path.exists(STORED_IDS_FILE):
        return set()
    try:
        with open(STORED_IDS_FILE, "r") as f:
            return set(f.read().splitlines())
    except Exception as e:
        log(f"read_stored_ids 에러: {e}")
        return set()


def write_ids_to_file(ids):
    try:
        with open(STORED_IDS_FILE, "w") as f:
            for id in ids:
                f.write(str(id) + "\n")
    except Exception as e:
        log(f"write_ids_to_file 에러: {e}")


def send_telegram_notification(title, link):
    message = f"새로운 글: {title}\n{link}"
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage?chat_id={CHAT_ID}&text={message}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            log(f"텔레그램 전송 실패: {response.status_code}, {response.text}")
            print(f"텔레그램 전송 실패: {response.status_code}, {response.text}")
        else:
            log("텔레그램 전송 성공")
            print("텔레그램 전송 성공")
    except Exception as e:
        log(f"텔레그램 전송 중 에러: {e}")
        print(f"텔레그램 전송 중 에러: {e}")


def seconds_until_7am_kst():
    now = datetime.now(UTC)
    target = now.replace(hour=22, minute=0, second=0,
                         microsecond=0)  # UTC 22시 = KST 7시
    if now > target:
        target = target.replace(day=target.day + 1)  # 다음 날 22시
    seconds = (target - now).total_seconds()
    return seconds


try:
    while True:
        sleep_seconds = seconds_until_7am_kst()
        log(f"다음 KST 7시까지 대기: {sleep_seconds}초")
        print(f"다음 KST 7시까지 대기: {sleep_seconds}초")
        time.sleep(sleep_seconds)

        now = datetime.now(UTC)
        log(f"KST 7시 체크 시작: {now}")
        print(f"KST 7시 체크 시작: {now}")
        try:
            current_posts = get_posts()
            current_ids = {post[0] for post in current_posts}
            if not os.path.exists(STORED_IDS_FILE):
                write_ids_to_file(current_ids)
                send_telegram_notification("첫 체크 - 새 글 없음", URL)
            else:
                stored_ids = read_stored_ids()
                new_posts = [
                    post for post in current_posts if post[0] not in stored_ids
                ]
                if new_posts:
                    for post in new_posts:
                        send_telegram_notification(post[1], post[2])
                else:
                    send_telegram_notification("새 글 없음", URL)
                write_ids_to_file(current_ids)
            log("체크 완료")
            print("체크 완료:", datetime.now(UTC))
        except Exception as e:
            log(f"체크 중 에러: {e}")
            print("체크 중 에러:", e)
except Exception as e:
    log(f"루프 종료: {e}")
    print("루프 종료:", e)
