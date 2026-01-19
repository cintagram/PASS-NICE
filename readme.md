# PASS-NICE

[![PyPI version](https://badge.fury.io/py/pass-nice.svg)](https://badge.fury.io/py/pass-nice)
[![Python Versions](https://img.shields.io/pypi/pyversions/pass-nice.svg)](https://pypi.org/project/pass-nice/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

[NICE아이디](https://www.niceid.co.kr/index.nc/index.nc) 본인인증 요청을 자동화해주는 비공식적인 Python 모듈입니다.

## 주의사항

**교육용 및 학습용으로만 사용해 주세요**

- 이 라이브러리를 사용함으로써 발생하는 모든 피해나 손실은 사용자 본인의 책임입니다.
- **[NICE아이디](https://www.niceid.co.kr/index.nc/index.nc) 및 [한국도로교통공사](https://ex.co.kr/)측의 삭제 요청이 있을 경우, 즉시 삭제됩니다.**
- 모든 문의는 `sunr1s2@pm.me`로 부탁드립니다.
- 상업적 사용 시 출처를 명시해 주세요.

## 설치

```bash
pip install pass-nice
```

## 지원 기능

- NICE에서 지원하는 모든 형태의 본인인증 (SMS, PASS, QR)
- MVNO 포함 총 `6`개의 모든 통신사 지원
- 비동기 처리 (httpx 기반)
- 타입 안전성 (Type Hints)

## 지원 통신사

| 통신사 | 코드 | 비고 |
|--------|------|------|
| SKT | `"SK"` | SK텔레콤 |
| KT | `"KT"` | KT |
| LGU+ | `"LG"` | LG유플러스 |
| SKT 알뜰폰 | `"SM"` | SK 계열 MVNO |
| KT 알뜰폰 | `"KM"` | KT 계열 MVNO |
| LGU+ 알뜰폰 | `"LM"` | LG 계열 MVNO |

## 라이센스
이 프로젝트는 MIT 라이센스 하에 배포됩니다.

## Special Thanks
`@cintagram` - `PASS 앱 알림` 및 `QR` 본인인증 기능 추가에 도움을 주셨습니다!

## 자세한 Docs는
`/docs.md` 파일에서 확인하실 수 있습니다.

---
⭐ 이 프로젝트가 도움이 되셨다면 Star를 눌러주세요!
