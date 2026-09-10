import requests
import time
import json
from datetime import date

BASE_URL = "https://www.lguplus.com/uhdc/fo/prdv/chnlgid/v1/tv-schedule-list"

HEADERS = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "referer": "https://www.lguplus.com/iptv/channel-guide",
    "x-menu-url": "/iptv/channel-guide",
    "user-agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "x-datadog-origin": "rum",
    "x-menu-url":"/iptv/channel-guide",
}

# 장르: {채널명: (채널ID, 장르코드, 채널번호)}
CHANNELS = {
    "해외축구": {
        "스포티비2": ("638", "01", "108"),
        "ENA SPORTS": ("692", "01", "112"),
        "tvN SPORTS": ("778", "01", "116"),
        "OGN": ("681", "01", "119"),
        "BallTV": ("659", "01", "126"),
        "JTBC SPORTS": ("795", "01", "102"),
        "스포티비": ("667", "01", "107"),
    },
    "해외드라마": {
        "NXT": ("744", "02", "141"),
        "채널J": ("656", "02", "144"),
        "채널W": ("161", "02", "146"),
    },
    "영화": {
        "CINETREE": ("574", "02", "50"),
        "OCN Movies2": ("685", "02", "51"),
        "채널액션": ("593", "02", "54"),
        "채널나우": ("654", "02", "140"),
        "OCN": ("684", "02", "44"),
        "OCN Movies": ("686", "02", "45"),
        "엠플렉스": ("756", "02", "48"),
        "더 무비": ("724", "02", "49"),
    },
    "기타": {
        "CNN International":("729","03","200"),
        "디스커버리":("610","04","194"),
        "히스토리":("664","04","218"),
        "NHK World Premium":("633","03","209"),
    }
}


def fetch_today_schedule(channel_id: str, genre_code: str):
    today = date.today().strftime("%Y%m%d")
    params = {
        "brdCntrTvChnlBrdDt": today,
        "urcBrdCntrTvChnlId": channel_id,
        "urcBrdCntrTvChnlGnreCd": genre_code,
    }
    #res = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=7)
    session = requests.Session()
    session.headers.update(HEADERS)
    res = session.get(BASE_URL, params=params,timeout=7)
    res.raise_for_status()
    data = res.json()

    programs = []
    for item in data.get("brdCntTvSchIDtoList") or []:
        start_time = item.get("epgStrtTme")  # "HH:MM:SS"
        title = item.get("brdPgmTitNm")
        if not start_time or not title:
            continue
        programs.append({
            "time": start_time[:5],  # "HH:MM"
            "title": title,
            "sub_title": item.get("brdPgmDscr"),
        })
    return programs


def build_today_schedule():
    result = {}
    for genre, channels in CHANNELS.items():
        result[genre] = []
        for name, (channel_id, genre_code, channel_no) in channels.items():
            try:
                programs = fetch_today_schedule(channel_id, genre_code)
                filtered = [p for p in programs if p["time"] >= "18:00"]
                if filtered:
                    result[genre].append({
                        "channel": name,
                        "channel_no": channel_no,
                        "programs": filtered,
                    })
            except Exception as e:
                print(f"[실패] {name}: {e}")
            time.sleep(0.5)  # 과도한 요청 방지
    return result


if __name__ == "__main__":
    data = build_today_schedule()
    with open("schedule.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("완료:", date.today())