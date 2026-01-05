############################################
# Supabase로부터 데이터를 어떻게 가져올지만을 담당하는 부분
# 나중에 Supabase -> Firebase를 한다거나, 테이블 이름 변경 / 칼럼 추가 등 할 때 이 부분만 건드림
# UI는 오직 여기 있는 함수를 통해 데이터 가져오는 것
############################################

from .config import REPORTS_TABLE, FETCH_LIMIT
from .supabase_client import get_supabase

def fetch_reports():
    supabase = get_supabase()
    resp = (
        supabase.table(REPORTS_TABLE)
        .select("date, title, context")
        .order("date", desc=True)
        .limit(FETCH_LIMIT)
        .execute()
    )
    return resp.data or []
