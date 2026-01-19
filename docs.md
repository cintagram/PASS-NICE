# PASS_NICE v2.0.1
>  NICE신용평가의 휴대폰본인인증을 자동화시킨 비공식적인 파이썬 모듈입니다.

해당 문서에서는, 이 모듈의 기본적인 기능과 사용법, 예제를 간단히 소개합니다.

## 기본 기능
이 모듈은 NICE신용평가의 휴대폰 본인인증 시스템을 자동화시킨 모듈입니다.

작동 Flow:
```
객체 생성 -> init_session('method') -> send_xxx_verification(**verify_info) -> check_xxx_verification()
```

지원되는 본인인증 방식은 다음과 같습니다.
- `SMS` 본인인증
- `PASS 앱 QR` 본인인증
- `PASS 앱 알림` 본인인증

본인인증을 끝낸 후 확인할 수 있는 정보는 다음과 같습니다.
- 이름
- 생년월일
- 성별
- 휴대전화번호
- 통신사

인증 후에는 해당 정보들이 포함된 `VerificationData`가 `Result`에 `data`로 반환됩니다.

## 설치
이 모듈은 Python 3.8+을 지원합니다. 또한, `uv`를 이용하시면 간편하게 환경을 설정하실 수 있습니다.
```bash
>>> python -m pip install pass_nice
```

## 사용 예제
### 공통 (객체 생성 및 세션 초기화)
```python
import asyncio

from pass_nice import PASS_NICE
from pass_nice.exceptions import ValidationError, NetworkError

async def main():
    pass_nice = PASS_NICE("carrier") # SK, KT, LG, SM, KM, LM

    await pass_nice.init_session("method") # sms, app_push, app_qr
    # -> <Result>
```

### 인증 전송
- 만약 `SMS`나 `PASS 앱 알림` 본인인증을 전송하고 싶으시다면:
```python
    captcha_result = await pass_nice.retrieve_captcha()
    if not captcha_result.status:
        raise Exception("자동화방지 코드를 확인하던 중 오류가 발생했습니다.")
    
    with open("captcha.png", "wb") as f:
        f.write(captcha_result.data)
    
    captcha_answer = input(": ")

    verify_data = {
        "name": "",             # 이름
        "birthdate": "010203",  # 주민등록번호 앞 6자리
        "gender": "3",          # 주민등록번호 7자리 성별코드
        "phone": "01012345678", # 휴대전화번호 (11자리 혹은 13자리, 하이폰 포함 가능)
        "captcha_answer": captcha_answer
    }
    try:  
        send_result = await pass_nice.send_sms_verification(**verify_data) 
        # 앱 알림은 send_push_verification()을 호출해 주세요. (파라미터가 일부 다릅니다.)
    
    except ValidationError:
        raise Exception("올바르지 않은 데이터가 입력되었습니다.")
    
    if not send_result.status:
        raise Exception(send_result.message)
```

- 만약 `PASS 앱 QR` 본인인증 QR코드/번호를 확인하고 싶으시다면:
```python
    try:
        send_result = await pass_nice.create_qr_verification() # QR 코드 인증은 데이터를 입력받지 않습니다.

    except NetworkError:
        raise Exception("네트워크 에러가 발생했습니다.")

    with open('qr_code.png', 'wb') as f:
        f.write(send_result.data)
    
    # QR코드 번호는 Result.message로 반환됩니다.
    print(f"qr_number: {send_result.message}")
```

### 인증 확인 및 본인인증 데이터 수신
- `PASS 앱 알림`, `PASS 앱 QR` 인증 방식에서 확인하시려면:
```python
    result = None

    while True:
        result = await pass_nice.check_push_verification()
        # QR 인증은 check_qr_verification()을 호출해 주세요. (로직 자체는 동일합니다.)
        if result.status == True:
            break

        await asyncio.sleep(1) 
        # 서버에서 결과값을 폴링하는 방식이기에 적절한 인터벌을 두고 확인해야 합니다.
    
```

- `SMS` 인증 방식에서 확인하시려면:
```python
    otp = input(": ")

    result = await pass_nice.check_sms_verification(sms_code=otp)

    if not send_result.status:
        raise Exception(send_result.message) 
```

인증이 확인된 후, `result.data`에서 반환된 `VerificationData`를 확인하셔서 이후 프로세스를 진행하시면 됩니다.