app/
  main.py                ← 앱 엔트리 (아주 얇음)
  requirements.txt

  briefy/
    __init__.py
    app.py               ← 앱 전체 흐름 / 상태 / 화면 전환
    config.py            ← 환경변수 / 상수
    supabase_client.py   ← Supabase 연결 1곳에서 관리
    repo.py              ← DB 접근 로직 (select/insert 등)

    ui/
      __init__.py
      feed.py            ← 피드 화면 UI
      login.py           ← 로그인 선택 화면 UI
      theme.py           ← 다크/라이트 테마
      profile.py         ← 사용자 개인 페이지
