############################################
# 앱의 뇌를 담당하는 부분, 화면 전환 및 상태 관리를 담당함
# 다크모드 토글 가능함
# 게스트로 시작 -> feed 전환
# Google/Kakao 로그인 버튼 눌 렀을 때의 전환
############################################

import urllib.parse
import flet as ft
from .config import SUPABASE_URL, APP_DEEPLINK_CALLBACK
from .supabase_client import get_supabase
from .ui.theme import apply_theme
from .ui.login import build_login_view
from .ui.feed import build_feed_view
from .ui.profile import build_profile_view


def run_app(page: ft.Page):
    page.theme_mode = ft.ThemeMode.LIGHT
    page.scroll = ft.ScrollMode.ADAPTIVE
    page.padding = 0

    supabase = get_supabase()

    status = ft.Text("", size=12, opacity=0.8)
    feed = ft.ListView(expand=True, spacing=10, padding=ft.padding.all(12))
    state = {
        "view": "login",      # login / feed / profile
        "display_name": "게스트",
        "email": None,
    }


    def toast(msg: str):
        page.snack_bar = ft.SnackBar(ft.Text(msg))
        page.snack_bar.open = True
        page.update()

    def set_status(msg: str):
        status.value = msg
        page.update()

    def toggle_theme(e=None):
        page.theme_mode = ft.ThemeMode.DARK if page.theme_mode == ft.ThemeMode.LIGHT else ft.ThemeMode.LIGHT
        apply_theme(page)
        rebuild()

    def go_feed(e=None):
        state["display_name"] = "게스트"
        state["email"] = None
        state["view"] = "feed"
        rebuild()

    def go_login(e=None):
        state["view"] = "login"
        rebuild()

    def go_profile(e=None):
        state["view"] = "profile"
        rebuild()

    def back_to_feed(e=None):
        state["view"] = "feed"
        rebuild()   


    # ✅ Supabase OAuth URL 생성 + 열기
    async def start_supabase_oauth(provider: str):
        if not SUPABASE_URL:
            toast("SUPABASE_URL이 설정되지 않았습니다.")
            return

        redirect = APP_DEEPLINK_CALLBACK
        
        # 기본 쿼리 파라미터 설정
        params = {
            "provider": provider,
            "redirect_to": redirect
        }

        # ✅ 카카오일 경우, 권한이 없는 email을 빼고 'profile'만 명시적으로 요청
        if provider == "kakao":
            # 현재 설정에서 '선택 동의'인 항목들만 넣어야 합니다.
            params["scopes"] = "profile_nickname profile_image"

        # URL 생성 (urllib.parse.urlencode를 사용하면 더 안전합니다)
        query_string = urllib.parse.urlencode(params)
        auth_url = f"{SUPABASE_URL}/auth/v1/authorize?{query_string}"

        print("AUTH URL (Final):", auth_url)
        try:
            await page.launch_url(auth_url)
        except Exception:
            import webbrowser
            webbrowser.open(auth_url)

    async def google_login(e=None):
        await start_supabase_oauth("google")

    async def kakao_login(e=None):
        await start_supabase_oauth("kakao")

    # ✅ 딥링크로 돌아온 code 처리
    def try_exchange_session_from_url():
        full_url = page.url or ""
        # 예: briefy://auth-callback?code=xxxxx
        parsed = urllib.parse.urlparse(full_url)
        qs = urllib.parse.parse_qs(parsed.query)
        code = (qs.get("code") or [None])[0]
        if not code:
            return False

        print("OAUTH CODE:", code)
        try:
            set_status("세션 생성 중...")
            # supabase-py 버전에 따라 dict/str 둘 다 대응
            try:
                supabase.auth.exchange_code_for_session({"auth_code": code})
            except Exception:
                supabase.auth.exchange_code_for_session(code)

            session = supabase.auth.get_session()
            if session and getattr(session, "user", None):
                user = session.user
                meta = getattr(user, "user_metadata", None) or {}

                state["email"] = getattr(user, "email", None)

                name = meta.get("full_name") or meta.get("name") or meta.get("nickname")
                if not name:
                    if state["email"]:
                        name = state["email"].split("@")[0]
                    else:
                        name = "사용자"

                state["display_name"] = name

                set_status("")
                state["view"] = "feed"
                rebuild()
                return True


            set_status("세션 생성 실패(설정 확인 필요)")
            return False

        except Exception as ex:
            set_status(f"로그인 처리 실패: {ex}")
            return False

    def rebuild():
        apply_theme(page)

        if state["view"] == "feed":
            build_feed_view(
                page,
                status=status,
                feed=feed,
                on_toggle_theme=toggle_theme,
                on_open_profile=go_profile,   # ✅ 추가
            )
        elif state["view"] == "profile":
            build_profile_view(
                page,
                display_name=state["display_name"],
                email=state["email"],
                on_back=back_to_feed,
                on_toggle_theme=toggle_theme,
            )
        else:
            build_login_view(
                page,
                status=status,
                on_guest=go_feed,
                on_google=google_login,
                on_kakao=kakao_login,
                on_toggle_theme=toggle_theme,
            )


    # ✅ 앱 시작 시: 혹시 이미 세션 있으면 바로 feed
    try:
        session = supabase.auth.get_session()
        if session and getattr(session, "user", None):
            user = session.user
            meta = getattr(user, "user_metadata", None) or {}

            state["email"] = getattr(user, "email", None)

            name = meta.get("full_name") or meta.get("name") or meta.get("nickname")
            if not name:
                name = state["email"].split("@")[0] if state["email"] else "사용자"

            state["display_name"] = name
            state["view"] = "feed"
    except Exception:
        pass


    # ✅ 앱 시작 시: 딥링크로 들어온 경우 code 교환 시도
    try_exchange_session_from_url()

    # ✅ route/url 변경될 때마다 code 처리 시도
    def on_route_change(e):
        try_exchange_session_from_url()

    page.on_route_change = on_route_change

    rebuild()
