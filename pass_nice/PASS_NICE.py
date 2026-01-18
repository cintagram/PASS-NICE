import re
import random
import uuid
from urllib.parse import quote
from typing import Literal, Optional

import httpx

from .types import Result
from .exceptions import SessionNotInitializedError, NetworkError, ParseError, ValidationError

class PASS_NICE:
    """
    NICE아이디 본인인증 요청을 자동화해주는 비공식적인 모듈입니다. [요청업체: 한국도로교통공사]

    V2.0.1

    - 기능
        - SMS 본인인증 기능을 지원합니다.
        - MVNO 포함 모든 통신사를 지원합니다.
        - `httpx`를 기반으로 100% 비동기로 작동합니다.
    
    - Notes
        - checkplusData 형식은 NICE아이디 사용하는 거의 모든 업체가 동일합니다.
        - 따라서, 다른 요청업체 엔드포인트만 따서 checkplusDataRequest URL을 바꾸시면 대부분 동작합니다.
    """

    def __init__(self, cell_corp: Literal["SK", "KT", "LG", "SM", "KM", "LM"], proxy: Optional[str] = None):
        """
        파라미터:
            * cellCorp (str): 인증 요청 대상자의 통신사
            * proxy (str, optional): 프록시 URL (Ex: "http://host:port" 또는 "http://user:pass@host:port")
        
        """

        self.client = httpx.AsyncClient(proxy=proxy, timeout=30.0)
        self.cell_corp = cell_corp
        self._is_initialized, self._is_verify_sent = False, False

        self._HOST_ISP_MAPPING = {
            "SK": "COMMON_MOBILE_SKT",
            "SM": "COMMON_MOBILE_SKT", 
            "KT": "COMMON_MOBILE_KT",
            "KM": "COMMON_MOBILE_KT",
            "LG": "COMMON_MOBILE_LGU",
            "LM": "COMMON_MOBILE_LGU"
        }
        
        self._AUTH_TYPE: str = ""

    async def init_session(self, auth_type: Literal["sms"]) -> Result[None]: 
        # TODO: Add Pass App / QR Verification
        """
        현재 클래스의 세션을 초기화합니다.
        
        파라미터:
        * auth_type: str

        ```
        await <Client>.init_session()
        # -> <Result>
        ```
        """

        if self._is_initialized:
            return Result(False, "이미 초기화된 세션입니다.")

        try:
            checkplus_data_request = await self.client.get('https://www.ex.co.kr:8070/recruit/company/nice/checkplus_main_company.jsp')
            checkplus_data = checkplus_data_request.text
            
        except httpx.RequestError as e:
            raise NetworkError(f"요청업체와의 통신에 실패했습니다: {str(e)}", 1)

        m = self.parse_html(checkplus_data, "m", "input")
        encode_data = self.parse_html(checkplus_data, "EncodeData", "input")

        wc_cookie = f'{uuid.uuid4()}_T_{random.randint(10000, 99999)}_WC'  
        self.client.cookies.update({'wcCookie': wc_cookie})

        try:
            checkplus_request = await self.client.post(
                'https://nice.checkplus.co.kr/CheckPlusSafeModel/checkplus.cb',
                data={
                    'm': m, 
                    'EncodeData': encode_data
                }
            )

        except httpx.RequestError as e:
            raise NetworkError(f"나이스 서버와 통신에 실패했습니다: {str(e)}", 3)

        self._SERVICE_INFO = self.parse_html(checkplus_request.text, "SERVICE_INFO")

        try:
            await self.client.post(
                'https://nice.checkplus.co.kr/cert/main/menu',
                data={
                    'accTkInfo': self._SERVICE_INFO
                }
            )

            cert_method_request = await self.client.post(
                'https://nice.checkplus.co.kr/cert/mobileCert/method', 
                data={
                    "accTkInfo": self._SERVICE_INFO,
                    "selectMobileCo": self.cell_corp, 
                    "os": "Windows"
                }
            )

        except httpx.RequestError as e:
            raise NetworkError(f"나이스 서버와 통신에 실패했습니다: {str(e)}", 7)

        cert_info_hash = self.parse_html(cert_method_request.text, "certInfoHash", "input")

        try:
            cert_proc_request = await self.client.post(
                url=f'https://nice.checkplus.co.kr/cert/mobileCert/{auth_type}/certification',
                data = {
                    "certInfoHash": cert_info_hash,
                    "accTkInfo": self._SERVICE_INFO,
                    "mobileCertAgree": "Y"
                }
            )

        except httpx.RequestError as e:
            raise NetworkError(f"나이스 서버와 통신에 실패했습니다: {str(e)}", 9)

        self._CAPTCHA_VERSION = self.parse_html(cert_proc_request.text, "captchaVersion")

        self._is_initialized = True

        return Result(True, '세션 초기화에 성공했습니다.')

    async def retrieve_captcha(self) -> Result[bytes]:
        """
        현재 클래스의 초기화된 세션을 기준으로, 인증 요청 전송시에 필요한 캡챠 이미지를 반환합니다.

        Returns:
            Result[bytes]: 성공 시 캡챠 이미지 바이트 데이터를 포함한 Result 객체
            
        Raises:
            SessionNotInitializedError: 세션이 초기화되지 않은 경우
        """ 

        if not self._is_initialized or not hasattr(self, '_CAPTCHA_VERSION'):
            raise SessionNotInitializedError("세션이 초기화되지 않았습니다. init_session()을 먼저 호출하세요.")

        try:
            captcha_request = await self.client.get(f'https://nice.checkplus.co.kr/cert/captcha/image/{self._CAPTCHA_VERSION}')
            content = captcha_request.content
            
        except httpx.RequestError as e:
            raise NetworkError(f"나이스 서버와 통신에 실패했습니다: {str(e)}", 1)

        return Result(True, "캡챠 이미지 확인에 성공했습니다.", content)

    async def send_sms_verification(
        self, name: str, birthdate: str, 
        gender: Literal[
            "1", "2", "3", "4",  # 내국인
            "5", "6", "7", "8",  # 외국인
        ], phone: str, captcha_answer: str
    ) -> Result[None]:
        """
        휴대폰 본인확인 요청을 전송합니다.

        파라미터:
            * name (str): 이름 (홍길동)
            * birthdate (str): 생년월일 (YYMMDD)
            * gender (str): 성별코드 (N) | 주민등록번호상 성별코드를 작성해야 합니다.
            * phone (str): 휴대전화번호 (01012345678) | -(하이폰) 없이 작성해야 합니다.
            * captcha_answer (str): 캡챠 코드 (XXXXXX) | 숫자만 작성해야 합니다.
        
        ```
        await <Client>.send_sms_verification("홍길동", "0001013", "01012345678", "123456")
        -> <Result>
        ```
        """

        if not self._is_initialized or not self._CAPTCHA_VERSION:
            return Result(False, "해당 함수를 이용하려면 세션 초기화가 필요합니다.")
    
        try:
            sms_proc_request = await self.client.post(
                url = 'https://nice.checkplus.co.kr/cert/mobileCert/sms/certification/proc', 
                headers = {
                    "X-Requested-With": "XMLHTTPRequest",
                    "x-service-info": self._SERVICE_INFO
                },
                data = {
                    "userNameEncoding": quote(name),
                    "userName": name,
                    "myNum1": birthdate,
                    "myNum2": gender,
                    "mobileNo": phone,
                    "captchaAnswer": captcha_answer
                }
            )

        except httpx.RequestError as e:
            raise NetworkError(f"나이스 서버와 통신에 실패했습니다: {str(e)}", 1)

        # SMS 전송 성공 여부 확인 (비즈니스 로직 오류는 Result로 반환)
        response_json = sms_proc_request.json()
        if response_json.get('code') != "SUCCESS":
            error_msg = response_json.get('message', '올바른 본인인증 정보를 입력해주세요.')
            return Result(False, error_msg)
        
        try:
            await self.client.post('https://nice.checkplus.co.kr/cert/mobileCert/sms/confirm')

        except httpx.RequestError as e:
            raise NetworkError(f"나이스 서버와 통신에 실패했습니다: {str(e)}", 4)

        self._is_verify_sent = True

        return Result(True, "휴대폰 본인인증 요청을 성공적으로 전송했습니다.")

    async def check_sms_verification(self, sms_code: str) -> Result[None]:
        """
        전송된 SMS 코드를 확인합니다.

        Args:
            sms_code: 휴대전화로 전송된 SMS 코드 (6자리)
        
        Returns:
            Result[None]: 성공/실패 결과
            
        Raises:
            SessionNotInitializedError: 세션이 올바르게 초기화되지 않은 경우
            ValidationError: SMS 코드 형식이 올바르지 않은 경우
        """
        if not self._is_initialized or not hasattr(self, '_CAPTCHA_VERSION'):
            raise SessionNotInitializedError("세션이 정상적으로 초기화되지 않았습니다.")

        if not self._is_verify_sent:
            return Result(False, "아직 인증을 진행하지 않았습니다.")

        # SMS 코드 검증
        if not sms_code.strip() or len(sms_code) != 6 or not sms_code.isdigit():
            raise ValidationError("SMS 코드는 6자리 숫자여야 합니다.")

        try:
            sms_confirm_request = await self.client.post(
                url='https://nice.checkplus.co.kr/cert/mobileCert/sms/confirm/proc',
                headers={
                    "X-Requested-With": "XMLHTTPRequest",
                    "x-service-info": self._SERVICE_INFO
                },
                data={
                    "certCode": sms_code
                }
            )
            
        except httpx.RequestError as e:
            raise NetworkError(f"나이스 서버와 통신에 실패했습니다: {str(e)}", 2)

        try:
            response_json = sms_confirm_request.json()
            response_code = response_json.get('code')
        except (KeyError, ValueError) as e:
            raise ParseError(f"나이스 응답 데이터 파싱에 실패했습니다: {str(e)}", 3)

        if response_code == "RETRY":
            return Result(False, "올바른 인증코드를 입력해주세요.")

        if response_code != "SUCCESS":
            error_msg = response_json.get('message', '인증 확인 도중 문제가 발생하였습니다.')
            return Result(False, error_msg)

        return Result(True, "본인인증이 완료되었습니다.")

    # ----- helper ----- #
    @staticmethod
    def parse_html(html: str, var_name: str, parse_type: Literal["const", "input"] = "const") -> str:
        if parse_type == "const":
            pattern = rf'const\s+{var_name}\s*=\s*"([^"]+)"'
        
        else:
            pattern = rf'<input\s+type=["\']hidden["\']\s+name=["\']{var_name}["\']\s+value=["\']([^"\'\']+)["\']>'

        match = re.search(pattern, html)
        if not match:
            raise ParseError(f"{var_name} 데이터 파싱에 실패했습니다.")
        
        return match.group(1)

    # ----- context manager ----- #
    async def close(self) -> None:
        """HTTP 클라이언트를 종료합니다."""
        await self.client.aclose()

    async def __aenter__(self):
        """async with 구문 지원"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """async with 구문 지원"""
        await self.close()