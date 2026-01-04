import os
import flet as ft
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# -------------------------
# Supabase (앱은 "읽기만" 하므로 anon key만 사용)
# -------------------------
# SUPABASE_URL = os.getenv("SUPABASE_URL")
# SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_URL = "https://rrqkqpgilkjziivjuuzb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJycWtxcGdpbGtqemlpdmp1dXpiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njc1NDkwMTMsImV4cCI6MjA4MzEyNTAxM30.B6b1M22aKO3xRrJ2T0FC6-GGJKpCNdVXTLY8iCVLwzE"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJycWtxcGdpbGtqemlpdmp1dXpiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njc1NDkwMTMsImV4cCI6MjA4MzEyNTAxM30.B6b1M22aKO3xRrJ2T0FC6-GGJKpCNdVXTLY8iCVLwzE"

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    raise RuntimeError("SUPABASE_URL / SUPABASE_ANON_KEY 환경변수가 필요합니다. (.env 확인)")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

TABLE_NAME = os.getenv("SUPABASE_REPORTS_TABLE", "Reports_US_After")


def main(page: ft.Page):
    page.title = "Briefy 📱"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.bgcolor = "#F0F2F5"
    page.scroll = ft.ScrollMode.ADAPTIVE

    # -------------------------
    # 상태 / UI 공통
    # -------------------------
    status_text = ft.Text("", size=12, color=ft.Colors.BLUE_GREY_700)

    def set_status(msg: str):
        status_text.value = msg
        page.update()

    # 인스타/스레드 느낌: 중앙 정렬 + 폭 제한
    content_max_width = 720

    feed_list = ft.ListView(
        expand=True,
        spacing=10,
        padding=ft.padding.only(top=10, left=12, right=12, bottom=30),
    )

    # -------------------------
    # 데이터 로딩 (main.py에서 직접)
    # -------------------------
    def get_reports_from_supabase(limit: int = 50):
        """
        최신순으로 가져오기.
        date 컬럼이 문자열이어도 YYYY-MM-DD면 desc 정렬이 잘 됩니다.
        created_at이 있다면 order("created_at", desc=True) 추천.
        """
        try:
            resp = (
                supabase.table(TABLE_NAME)
                .select("date, title, context")
                .order("date", desc=True)  # ✅ 최신순
                .limit(limit)
                .execute()
            )
            return resp.data or []
        except Exception as e:
            print(f"❌ 데이터 로딩 실패: {e}")
            raise

    # -------------------------
    # 피드 카드 UI (인스타/스레드 톤)
    # -------------------------
    def create_news_card(report: dict):
        date = (report.get("date") or "").strip()
        title = (report.get("title") or "").strip()
        context = (report.get("context") or "").strip()

        header = ft.Row(
            [
                ft.CircleAvatar(
                    content=ft.Icon(ft.Icons.AUTO_AWESOME, color=ft.Colors.WHITE, size=18),
                    bgcolor=ft.Colors.BLUE_600,
                    radius=18,
                ),
                ft.Column(
                    [
                        ft.Text("Briefy AI", size=13, weight=ft.FontWeight.BOLD),
                        ft.Text(date, size=11, color=ft.Colors.GREY_600),
                    ],
                    spacing=0,
                ),
                ft.Container(expand=True),
                ft.Icon(ft.Icons.MORE_HORIZ, size=18, color=ft.Colors.GREY_600),
            ],
            alignment=ft.MainAxisAlignment.START,
        )

        body = ft.Column(
            [
                ft.Text(title, size=18, weight=ft.FontWeight.W_800),
                ft.Markdown(
                    context,
                    selectable=True,
                    extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
                ),
            ],
            spacing=10,
        )

        actions = ft.Row(
            [
                ft.Icon(ft.Icons.FAVORITE_BORDER, size=20, color=ft.Colors.GREY_700),
                ft.Container(width=6),
                ft.Icon(ft.Icons.CHAT_BUBBLE_OUTLINE, size=20, color=ft.Colors.GREY_700),
                ft.Container(width=6),
                ft.Icon(ft.Icons.BOOKMARK_BORDER, size=20, color=ft.Colors.GREY_700),
                ft.Container(expand=True),
                ft.Icon(ft.Icons.SHARE, size=20, color=ft.Colors.GREY_700),
            ],
            alignment=ft.MainAxisAlignment.START,
        )

        card = ft.Container(
            content=ft.Column([header, body, actions], spacing=12),
            padding=16,
            bgcolor=ft.Colors.WHITE,
            border_radius=16,
            shadow=ft.BoxShadow(
                blur_radius=10,
                spread_radius=1,
                color=ft.Colors.with_opacity(0.06, ft.Colors.BLACK),
                offset=ft.Offset(0, 3),
            ),
        )

        # 가운데 폭 제한
        return ft.Row(
            [
                ft.Container(
                    content=card,
                    width=content_max_width,
                    expand=False,
                )
            ],
            alignment=ft.MainAxisAlignment.CENTER,
        )

    # -------------------------
    # 화면 구성
    # -------------------------
    def show_feed():
        page.controls.clear()

        page.appbar = ft.AppBar(
            leading=ft.Icon(ft.Icons.SHOW_CHART, color=ft.Colors.BLUE_600),
            title=ft.Text("Briefy", weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK),
            bgcolor=ft.Colors.WHITE,
            center_title=False,
            actions=[
                ft.IconButton(ft.Icons.REFRESH, tooltip="새로고침", on_click=lambda e: load_feed()),
                ft.IconButton(ft.Icons.LOGIN, tooltip="로그인(준비중)", on_click=login_placeholder),
            ],
        )

        page.add(
            ft.Container(
                content=ft.Column(
                    [
                        ft.Container(height=8),
                        ft.Row(
                            [
                                ft.Container(
                                    content=ft.Column(
                                        [
                                            ft.Text("오늘의 브리핑", size=16, weight=ft.FontWeight.BOLD),
                                            status_text,
                                        ],
                                        spacing=4,
                                    ),
                                    width=content_max_width,
                                )
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                        ),
                        feed_list,
                    ],
                    spacing=0,
                    expand=True,
                ),
                expand=True,
            )
        )

        load_feed()

    # -------------------------
    # 로그인 (자리만 확보: 나중에 Google/Kakao 붙이기)
    # -------------------------
    def login_placeholder(e):
        page.open(
            ft.AlertDialog(
                title=ft.Text("로그인"),
                content=ft.Text("지금은 게스트 피드만 제공 중입니다.\n(추후 Google/Kakao 로그인 추가 예정)"),
                actions=[ft.TextButton("확인", on_click=lambda ev: page.close_dialog())],
            )
        )

    # page.close_dialog() 호환용 (버전별 차이 방지)
    def _close_dialog(_):
        page.dialog.open = False
        page.update()

    # 위 AlertDialog 닫기 호환 (혹시 page.close_dialog가 없을 수 있어서)
    def open_dialog(dialog: ft.AlertDialog):
        page.dialog = dialog
        page.dialog.open = True
        page.update()

    # open() API 없는 버전 대비
    def safe_open_dialog(dialog: ft.AlertDialog):
        try:
            page.open(dialog)
        except Exception:
            open_dialog(dialog)

    def login_placeholder(e):
        dialog = ft.AlertDialog(
            title=ft.Text("로그인"),
            content=ft.Text("지금은 게스트 피드만 제공 중입니다.\n(추후 Google/Kakao 로그인 추가 예정)"),
            actions=[ft.TextButton("확인", on_click=_close_dialog)],
        )
        safe_open_dialog(dialog)

    # -------------------------
    # 로딩
    # -------------------------
    def load_feed(limit: int = 50):
        try:
            set_status("불러오는 중...")
            reports = get_reports_from_supabase(limit=limit)

            feed_list.controls.clear()
            if not reports:
                feed_list.controls.append(
                    ft.Row(
                        [ft.Text("표시할 리포트가 없습니다.", color=ft.Colors.GREY_700)],
                        alignment=ft.MainAxisAlignment.CENTER,
                    )
                )
            else:
                for r in reports:
                    feed_list.controls.append(create_news_card(r))

            set_status(f"최신 {min(len(reports), limit)}개")
            page.update()

        except Exception as ex:
            feed_list.controls.clear()
            feed_list.controls.append(
                ft.Row(
                    [ft.Text(f"데이터 로딩 오류: {ex}", color=ft.Colors.RED_600)],
                    alignment=ft.MainAxisAlignment.CENTER,
                )
            )
            set_status("로드 실패 (RLS/테이블명/컬럼 확인)")
            page.update()

    # 시작: 바로 피드 보여주기 (게스트)
    show_feed()


# WEB_BROWSER는 개발용. APK 빌드하면 Android에서 정상 앱처럼 동작.
ft.app(target=main, port=8550, view=ft.AppView.WEB_BROWSER)
