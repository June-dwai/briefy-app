############################################
# 피드가 어떻게 보일지 책임지는 부분
# 카드 UI / 리스트 레이아웃 / 새로고침 버튼 / 스크롤 등
# 이 곳에선 절대 Supabase 키를 다루지 않고, 화면 전환도 결정하지 않으며, 앱 상태 관리도 안 함
############################################

import traceback
import flet as ft
from ..repo import fetch_reports
from .theme import card_bg, sub_text

def build_feed_view(page: ft.Page, status: ft.Text, feed: ft.ListView, on_toggle_theme, on_open_profile):
    page.controls.clear()

    def create_card(r: dict):
        date = (r.get("date") or "").strip()
        title = (r.get("title") or "").strip()
        context = (r.get("context") or "").strip()

        return ft.Container(
            bgcolor=card_bg(page),
            border_radius=16,
            padding=16,
            margin=ft.margin.only(bottom=10),
            expand=True,
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.CircleAvatar(
                                content=ft.Icon(ft.Icons.AUTO_AWESOME, color=ft.Colors.WHITE, size=18),
                                bgcolor=ft.Colors.BLUE_600,
                                radius=18,
                            ),
                            ft.Column(
                                [
                                    ft.Text("Briefy AI", size=13, weight=ft.FontWeight.BOLD),
                                    ft.Text(date, size=11, color=sub_text(page)),
                                ],
                                spacing=0,
                            ),
                            ft.Container(expand=True),
                            ft.Icon(ft.Icons.MORE_HORIZ, color=sub_text(page)),
                        ]
                    ),
                    ft.Text(title, size=18, weight=ft.FontWeight.W_800),
                    ft.Markdown(context, selectable=True, extension_set=ft.MarkdownExtensionSet.GITHUB_WEB),
                ],
                spacing=10,
            ),
        )

    def load_feed(e=None):
        try:
            status.value = "불러오는 중..."
            page.update()

            data = fetch_reports()
            feed.controls.clear()

            if not data:
                feed.controls.append(ft.Text("표시할 리포트가 없습니다."))
            else:
                for r in data:
                    feed.controls.append(create_card(r))

            status.value = f"최신 {len(data)}개"
            page.update()

        except Exception as ex:
            feed.controls.clear()
            feed.controls.append(
                ft.Text(
                    f"데이터 로딩 실패: {ex}\n\n{traceback.format_exc()}",
                    selectable=True,
                    color=ft.Colors.RED_400,
                )
            )
            status.value = "로딩 실패"
            page.update()

    page.appbar = ft.AppBar(
        title=ft.Text("Briefy", weight=ft.FontWeight.BOLD),
        actions=[
            ft.IconButton(ft.Icons.PERSON_OUTLINE, on_click=on_open_profile),  # ✅ 추가
            ft.IconButton(ft.Icons.REFRESH, on_click=load_feed),
            ft.IconButton(ft.Icons.DARK_MODE, on_click=on_toggle_theme),
        ],
    )


    page.add(
        ft.Container(
            padding=ft.padding.symmetric(horizontal=12, vertical=8),
            content=ft.Column(
                [ft.Text("오늘의 브리핑", size=16, weight=ft.FontWeight.BOLD), status],
                spacing=2,
            ),
        )
    )
    page.add(feed)

    load_feed()
