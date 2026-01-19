# Changelog: V2.0.2 -> V2.1.0 [2026-01-19]

### PASS-NICE 레포지토리가 PyPI에 모듈로 업로드되었습니다!
- `pip install pass_nice` 를 통해 설치하실 수 있습니다.

### 추가된 기능
- `PASS 앱 알림`, `PASS 앱 QR` 본인인증 방식이 추가되었습니다.
- 본인인증 데이터를 반환하는 `<VerificationData>` 모델이 추가되었습니다. (`/types.py`)

### 변경사항
- 비표준 문법을 수정했습니다. (PEP 8 준수 + 가독성 향상)
- V1 -> V2 변경 후 혼동이 생길 것으로 예상되어 `docs.md`(docs)를 추가했습니다.
- 각 함수별로 표준 형식을 준수한 docString을 생성했습니다.