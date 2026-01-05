import flet as ft
from .theme import card_bg, sub_text

def build_profile_view(
    page: ft.Page,
    display_name: str,
    email: str | None,
    on_back,
    on_toggle_theme,
):
    page.controls.clear()

    page.appbar = ft.AppBar(
        leading=ft.IconButton(ft.Icons.ARROW_BACK, on_click=on_back),
        title=ft.Text("내 페이지", weight=ft.FontWeight.BOLD),
        actions=[ft.IconButton(ft.Icons.DARK_MODE, on_click=on_toggle_theme)],
    )

    page.add(
        ft.Container(
            padding=20,
            content=ft.Column(
                [
                    ft.Container(height=10),
                    ft.Row(
                        [
                            ft.CircleAvatar(
                                content=ft.Text(
                                    (display_name[:1] or "?").upper(),
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.Colors.WHITE,
                                ),
                                bgcolor=ft.Colors.BLUE_600,
                                radius=28,
                            ),
                            ft.Container(width=14),
                            ft.Column(
                                [
                                    ft.Text(display_name, size=22, weight=ft.FontWeight.BOLD),
                                    ft.Text(
                                        email if email else "게스트",
                                        size=13,
                                        color=sub_text(page),
                                    ),
                                ],
                                spacing=2,
                            ),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Container(height=16),

                    # ✅ 지금은 “기능 placeholder”
                    ft.Container(
                        bgcolor=card_bg(page),
                        border_radius=16,
                        padding=16,
                        content=ft.Column(
                            [
                                ft.Text("추후 추가될 기능", weight=ft.FontWeight.BOLD),
                                ft.Text("• 저장한 글\n• 좋아요\n• 알림 설정\n• 구독 등", color=sub_text(page)),
                            ],
                            spacing=8,
                        ),
                    ),
                ],
                spacing=10,
            ),
        )
    )

    page.update()
