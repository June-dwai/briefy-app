import os
import warnings
import requests
import xml.etree.ElementTree as ET
import yfinance as yf
import pandas as pd
from google import genai
from dotenv import load_dotenv
from datetime import datetime, timedelta
from supabase import create_client, Client

# 경고 무시
warnings.filterwarnings("ignore")

# API 키 로드
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

# supabase 키 로드
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

if not api_key:
    print("❌ 에러: .env 파일을 찾을 수 없거나 API 키가 없습니다.")
    exit()

client = genai.Client(api_key=api_key)

# ==========================================
# 1. 날짜 계산 함수
# ==========================================
def get_latest_market_date():
    kst_now = datetime.now()
    us_now = kst_now - timedelta(hours=14) 
    target_date = us_now

    if target_date.weekday() == 5:  # 토 -> 금
        target_date -= timedelta(days=1)
    elif target_date.weekday() == 6:  # 일 -> 금
        target_date -= timedelta(days=2)
        
    return target_date

# ==========================================
# 2. 수치 데이터 수집 (★ 앱 호환성 최적화 ★)
# ==========================================
def fetch_market_indices(target_date):
    """
    앱(app_ui.py)이 파싱하기 가장 좋은 '순수 텍스트' 형태로 데이터를 반환합니다.
    불필요한 마크다운(**)이나 HTML 태그를 제거했습니다.
    """
    start_date = target_date - timedelta(days=7)
    end_date = target_date + timedelta(days=5)
    
    date_str = target_date.strftime("%Y-%m-%d")
    print(f"📊 [{date_str}] 기준: 지수, 빅테크, 섹터 데이터를 모두 수집합니다...")

    market_groups = {
        "주요 지수": {
            "다우존스": "^DJI", "S&P 500": "^GSPC", "나스닥": "^IXIC", 
            "VIX (공포지수)": "^VIX", "미국채 10년물": "^TNX"
        },
        "원자재 & 환율": {
            "금": "GC=F", "WTI 원유": "CL=F", 
            "비트코인": "BTC-USD", "달러 인덱스": "DX-Y.NYB"
        },
        "매그니피센트 7 (빅테크)": {
            "애플": "AAPL", "마이크로소프트": "MSFT", "엔비디아": "NVDA", 
            "구글": "GOOGL", "아마존": "AMZN", "메타": "META", "테슬라": "TSLA"
        },
        "주요 섹터 (ETF)": {
            "기술 (XLK)": "XLK", "에너지 (XLE)": "XLE", "금융 (XLF)": "XLF",
            "반도체 (SOXX)": "SOXX", "헬스케어 (XLV)": "XLV"
        }
    }

    final_summary = []

    for group_name, tickers in market_groups.items():
        # [수정] 앱이 제목으로 인식하도록 '###' 사용 (기존 ** 제거)
        group_lines = [f"\n### {group_name}"] 
        
        for name, symbol in tickers.items():
            try:
                df = yf.download(symbol, start=start_date, end=end_date, progress=False, multi_level_index=False)
                df.index = df.index.strftime("%Y-%m-%d")
                
                if date_str in df.index:
                    curr_close = df.loc[date_str]['Close']
                    curr_idx_loc = df.index.get_loc(date_str)
                    
                    if curr_idx_loc > 0:
                        prev_close = df.iloc[curr_idx_loc - 1]['Close']
                        change_pct = ((curr_close - prev_close) / prev_close) * 100
                        
                        # 아이콘 설정 (이모지는 텍스트로 취급되므로 OK)
                        if "VIX" in name or "미국채" in name:
                             icon = "📊" 
                        elif change_pct > 0:
                            icon = '📈' # 또는 🔺
                        elif change_pct < 0:
                            icon = '📉' # 또는 ⬇️
                        else:
                            icon = "-"
                        
                        # [수정] 볼드(**)나 span 태그 없이 순수 텍스트만 보냄
                        # 앱이 '괄호('와 '%'를 보고 색상을 입힘
                        line = f"- {icon} {name}: {curr_close:,.2f} ({change_pct:+.2f}%)"
                        group_lines.append(line)
                    else:
                        group_lines.append(f"- {name}: {curr_close:,.2f} (New)")
                else:
                    group_lines.append(f"- {name}: 데이터 없음")
                    
            except Exception:
                continue
        
        final_summary.extend(group_lines)

    return "\n".join(final_summary)

# ==========================================
# 3. 뉴스 데이터 수집 (★ 앱 호환성 최적화 ★)
# ==========================================
def fetch_rss_news(target_date):
    target_str = target_date.strftime("%Y-%m-%d")
    # 검색 기간을 여유 있게 설정 (after~before)
    next_day_str = (target_date + timedelta(days=2)).strftime("%Y-%m-%d")
    
    print(f"📡 [{target_str}] 주요 섹터별 뉴스를 수집합니다...")
    
    base_url = "https://news.google.com/rss/search?q={}+after:{}+before:{}&hl=en-US&gl=US&ceid=US:en"
    
    keywords = {
        "1_Market_Macro": "US Stock Market Economy Fed Inflation", 
        "2_Technology": "US Technology Stocks Big Tech",          
        "3_Semiconductor": "Semiconductor Stocks AI Chips",       
        "4_EV_Auto": "Electric Vehicle Stocks US Auto",           
        "5_Finance": "US Bank Stocks Financial Sector",
        "6_Energy_Oil": "US Energy Sector Oil Gas Refining Stocks",
        "7_Materials_Steel": "US Steel Industry Petrochemical Chemical Stocks"
    }
    
    collected_news = []
    
    # HTTP 요청 시 브라우저인 것처럼 보이게 하는 헤더 (차단 방지)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    for category, query in keywords.items():
        try:
            url = base_url.format(query.replace(" ", "+"), target_str, next_day_str)
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                continue

            # XML 파싱 (feedparser 대신 사용)
            root = ET.fromstring(response.content)
            
            count = 0
            # 구글 뉴스 RSS는 <channel> 안에 여러 개의 <item>이 있습니다.
            for item in root.findall(".//item"):
                if count >= 3: 
                    break 
                
                title = item.find("title").text if item.find("title") is not None else "No Title"
                link = item.find("link").text if item.find("link") is not None else ""
                pub_date_raw = item.find("pubDate").text if item.find("pubDate") is not None else ""

                # 날짜 체크 (단순 문자열 포함 여부로 체크하거나 생략 가능)
                # 구글 뉴스가 이미 검색어(after/before)로 필터링해주므로 바로 추가해도 무방합니다.
                clean_cat = category.split("_")[-1]
                news_item = f"- [{clean_cat}] {title} (Link: {link})"
                
                collected_news.append(news_item)
                count += 1
                        
        except Exception as e:
            print(f"Error fetching {category}: {e}")
            continue
            
    return "\n".join(collected_news)


# ==========================================
# 4. AI 리포트 작성
# ==========================================
def generate_market_briefing(indices_data, news_data, date_str):
    prompt = f"""
    당신은 월가 베테랑 애널리스트입니다. 
    제공된 [시장 데이터]와 [뉴스]를 종합하여 인사이트 있는 시황 리포트를 작성하세요.

    [작성 기준 날짜]
    {date_str} (미국 현지 시간)

    [시장 데이터 (지수/빅테크/섹터)]
    {indices_data}

    [주요 뉴스]
    {news_data}

    [작성 지침]
    1. ★ [제목 필수]: 리포트의 시작은 '오늘의 증시 요약 제목'이어야 합니다. 제목 맨 앞에는 반드시 '# ' (샵 1개 + 띄어쓰기)를 붙여서 가장 크고 굵게 표시하세요.
       - 예시: # 새해 첫 거래일, 나스닥 혼조세 출발
    2. [빅테크(M7) 및 특징주]: 제공된 'Magnificent 7' 데이터를 참고하여 등락률과 원인을 분석하세요.
    3. [섹터 흐름]: 어떤 섹터가 강세였는지 수치로 비교하세요.
    4. [시장 심리]: VIX와 국채금리를 언급하며 투자 심리를 평가하세요.
    5. [월가 분석]: 분석가들의 코멘트가 있으면 인용하세요.
    
    6. ★ [마크다운 문법 엄수 - 매우 중요]: 
       - 모바일 앱에서 제목이 잘 보이도록 다음 규칙을 반드시 지키세요.
       
       (1) 소제목 앞 '줄바꿈 2번' 필수: 
           - 소제목을 쓰기 전에는 반드시 엔터를 두 번 쳐서 윗 문단과 확실하게 띄워주세요. (줄바꿈이 없으면 제목으로 인식되지 않습니다.)
       
       (2) ★ [소제목 형식 필수 - 매우 중요]: 
            - 본문의 각 챕터 소제목은 반드시 '## [제목]' 형식을 지켜야 합니다. (샵 2개 + 대괄호)
            - 소제목 위에는 반드시 줄바꿈(엔터)을 2번 넣어서 윗 문단과 띄워주세요.
            
            [올바른 작성 예시]
            (...윗 문단 내용 끝)
            
            
            ## [빅테크(M7) 및 특징주]
            엔비디아는 상승했으나...
            
            
            ## [섹터 흐름]
            반도체 섹터가 강세를...
            
            
            ## [시장 심리]
            VIX 지수는...
       
       (3) 강조: 중요한 종목명이나 수치는 **굵게** 처리하세요. (예: **엔비디아**는 **+3% 급등**)

    경고: 수치는 제공된 데이터 그대로 사용하고, 절대 지어내지 마세요.
    """

    try:
        response = client.models.generate_content(
            model = 'gemini-3-flash-preview', 
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"❌ AI 작성 중 에러: {e}"



# ==========================================
# 5. 리포트를 Supabase DB에 저장하기 (컬럼명: context로 수정)
# ==========================================
def save_report_to_supabase(date_str, title, report_context):
    try:
        data = {
            "date": date_str,
            "title": title,
            "context": report_context 
        }
        # 데이터를 삽입하거나, 날짜가 겹치면 업데이트(upsert) 합니다.
        response = supabase.table("Reports_US_After").upsert(data, on_conflict="date").execute()
        print(f"🚀 [Supabase] {date_str} 리포트 저장 완료!")
    except Exception as e:
        print(f"❌ Supabase 저장 중 오류: {e}")

# ==========================================
# 6. 리포트 최신순으로 가져오기 (앱 화면 출력용)
# ==========================================
def get_reports_from_supabase():
    try:
        # 테이블 이름을 'Reports_US_After'로 정확히 지정해야 합니다.
        response = supabase.table("Reports_US_After") \
            .select("date, title, context") \
            .order("date", desc=True) \
            .execute()
        return response.data
    except Exception as e:
        print(f"❌ 데이터 로딩 실패: {e}")
        return []

# ==========================================
# 메인 실행부 (저장 로직 연결)
# ==========================================
# if __name__ == "__main__":
#     market_date = get_latest_market_date()
#     db_date_key = market_date.strftime("%Y-%m-%d")
    
#     # 1. 중복 확인
#     existing_reports = get_reports_from_supabase()
#     today_exists = any(report['date'] == db_date_key for report in existing_reports)

#     if today_exists:
#         print(f"✅ [{db_date_key}] 리포트가 이미 존재합니다.")
#     else:
#         # 2. 데이터 수집 및 AI 요약
#         indices_text = fetch_market_indices(market_date)
#         news_text = fetch_rss_news(market_date)
        
#         print("📝 AI 리포트 생성 중...")
#         ai_briefing = generate_market_briefing(indices_text, news_text, db_date_key)
        
#         # 3. DB 저장 (함수 호출)
#         report_title = f"{market_date.strftime('%Y년 %m월 %d일')} 증시 요약"
#         save_report_to_supabase(db_date_key, report_title, ai_briefing)

if __name__ == "__main__":
    # 1. 시작 날짜 설정
    start_date = datetime(2025, 12, 21)
    
    # 2. 미국 현지 시간 기준 '오늘' 계산 (한국 1월 5일 오전 -> 미국 1월 4일 일요일)
    # 미래 날짜의 데이터를 요청해서 에러가 나는 것을 방지합니다.
    us_now = datetime.now() - timedelta(hours=14)
    us_today = us_now.date()
    
    current_date = start_date
    
    # 3. 기존 DB 데이터 확인
    existing_reports = get_reports_from_supabase()
    existing_dates = [report['date'] for report in existing_reports]

    while current_date.date() <= us_today:
        db_date_key = current_date.strftime("%Y-%m-%d")
        
        # [체크 1] 주말 건너뛰기
        if current_date.weekday() >= 5:
            print(f"⏩ [{db_date_key}] 주말(토/일)이므로 건너뜁니다.")
            current_date += timedelta(days=1)
            continue
            
        # [체크 2] 이미 DB에 있는 날짜인지 확인
        if db_date_key in existing_dates:
            print(f"⏩ [{db_date_key}] 이미 데이터가 존재하여 건너뜁니다.")
            current_date += timedelta(days=1)
            continue

        print(f"🔍 [{db_date_key}] 시장 데이터 수집 중...")
        
        # [체크 3] 휴장일 감지 (가장 중요!)
        # fetch_market_indices가 내부에서 yfinance 데이터를 못 가져오면 "데이터 없음"을 반환합니다.
        indices_text = fetch_market_indices(current_date)
        
        if "데이터 없음" in indices_text or not indices_text.strip():
            print(f"🛑 [{db_date_key}] 시장 데이터가 없습니다. (미국 증시 휴장일로 판단)")
            current_date += timedelta(days=1)
            continue

        # --- 위 검증을 모두 통과하면 리포트 생성 시작 ---
        print(f"📝 AI 리포트 생성 시작 (모델: gemini-3.0-flash)...")
        news_text = fetch_rss_news(current_date)
        ai_briefing = generate_market_briefing(indices_text, news_text, db_date_key)
        
        # 최종 본문 구성
        final_context = f"{ai_briefing}\n\n---\n### 📊 상세 지수 데이터\n{indices_text}"
        report_title = f"{current_date.strftime('%Y년 %m월 %d일')} 증시 요약"
        
        # Supabase 저장
        save_report_to_supabase(db_date_key, report_title, final_context)
        
        # API 과부하 방지를 위한 짧은 대기
        import time
        time.sleep(2) 
        
        current_date += timedelta(days=1)

    print("✅ 모든 과거 데이터 생성이 완료되었습니다!")