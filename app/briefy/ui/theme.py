############################################
# 테마 전담하는 모듈
# 색 및 다크모드 관리
# 다크 모드 깨질 때 이곳만 보면 됨, 나중에 디자인 변경도 쉬울 것
############################################

import flet as ft

def apply_theme(page: ft.Page):
    page.bgcolor = "#F0F2F5" if page.theme_mode == ft.ThemeMode.LIGHT else ft.Colors.BLACK

def card_bg(page: ft.Page):
    return ft.Colors.WHITE if page.theme_mode == ft.ThemeMode.LIGHT else ft.Colors.GREY_900

def sub_text(page: ft.Page):
    return ft.Colors.GREY_600 if page.theme_mode == ft.ThemeMode.LIGHT else ft.Colors.GREY_400
