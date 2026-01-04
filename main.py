import os
import urllib.parse
import flet as ft
import webbrowser
import urllib.parse

from flet.auth.providers import GoogleOAuthProvider
from supabase import create_client, Client
from backend import get_reports_from_supabase  # 그대로 사용한다고 가정
from dotenv import load_dotenv
load_dotenv()


# -------------------------
# Supabase
# -------------------------
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# -------------------------
# Google OAuth (Flet)
# -------------------------
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

# 개발용 앱 URL (로그인 후 돌아올 주소)
# - 로컬에서 Flet 웹으로 띄우면 보통 이런 형태로 맞춥니다.
APP_URL = "http://localhost:8550"  # 고정
OAUTH_CALLBACK = f"{APP_URL}/oauth_callback"



def main(page: ft.Page):
    print("=== MAIN STARTED ===")

    page.title = "Briefy 📱"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.bgcolor = "#F0F2F5"
    page.scroll = ft.ScrollMode.ADAPTIVE

    status_text = ft.Text("", size=14, color=ft.Colors.BLUE_GREY_700)

    def set_status(msg: str):
        status_text.value = msg
        page.update()

    # -------------------------
    # OAuth Provider (Flet)
    # -------------------------
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET or "YOUR_" in GOOGLE_CLIENT_ID:
        page.add(
            ft.Column(
                [
                    ft.Text("Google OAuth 설정이 필요합니다", size=18, weight=ft.FontWeight.BOLD),
                    ft.Text("GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET 환경변수를 설정하세요."),
                    ft.Text("Google OAuth Client에 Redirect URI 추가:"),
                    ft.Text(OAUTH_CALLBACK, selectable=True),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
            )
        )
        page.update()
        return

    google_provider = GoogleOAuthProvider(
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        redirect_url=OAUTH_CALLBACK,
    )

    # -------------------------
    # UI: feed
    # -------------------------
    feed_list = ft.ListView(expand=True, spacing=10, padding=10)

    def create_news_card(report: dict):
        date = report.get("date", "")
        title = report.get("title", "")
        context = report.get("context", "")

        return ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.CircleAvatar(
                                content=ft.Icon(ft.Icons.STAR, color=ft.Colors.WHITE),
                                bgcolor=ft.Colors.BLUE_ACCENT,
                                radius=20,
                            ),
                            ft.Column(
                                [
                                    ft.Text("AI Market Analyst", weight=ft.FontWeight.BOLD, size=14),
                                    ft.Text(f"{date} • Market Summary", size=12, color=ft.Colors.GREY_600),
                                ],
                                spacing=0,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.START,
                    ),
                    ft.Text(title, size=18, weight=ft.FontWeight.W_800),
                    ft.Markdown(context, selectable=True, extension_set=ft.MarkdownExtensionSet.GITHUB_WEB),
                ],
                spacing=12,
            ),
            padding=20,
            margin=ft.margin.only(bottom=10),
            bgcolor=ft.Colors.WHITE,
        )

    def load_data():
        try:
            set_status("리포트 불러오는 중...")
            reports = get_reports_from_supabase()
            feed_list.controls.clear()

            if not reports:
                feed_list.controls.append(ft.Text("표시할 리포트가 없습니다."))
            else:
                for r in reports:
                    feed_list.controls.append(create_news_card(r))

            set_status("")
            page.update()
        except Exception as ex:
            feed_list.controls.clear()
            feed_list.controls.append(ft.Text(f"데이터 로딩 오류: {ex}"))
            set_status("데이터 로딩 실패")
            page.update()

    # -------------------------
    # Views
    # -------------------------
    def logout_click(e):
        try:
            supabase.auth.sign_out()
        except Exception as ex:
            print("sign_out error:", ex)
        build_login_view()

    def build_main_view(user_email: str | None):
        page.controls.clear()
        page.appbar = ft.AppBar(
            leading=ft.Icon(ft.Icons.SHOW_CHART, color=ft.Colors.BLUE_600),
            title=ft.Text("Briefy Insights", weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK),
            bgcolor=ft.Colors.WHITE,
            actions=[
                ft.Text(user_email or "", size=12),
                ft.IconButton(ft.Icons.LOGOUT, on_click=logout_click),
            ],
        )
        page.add(status_text)
        page.add(feed_list)
        load_data()

    def build_login_view():
        page.controls.clear()
        page.appbar = ft.AppBar(
            title=ft.Text("Briefy", weight=ft.FontWeight.BOLD),
            bgcolor=ft.Colors.WHITE,
            center_title=True,
        )

        def login_click(e):
            print("LOGIN CLICKED")
            set_status("Google 로그인 페이지로 이동합니다...")

            auth_url = (
                f"{SUPABASE_URL}/auth/v1/authorize?"
                f"provider=google&"
                f"redirect_to={urllib.parse.quote(APP_URL, safe=':/')}"
            )

            print("=== SUPABASE AUTH URL ===")
            print(auth_url)
            print("=========================")

            webbrowser.open(auth_url)  # ✅ 이건 반드시 열린다

        page.add(
            ft.Column(
                [
                    ft.Icon(ft.Icons.FLASH_ON, size=90, color=ft.Colors.AMBER_400),
                    ft.Text("Briefy에 오신 것을 환영합니다", size=20, weight=ft.FontWeight.BOLD),
                    ft.Text("AI가 요약한 10일치 뉴스를 만나보세요", color=ft.Colors.GREY_600),
                    ft.Container(height=10),
                    status_text,
                    ft.Container(height=10),
                    ft.ElevatedButton(
                        "Google로 계속하기",
                        on_click=login_click,
                        style=ft.ButtonStyle(
                            bgcolor=ft.Colors.BLUE_600,
                            color=ft.Colors.WHITE,
                            padding=ft.padding.all(20),
                        ),
                    ),
                    ft.ElevatedButton(
                            "피드 보기 (게스트)",
                            on_click=lambda e: build_main_view(user_email=None),
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )
        )
        page.update()

    # -------------------------
    # OAuth 완료 이벤트: 여기서 Supabase 로그인!
    # -------------------------
    def on_login(e: ft.LoginEvent):
        print("=== on_login fired ===")
        if e.error:
            print("LOGIN ERROR:", e.error, getattr(e, "error_description", ""))
            set_status(f"로그인 실패: {e.error}")
            return

        token_obj = page.auth.token
        user_obj = page.auth.user
        print("AUTH USER:", getattr(user_obj, "id", None), user_obj)
        print("TOKEN OBJ:", token_obj)

        # Google의 id_token을 기대
        id_token = getattr(token_obj, "id_token", None)
        if not id_token:
            set_status("로그인 성공했지만 id_token이 없습니다. (scope/설정 확인 필요)")
            return

        try:
            set_status("Supabase 세션 생성 중...")
            supabase.auth.sign_in_with_id_token({"provider": "google", "token": id_token})

            session = supabase.auth.get_session()
            email = None
            if session and getattr(session, "user", None):
                email = getattr(session.user, "email", None)

            set_status("")
            build_main_view(email)
        except Exception as ex:
            print("Supabase sign_in_with_id_token failed:", ex)
            set_status(f"Supabase 로그인 실패: {ex}")

    page.on_login = on_login
    build_login_view()


ft.app(target=main, port=8550, view=ft.AppView.WEB_BROWSER)