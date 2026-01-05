############################################
# Flet이 요구하는 유일한 진입점
# 여기엔 비즈니스 로직 / UI 코드를 두지 않음
# APK 빌드, 실행, 테스트에 제일 안정적인 형태
############################################

import flet as ft
from briefy.app import run_app

def main(page: ft.Page):
    run_app(page)

if __name__ == "__main__":
    ft.run(main)
