# 매크로 경제 뉴스 다이제스트 자동 발송

매일 아침 거시경제(매크로) 관련 해외 기사를 RSS로 수집해 한국어로 번역·요약한 뒤
이메일로 발송하는 자동화 시스템입니다. Claude Code의 **scheduled remote agent(routine)**가
매일 정해진 시간에 클라우드에서 이 저장소를 클론해 실행합니다.

## 동작 흐름

1. `fetch_news.py` — WSJ, CNBC, 연방준비제도(Fed), Investing.com 등 RSS 피드에서
   최근 기사 목록을 JSON으로 수집 (표준 라이브러리만 사용, pip install 불필요)
2. (원격 에이전트가 직접 수행) 거시경제 관련도가 높은 기사 8~12개를 선별하고
   한국어로 번역·요약하여 HTML 다이제스트(`digest.html`)를 생성
3. `send_email.py` — 생성된 HTML을 Gmail SMTP로 발송

## 파일 구성

| 파일 | 설명 |
|---|---|
| `fetch_news.py` | RSS 피드 수집 스크립트. 최근 30시간 이내 기사를 모아 JSON으로 출력 |
| `send_email.py` | Gmail SMTP를 통해 HTML 이메일을 발송하는 스크립트 |

## 환경변수 (시크릿)

`send_email.py`는 다음 환경변수를 필요로 합니다. 코드에는 값이 포함되어 있지 않으며,
원격 라우틴 실행 시 프롬프트 내에서 `export`로 설정됩니다.

| 변수 | 설명 |
|---|---|
| `GMAIL_ADDRESS` | 발신 Gmail 주소 |
| `GMAIL_APP_PASSWORD` | Gmail 앱 비밀번호 (https://myaccount.google.com/apppasswords 에서 생성) |
| `DIGEST_RECIPIENT` | 수신 이메일 주소 (생략 시 `GMAIL_ADDRESS`와 동일) |

## 로컬 테스트

```bash
# 1. 뉴스 수집 확인
python fetch_news.py > out.json

# 2. 메일 발송 테스트
$env:GMAIL_ADDRESS = "you@gmail.com"
$env:GMAIL_APP_PASSWORD = "xxxx xxxx xxxx xxxx"
$env:DIGEST_RECIPIENT = "you@gmail.com"
python send_email.py --subject "테스트" --body-file digest.html
```

## 자동 실행 스케줄

Claude Code 라우틴으로 등록되어 있으며, 매일 **KST 오전 7시(UTC 22:00)**에 실행됩니다.

- cron: `0 22 * * *` (UTC)
- 관리: https://claude.ai/code/routines
