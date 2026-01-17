# PASS-NICE

[![PyPI version](https://badge.fury.io/py/pass-nice.svg)](https://badge.fury.io/py/pass-nice)
[![Python Versions](https://img.shields.io/pypi/pyversions/pass-nice.svg)](https://pypi.org/project/pass-nice/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

[NICE아이디](https://www.niceid.co.kr/index.nc/index.nc) 본인인증 요청을 자동화해주는 비공식적인 Python 모듈입니다.

## ⚠️ 주의사항

**교육용 및 학습용으로만 사용해 주세요**

- 이 라이브러리를 사용함으로써 발생하는 모든 피해나 손실은 사용자 본인의 책임입니다.
- **[NICE아이디](https://www.niceid.co.kr/index.nc/index.nc) 및 [한국도로교통공사](https://ex.co.kr/)측의 삭제 요청이 있을 경우, 즉시 삭제됩니다.**
- 상업적 사용 시 출처를 명시해 주세요.

## 🚀 설치

```bash
pip install pass-nice
```

## 📋 지원 기능

- ✅ SMS 본인인증 (MVNO 포함, 모든 통신사 지원)
- 🔄 PASS 앱 본인인증 (지원 예정)
- 🌐 비동기 처리 (httpx 기반)
- 🛡️ 타입 안전성 (Type Hints)

## 🏗️ 지원 통신사

| 통신사 | 코드 | 비고 |
|--------|------|------|
| SKT | `"SK"` | SK텔레콤 |
| KT | `"KT"` | KT |
| LGU+ | `"LG"` | LG유플러스 |
| SKT 알뜰폰 | `"SM"` | SK 계열 MVNO |
| KT 알뜰폰 | `"KM"` | KT 계열 MVNO |
| LGU+ 알뜰폰 | `"LM"` | LG 계열 MVNO |

## 💻 사용법

### 기본 사용예제

```python
import asyncio
import pass_nice

async def main():
    # 클라이언트 생성 (SKT 사용자의 경우로 예제를 작성했습니다.)
    async with pass_nice.PASS_NICE("SK") as client:
        # 1. 세션 초기화
        init_result = await client.init_session()
        if not init_result.success:
            print(f"세션 초기화 실패: {init_result.message}")
            return
        
        # 2. 캡챠 이미지 가져오기
        captcha_result = await client.retrieve_captcha()
        if not captcha_result.success:
            print(f"캡챠 이미지 가져오기 실패: {captcha_result.message}")
            return
            
        # 캡챠 이미지를 파일로 저장
        with open("captcha.png", "wb") as f:
            f.write(captcha_result.data)
        
        # 3. 사용자로부터 캡챠 입력 받기
        captcha_answer = input("캡챠 이미지를 확인하고 숫자 6자리를 입력하세요: ")
        
        # 4. SMS 인증 요청
        sms_result = await client.send_sms_verification(
            name="홍길동",
            birthdate="010203",  # YYMMDD
            gender="1",          # 주민등록번호 뒷자리 첫째 자리
            phone="01012345678", # 하이픈 없이
            captcha_answer=captcha_answer
        )
        
        if not sms_result.success:
            print(f"SMS 전송 실패: {sms_result.message}")
            return
            
        print("SMS가 전송되었습니다!")
        
        # 5. SMS 인증 코드 확인
        sms_code = input("휴대폰으로 받은 6자리 인증 코드를 입력하세요: ")
        
        verify_result = await client.check_sms_verification(sms_code)
        if verify_result.success:
            print("✅ 본인인증이 완료되었습니다!")
        else:
            print(f"❌ 인증 실패: {verify_result.message}")

# 실행
asyncio.run(main())
```

## 🔄 Result 객체

모든 메서드는 `Result` 객체를 반환합니다:

```python
@dataclass
class Result:
    status: bool      # 성공/실패 여부
    message: str      # 메시지 (오류 시 오류 메시지)
    error_code: int   # 오류 코드 (성공 시 9999)
    data: Optional[T] # 반환 데이터 (있는 경우)
```

## 📄 라이센스
이 프로젝트는 MIT 라이센스 하에 배포됩니다.

## 📞 연락처
문의사항이 있으시면 sunr1s2@proton.me로 연락해 주세요.

---

⭐ 이 프로젝트가 도움이 되셨다면 Star를 눌러주세요!
