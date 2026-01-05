############################################
# Supabase와의 연결을 이 곳에만 둠
# 모아둔 이유는 Supabase 키가 바뀌거나, 연결 방식이 바뀌거나, 캐싱/리트라이 넣고 싶을 때
# 이 파일만 바꾸면 앱 전체가 영향을 받고록 한 곳에 모아둠
############################################

from supabase import create_client, Client
from .config import SUPABASE_URL, SUPABASE_ANON_KEY

def get_supabase() -> Client:
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        raise RuntimeError("SUPABASE_URL / SUPABASE_ANON_KEY가 설정되지 않았습니다.")
    return create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
