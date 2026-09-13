from curl_cffi import requests
import time
import json
import sys
from datetime import date, datetime, timezone, timedelta

BASE_URL = "https://www.lguplus.com/uhdc/fo/prdv/chnlgid/v1/tv-schedule-list"

KST = timezone(timedelta(hours=9))

def today_kst() -> date:
    """서버(러너)의 시간대와 무관하게 항상 한국 기준 오늘 날짜를 반환"""
    return datetime.now(KST).date()

HEADERS = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "referer": "https://www.lguplus.com/iptv/channel-guide",
    "x-menu-url": "/iptv/channel-guide",
    "user-agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
}

CHANNELS = {
     "영화": {
        "OCN": ("684", "02", "44"),
        "OCN Movies": ("686", "02", "45"),
        "OCN Movies2": ("685", "02", "51"),
        "채널액션": ("593", "02", "54"),
        "채널나우": ("654", "02", "140"),
        "CINETREE": ("574", "02", "50"),
        "엠플렉스": ("756", "02", "48"),
        "더 무비": ("724", "02", "49"),
    },
    "해외드라마": {
        "NXT": ("744", "02", "141"),
        "채널J": ("656", "02", "144"),
        "채널W": ("161", "02", "146"),
    },
    "해외축구": {
        "스포티비": ("667", "01", "107"),
        "스포티비2": ("638", "01", "108"),
        "ENA SPORTS": ("692", "01", "112"),
        "tvN SPORTS": ("778", "01", "116"),
        "OGN": ("681", "01", "119"),
        "BallTV": ("659", "01", "126"),
        "JTBC SPORTS": ("795", "01", "102"),
    },
    "기타": {
        "CNN International": ("729", "03", "200"),
        "디스커버리": ("610", "04", "194"),
        "히스토리": ("664", "04", "218"),
        "NHK World Premium": ("633", "03", "209"),
    }
}


def get_cutoff_time(today: date) -> str:
    is_weekend = today.weekday() >= 5
    return "09:00" if is_weekend else "18:00"


def fetch_today_schedule(channel_id: str, genre_code: str, today: date):
    date_str = today.strftime("%Y%m%d")
    params = {
        "brdCntrTvChnlBrdDt": date_str,
        "urcBrdCntrTvChnlId": channel_id,
        "urcBrdCntrTvChnlGnreCd": genre_code,
    }
    res = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=7, impersonate="chrome")
    res.raise_for_status()
    data = res.json()

    programs = []
    for item in data.get("brdCntTvSchIDtoList") or []:
        start_time = item.get("epgStrtTme")
        title = item.get("brdPgmTitNm")
        if not start_time or not title:
            continue
        programs.append({
            "time": start_time[:5],
            "title": title,
            "sub_title": item.get("brdPgmDscr"),
        })
    return programs


def build_today_schedule():
    today = today_kst()
    cutoff = get_cutoff_time(today)
    result = {}
    fail_count = 0
    total_count = 0
    for genre, channels in CHANNELS.items():
        result[genre] = []
        for name, (channel_id, genre_code, channel_no) in channels.items():
            total_count += 1
            try:
                programs = fetch_today_schedule(channel_id, genre_code, today)
                filtered = [p for p in programs if p["time"] >= cutoff]
                if filtered:
                    result[genre].append({
                        "channel": name,
                        "channel_no": channel_no,
                        "programs": filtered,
                    })
            except Exception as e:
                fail_count += 1
                print(f"[실패] {name}: {e}")
            time.sleep(0.5)
    return result, fail_count, total_count, today


if __name__ == "__main__":
    data, fail_count, total_count, today = build_today_schedule()

    if fail_count == total_count:
        print(f"모든 채널({total_count}개) 요청 실패 — schedule.json을 덮어쓰지 않고 종료합니다.")
        sys.exit(1)

    with open("schedule.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    if fail_count > 0:
        print(f"완료(일부 실패 {fail_count}/{total_count}, 기준일 {today}):")
    else:
        print(f"완료(기준일 {today}):")