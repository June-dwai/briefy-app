############################################
# 설정값들을 모아둔 부분
# 값들만 넣어놨고 함수 및 로직은 아예 없는 파일
# 환경 변수 이름이 바뀌면 여기만 수정할 것
# 추후 DEV / PROD 환경 나둘 때도 여기서 처리해야 함.
############################################

import os
from dotenv import load_dotenv

load_dotenv()

# SUPABASE_URL = os.getenv("SUPABASE_URL")
# SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_URL = "https://rrqkqpgilkjziivjuuzb.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJycWtxcGdpbGtqemlpdmp1dXpiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njc1NDkwMTMsImV4cCI6MjA4MzEyNTAxM30.B6b1M22aKO3xRrJ2T0FC6-GGJKpCNdVXTLY8iCVLwzE"
REPORTS_TABLE = os.getenv("SUPABASE_REPORTS_TABLE", "Reports_US_After")
FETCH_LIMIT = int(os.getenv("BRIEFY_FETCH_LIMIT", "50"))

APP_DEEPLINK_CALLBACK = os.getenv("APP_DEEPLINK_CALLBACK", "briefy://auth-callback")
