# Changelog: V1.1.0 -> V2.0.0 [2026-01-12]

### PASS-NICE 레포지토리가 PyPI에 모듈로 업로드되었습니다!
- 앞으로는 방치하지 않고 자주 관리하겠습니다.

### 추가된 기능
- 프록시 지원 추가

### 변경사항
- 함수 실행 후 결과 반환 객체 `<Result>`, `<CaptchaResult>` 추가 (`pass_nice.types`)

- camelCase -> snake_case로 함수/변수명 변경 및 비표준 문법을 수정했습니다. (PEP 8 준수)

- 전반적인 예외 처리 강화 및 추후 오류 수정을 위한 예외별 `error_code` 추가

- `send_sms_verification` 함수에서 `birthdate`

- NICE 내부 업데이트 대응 

### 오류 수정
- NICE 내부 업데이트 후 일부 기능이 작동하지 않던 오류를 수정하였습니다.

### 사용 중단 예정 (Deprecated)
- `getCaptcha` 함수 지원 종료 예정
- V1 사용자를 위하여 override 처리해뒀지만 곧 삭제될 예정입니다.