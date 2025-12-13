# Link Bio 클론

Django로 구현한 링크 모음 페이지입니다. 관리자(admin)에서 프로필과 링크를 등록하면 링크인바이오 스타일의 랜딩 페이지를 노출합니다.

## 주요 기능
- 프로필(이름, 헤드라인, 소개, 아바타/배경 이미지, 포인트 컬러) 관리
- 링크(라벨, URL, 아이콘, 강조 여부, 노출 순서) 관리 및 정렬
- 기본 랜딩 페이지 및 슬러그별 개별 프로필 페이지 제공
- Django admin에서 프로필과 링크를 손쉽게 추가/수정

## 개발 환경
- Python 3.11+
- Django 5.x
- SQLite (기본 설정)

## 실행 방법
1. 가상환경을 만들고 Django를 설치합니다.
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. 마이그레이션을 적용합니다.
   ```bash
   python manage.py migrate
   ```
3. 슈퍼유저를 생성해 관리자에 로그인합니다.
   ```bash
   python manage.py createsuperuser
   ```
4. 개발 서버를 실행하고 브라우저에서 `http://127.0.0.1:8000/`에 접속합니다.
   ```bash
   python manage.py runserver
   ```

## Docker + Nginx + Gunicorn 실행
1. `.env.example`을 참고해 `.env` 파일을 만듭니다.
   ```bash
   cp .env.example .env
   ```
   - `DJANGO_SUPERUSER_USERNAME`, `DJANGO_SUPERUSER_PASSWORD`, `DJANGO_SUPERUSER_EMAIL`을 설정하면 컨테이너가 시작될 때 해당 계정이 없을 경우 자동으로 생성됩니다.
2. Docker로 애플리케이션을 실행합니다.
   ```bash
   docker-compose up --build
   ```
   - 브라우저에서 http://localhost 로 접속합니다.
   - `SERVER_NAME` 환경 변수를 변경하면 nginx `server_name` 값이 함께 반영됩니다.
   - SQLite 데이터베이스(`./data/db.sqlite3`)와 Django 로그(`/var/log/linky/linky.log`)는 Docker 볼륨으로 유지됩니다.

## Blue/Green 무중단 배포
- `docker-compose.yml`은 `web_blue`, `web_green` 두 인스턴스를 동시에 띄우고, nginx upstream이 두 인스턴스를 모두 바라보도록 구성되어 있습니다. 한쪽을 교체하는 동안 다른 쪽이 트래픽을 처리합니다.
- `deploy.sh`는 이미지 빌드 → 각 web 인스턴스 순차 배포 → 준비 체크 → nginx 재로드 순서로 실행됩니다.
  ```bash
  ./deploy.sh            # 기본은 docker compose 사용
  COMPOSE_CMD="docker compose -p linky" ./deploy.sh  # 프로젝트 명시가 필요할 때
  ```
- 준비 체크는 컨테이너 내부에서 `/healthz` → `/` 순으로 HTTP 요청을 시도하고, curl이 없을 경우 TCP 소켓으로 8000 포트 응답을 확인합니다. 체크가 통과한 후에만 다음 인스턴스 배포로 넘어가므로 배포 중 503을 최소화할 수 있습니다.

### /healthz 엔드포인트 추가 가이드
프레임워크에 관계없이 애플리케이션 코드에 단순 200 응답을 추가하면 준비 체크가 더 신뢰할 수 있습니다. WSGI/ASGI 미들웨어 또는 가장 단순한 라우터에 `/healthz`를 다음과 같이 추가하세요.

```python
# 예: WSGI 진입점에 추가하는 최소 구현
def healthz_app(environ, start_response):
    if environ.get("PATH_INFO") == "/healthz":
        start_response("200 OK", [("Content-Type", "text/plain")])
        return [b"ok"]
    return original_app(environ, start_response)

application = healthz_app  # 기존 WSGI 앱을 래핑
```

ASGI 프레임워크라면 비슷하게 `scope['path'] == '/healthz'`일 때 `200`을 반환하도록 가장 앞단에 라우팅하면 됩니다.

## 테스트
```bash
python manage.py test
```
