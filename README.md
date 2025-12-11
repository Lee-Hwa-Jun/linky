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

## Docker + Nginx + Uvicorn 실행 (HTTPS 지원)
1. `.env.example`을 참고해 `.env` 파일을 만듭니다. 로컬에서 생성한 인증서를 nginx 컨테이너에 마운트할 수 있도록 경로를 지정합니다.
   ```bash
   cp .env.example .env
   # SSL_CERT_PATH와 SSL_KEY_PATH에 사용할 인증서 경로를 입력합니다.
   ```
2. 테스트용 자체 서명 인증서가 필요하다면 다음과 같이 생성할 수 있습니다.
   ```bash
   mkdir -p certs
   openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
     -keyout certs/server.key -out certs/server.crt \
     -subj "/C=KR/ST=Seoul/O=Linky/OU=Dev/CN=localhost"
   ```
3. Docker로 애플리케이션을 실행합니다.
   ```bash
   docker-compose up --build
   ```
   - http://localhost 로 접속하거나, HTTPS가 필요한 경우 https://localhost 로 접속합니다.
   - `SERVER_NAME` 환경 변수를 변경하면 nginx `server_name` 값이 함께 반영됩니다.

## 테스트
```bash
python manage.py test
```
