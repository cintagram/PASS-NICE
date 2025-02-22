# PASS-NICE
[NICE아이디](https://www.niceid.co.kr/index.nc/) 본인인증 요청을 자동화해주는 비공식적인 
모듈입니다.<br>

## 필독
**교육용 및 학습용으로만 사용해 주세요**<br>
이 모듈 혹은 리포지토리를 사용함으로써 발생하는 모든 피해나 손실은 모두 본인의 책임입니다.<br>
해당 레포지토리는 **NICE아이디 및 한국도로교통공사측의 삭제 요청이 있을 경우, 즉시 삭제됩니다.**<br>
Support : Telegram @sunr1s2_0 | Discord @necynice_

## 추가 예정 기능
**PASS 앱 인증, QR코드 인증** 기능이 추가될 예정입니다.

## 사용방법
### Common Informations
기본 반환 형식:
```py
{
    "Success": Boolean,
    "Message": Message (실패시 실패메시지가 반환됩니다.)
}
```
<br>
모든 파라미터는 "string" 타입으로 처리됩니다.

### 클래스 선언
```py
from filename import Verification

verification = Verification("ISP")
```
* ISP 
    * SK (SK텔레콤), KT (KT), LG (LG)
    * SM (SK알뜰폰), KM (KT알뜰폰), LM (LG알뜰폰)

### 세션 초기화
initSession()를 호출하여 세션을 초기화합니다.
```py
await verification.initSession()
```

### 캡챠 이미지 확인
getCaptcha()를 호출하여 캡챠 이미지를 반환받습니다.<br>
Ex (captcha.png에 캡챠 내용을 저장합니다): 
```py
captchaImage = await verification.getCaptcha()
with open('captcha.png', 'wb') as f:
    f.write(captchaImage)
```

### SMS 메시지 전송
sendSmsCode()를 호출하여 SMS 인증 메시지를 전송합니다.
```py
name = "홍길동" # 인증자 성명
birthdate = "0701023" # YYMMDD(성별코드)
phone = "01012345678" # -(하이폰) 없이, 숫자로만 구성되어야 합니다.
captchaCode = 666666 # 캡챠 코드

await verification.sendSmsCode(name, birthdate, phone, captchaCode)
```

### 인증코드 확인
checkSmsCode()를 호출하여 SMS 인증코드를 확인합니다.
```py
smsCode = "123456" # SMS로 전송된 인증 코드 (6자리)

await verification.checkSmsCode(smsCode)
```
