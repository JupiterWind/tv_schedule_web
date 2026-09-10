import requests
from bs4 import BeautifulSoup
import time
import json
from datetime import date

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}

CHANNELS = {
    "영화": ["CINETREE", "OCN Movies2", "채널액션", "채널나우", "OCN", "OCN Movies", "더 무비", "Mplex"],
    "해외드라마": ["NXT", "채널W","channel J"],
    "해외축구": ["스포티비2", "ENA SPORTS", "tvN SPORTS","OGN","JTBC SPORTS", "스포티비"],
    "기타" : ["CNN Int’l", "디스커버리 채널", "히스토리채널","NHK WORLD Premium"],
}

def fetch_today_schedule(channel_name: str):
    url = "https://search.naver.com/search.naver"
    params = {"query": f"{channel_name} 편성표"}
    res = requests.get(url, params=params, headers=HEADERS, timeout=7)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")

    root = soup.select_one(".timeline_body._timeline_root")
    if not root:
        return None  # 이 채널은 위젯이 안 뜸

    # 'today' 컬럼(col1~col7 중 어떤 것인지) 찾기
    today_col = None
    for prog in root.select(".ind_program"):
        classes = prog.get("class", [])
        if "today" in classes:
            today_col = next(c for c in classes if c.startswith("col"))
            break
    if not today_col:
        return None

    schedule = []
    for li in root.select("li.item"):
        hour_span = li.select_one(".time_box span")
        if not hour_span:
            continue
        hour = int(hour_span.get_text(strip=True).replace("시", ""))

        today_block = next(
            (p for p in li.select(".ind_program") if today_col in p.get("class", [])),
            None,
        )
        if not today_block:
            continue

        for inner in today_block.select(".inner"):
            title_tag = inner.select_one(".pr_title")
            if not title_tag or not title_tag.get("title"):
                continue  # 빈 슬롯
            minute_tag = inner.select_one(".time_min")
            minute = minute_tag.get_text(strip=True).replace("분", "") if minute_tag else "00"
            sub_tag = inner.select_one(".pr_sub_title")

            schedule.append({
                "hour": hour,
                "time": f"{hour:02d}:{minute}",
                "title": title_tag["title"],
                "sub_title": sub_tag.get_text(strip=True) if sub_tag else None,
            })

    return schedule

def build_today_schedule():
    result = {}
    for genre, channels in CHANNELS.items():
        result[genre] = []
        for ch in channels:
            try:
                full = fetch_today_schedule(ch)
                if full is None:
                    print(f"[확인 필요] {ch}: 편성표 위젯이 안 뜸")
                    continue
                filtered = [p for p in full if p["hour"] >= 18]
                if filtered:
                    result[genre].append({"channel": ch, "programs": filtered})
            except Exception as e:
                print(f"[실패] {ch}: {e}")
            time.sleep(1.5)  # 과도한 요청 방지
    return result

if __name__ == "__main__":
    data = build_today_schedule()
    with open("schedule.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("완료:", date.today())
