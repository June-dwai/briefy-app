import sqlite3
import datetime
from fastapi import FastAPI
from apscheduler.schedulers.background import BackgroundScheduler
from contextlib import asynccontextmanager
import firebase_admin
from firebase_admin import credentials, messaging
import pandas_market_calendars as mcal # 휴장일 체크용
import backend # 기존에 만든 AI 뉴스 생성 모듈

# ==========================================
# 1. 설정 및 초기화
# ==========================================
# Firebase 설정 (Firebase 콘솔에서 받은 키 파일 필요)
# cred = credentials.Certificate("serviceAccountKey.json")
# firebase_admin.initialize_app(cred)

app = FastAPI()
DB_NAME = "news_feed.db"

# DB 초기화 (서버 켜질 때 없으면 생성)
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    # 뉴스 테이블: 타입(장전/마감), 날짜, 제목, 내용
    cur.execute("""
        CREATE TABLE IF NOT EXISTS news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            market_type TEXT, 
            report_type TEXT,
            date_str TEXT,
            title TEXT,
            content TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

# ==========================================
# 2. 핵심 로직: 휴장일 체크 및 뉴스 생성
# ==========================================
def is_market_open(market_code="NYSE"):
    """
    한국 시간이 아니라, '미국 현지 날짜' 기준으로 개장일인지 확인합니다.
    """
    nyse = mcal.get_calendar(market_code)
    
    # 1. 현재 한국 시간에서 14시간을 빼서 '미국 현지 시간(동부)'을 구합니다.
    # (월요일 아침 7시 KST -> 일요일 오후 5시 EST)
    us_now = datetime.datetime.now() - datetime.timedelta(hours=14)
    us_date_str = us_now.strftime("%Y-%m-%d")
    
    # 2. '미국 날짜'로 스케줄을 조회합니다.
    # 일요일이면 스케줄이 비어있으므로(Empty) False가 반환됩니다.
    schedule = nyse.schedule(start_date=us_date_str, end_date=us_date_str)
    
    return not schedule.empty

def job_us_morning_briefing():
    print(f"⏰ [작업 시작] 미국 증시 모닝 브리핑 생성 중... ({datetime.datetime.now()})")
    
    # 1. 휴장일 체크
    if not is_market_open("NYSE"):
        print("zzz... 오늘은 미국 증시 휴장일입니다. 뉴스를 생성하지 않습니다.")
        return

    try:
        # 2. 뉴스 생성 (backend.py 함수 사용)
        target_date = backend.get_latest_market_date()
        date_str = target_date.strftime("%Y-%m-%d")
        
        indices = backend.fetch_market_indices(target_date)
        news = backend.fetch_rss_news(target_date)
        body = backend.generate_market_briefing(indices, news, date_str)
        
        # 제목 추출 (첫 줄 # 제거)
        title = body.split('\n')[0].replace('#', '').strip()
        
        # 3. DB 저장 (SQLite)
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("INSERT INTO news (market_type, report_type, date_str, title, content) VALUES (?, ?, ?, ?, ?)",
                    ("US", "MORNING", date_str, title, body))
        conn.commit()
        conn.close()
        print("✅ DB 저장 완료!")

        # 4. 푸시 알림 발송 (Firebase)
        # send_push_notification("미국 증시 요약 도착!", title)
        
    except Exception as e:
        print(f"❌ 에러 발생: {e}")

# 푸시 발송 함수 (확장성 고려)
def send_push_notification(title, body):
    # 실제로는 앱에서 받은 토큰으로 전송해야 함 (Topic 전송 추천)
    message = messaging.Message(
        notification=messaging.Notification(title=title, body=body),
        topic="news_subscribers" # 앱에서 이 주제를 구독하게 하면 됨
    )
    response = messaging.send(message)
    print('🚀 푸시 전송 완료:', response)

# ==========================================
# 3. 스케줄러 설정 (확장성 고려)
# ==========================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 서버 켜질 때 실행
    init_db()
    
    scheduler = BackgroundScheduler()
    
    # [확장] 여기에 작업을 계속 추가하면 됩니다.
    # 예: 한국 시간 오전 7시 = 미국 장 마감 후 브리핑
    scheduler.add_job(job_us_morning_briefing, 'cron', hour=7, minute=0)
    
    # [확장 예시] 한국 장 마감 브리핑 (오후 4시)
    # scheduler.add_job(job_kr_close_briefing, 'cron', hour=16, minute=0)
    
    scheduler.start()
    yield

app = FastAPI(lifespan=lifespan)

# ==========================================
# 4. API (앱이 데이터를 가져가는 창구)
# ==========================================
@app.get("/feed")
def get_news_feed(limit: int = 10):
    """최신 뉴스 N개를 가져옵니다 (인스타 피드용)"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row # 딕셔너리 형태로 가져오기
    cur = conn.cursor()
    
    # 최신순(ORDER BY id DESC)으로 가져오기
    cur.execute("SELECT * FROM news ORDER BY id DESC LIMIT ?", (limit,))
    rows = cur.fetchall()
    conn.close()
    
    return {"feed": [dict(row) for row in rows]}