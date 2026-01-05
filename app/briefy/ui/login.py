############################################
# 로그인 선택 화면 (Google / Kakao / Guest 버튼 UI)
# 버튼 위치 및 스타일 결정
# 클릭할 시에 콜백만 호출하게 됨
############################################

import flet as ft

def build_login_view(page: ft.Page, status: ft.Text, on_guest, on_google, on_kakao, on_toggle_theme):
    page.controls.clear()

    page.appbar = ft.AppBar(
        title=ft.Text("Briefy", weight=ft.FontWeight.BOLD),
        center_title=True,
        actions=[ft.IconButton(ft.Icons.DARK_MODE_OUTLINED, on_click=on_toggle_theme)],
        bgcolor=ft.Colors.SURFACE,
    )

    page.add(
        ft.Row(
            [
                ft.Container(
                    width=360,
                    padding=20,
                    content=ft.Column(
                        [
                            ft.Icon(ft.Icons.FLASH_ON, size=90, color=ft.Colors.AMBER_400),
                            ft.Text("Briefy에 오신 것을 환영합니다", size=22, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                            ft.Text("AI가 요약한 뉴스를 피드로 확인하세요", opacity=0.7, text_align=ft.TextAlign.CENTER),
                            ft.Container(height=10),
                            status,
                            ft.Container(height=10),
                            
                            # ✅ Google 버튼: 흰색 배경 + 그림자 + 구글 블루 텍스트
                            ft.ElevatedButton(
                                content=ft.Row(
                                    [
                                        ft.Icon(ft.Icons.G_MOBILEDATA, color="#4285F4", size=30),
                                        ft.Text("Google로 계속하기", size=16, weight=ft.FontWeight.W_600, color=ft.Colors.BLACK87),
                                    ],
                                    alignment=ft.MainAxisAlignment.CENTER,
                                ),
                                on_click=on_google,
                                width=320,
                                height=50,
                                style=ft.ButtonStyle(
                                    bgcolor=ft.Colors.WHITE,
                                    shape=ft.RoundedRectangleBorder(radius=12),
                                    elevation={"pressed": 0, "": 2},
                                ),
                            ),

                            # ✅ Kakao 버튼: 카카오 옐로우 + 블랙 텍스트
                            ft.ElevatedButton(
                                content=ft.Row(
                                    [
                                        ft.Icon(ft.Icons.CHAT_BUBBLE_ROUNDED, color="#191919", size=18),
                                        ft.Text("Kakao로 계속하기", size=16, weight=ft.FontWeight.W_600, color="#191919"),
                                    ],
                                    alignment=ft.MainAxisAlignment.CENTER,
                                ),
                                on_click=on_kakao,
                                width=320,
                                height=50,
                                style=ft.ButtonStyle(
                                    bgcolor="#FEE500",
                                    shape=ft.RoundedRectangleBorder(radius=12),
                                    elevation={"pressed": 0, "": 1},
                                ),
                            ),

                            ft.Container(height=4),
                            
                            # ✅ 게스트 버튼: 깔끔한 외곽선 스타일
                            ft.OutlinedButton(
                                content=ft.Text("게스트로 시작하기"), # ✅ text 대신 content를 사용
                                on_click=on_guest,
                                width=320,
                                height=50,
                                style=ft.ButtonStyle(
                                    shape=ft.RoundedRectangleBorder(radius=12),
                                    side={"": ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT)},
                                ),
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=12,
                    ),
                )
            ],
            expand=True,
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
    )
    page.update()