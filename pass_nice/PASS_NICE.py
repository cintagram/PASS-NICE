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

    V2.0.0

    - 기능
        - SMS 본인인증 기능을 지원합니다.
        - MVNO 포함 모든 통신사를 지원합니다.
        - `httpx`를 기반으로 100% 비동기로 작동합니다.
    
    - Notes
        - checkplusData 형식은 NICE아이디 사용하는 거의 모든 업체가 동일합니다.
        - 따라서, 다른 요청업체 엔드포인트만 따서 checkplusDataRequest URL을 바꾸시면 대부분 동작합니다.
    """

    def __init__(self, cellCorp: Literal["SK", "KT", "LG", "SM", "KM", "LM"], proxy: Optional[str] = None):
        """
        파라미터:
            * cellCorp (str): 인증 요청 대상자의 통신사
            * proxy (str, optional): 프록시 URL (Ex: "http://host:port" 또는 "http://user:pass@host:port")
        
        Raises:
            ValidationError: 지원하지 않는 통신사 코드가 전달된 경우
        """
        if cellCorp not in ["SK", "KT", "LG", "SM", "KM", "LM"]:
            raise ValidationError(f"지원하지 않는 통신사입니다: {cellCorp}")
            
        self.client = httpx.AsyncClient(proxy=proxy, timeout=30.0)
        self.cell_corp = cellCorp
        self._is_initialized = False

        self._host_isp_mapping = {
            "SK": "COMMON_MOBILE_SKT",
            "SM": "COMMON_MOBILE_SKT", 
            "KT": "COMMON_MOBILE_KT",
            "KM": "COMMON_MOBILE_KT",
            "LG": "COMMON_MOBILE_LGU",
            "LM": "COMMON_MOBILE_LGU"
        }
        
        self._auth_type = "SMS" # TODO: add pass app verification

    async def init_session(self) -> Result:
        """
        현재 클래스의 세션을 초기화합니다.
        해당 과정 없이 인증을 진행할 수 없습니다.

        ```
        await <Client>.init_session()
        # -> <Result>
        ```
        """

        if self._is_initialized:
            return Result(False, "이미 초기화된 세션입니다.", 0)

        try:
            checkplusDataRequest = await self.client.get('https://www.ex.co.kr:8070/recruit/company/nice/checkplus_main_company.jsp')
            checkplusData = checkplusDataRequest.text
            
            m_match = re.search(r'name=["\']m["\']\s+value=["\']([^"\'\']+)["\']', checkplusData)
            encode_match = re.search(r'name=["\']EncodeData["\']\s+value=["\']([^"\'\']+)["\']', checkplusData)
            
            if not m_match or not encode_match:
                raise ParseError("요청업체 응답 데이터 파싱에 실패했습니다.")
                
            m = m_match.group(1)
            EncodeData = encode_match.group(1)

            wcCookie = f'{uuid.uuid4()}_T_{random.randint(10000, 99999)}_WC'  
            self.client.cookies.update({'wcCookie': wcCookie})

        except httpx.RequestError as e:
            raise NetworkError(f"요청업체와의 통신에 실패했습니다: {str(e)}", 1)

        try:
            checkplusRequest = await self.client.post('https://nice.checkplus.co.kr/CheckPlusSafeModel/checkplus.cb',
                data={
                    'm': m, 
                    'EncodeData': EncodeData
                }
            )

            service_info_match = re.search(r'const\s+SERVICE_INFO\s*=\s*"([^"]+)"', checkplusRequest.text)
            if not service_info_match:
                raise ParseError("나이스 응답 데이터에서 SERVICE_INFO를 찾을 수 없습니다.")
            self._SERVICE_INFO = service_info_match.group(1)

            mainTracerRequest = await self.client.post('https://nice.checkplus.co.kr/cert/main/tracer',
                data={
                    'accTkInfo': self._SERVICE_INFO
                }
            )
            ip_match = re.search(r'callTracerApiInput\(\s*"[^"]*",\s*"(\d{1,3}(?:\.\d{1,3}){3})",', mainTracerRequest.text)
            if not ip_match:
                raise ParseError("나이스 응답 데이터에서 IP 정보를 찾을 수 없습니다.")
            IP = ip_match.group(1)

        except httpx.RequestError as e:
            raise NetworkError(f"나이스 서버와 통신에 실패했습니다: {str(e)}", 3)

        try:
            await self.client.post('https://nice.checkplus.co.kr/cert/main/menu',
                data={
                    'accTkInfo': self._SERVICE_INFO
                }
            )

            await self.client.post('https://ifc.niceid.co.kr/TRACERAPI/inputQueue.do',
                data = {
                    "host": self._host_isp_mapping.get(self.cell_corp),
                    "ip": IP,
                    "loginId": wcCookie,
                    "port": "80",
                    "pageUrl": "mobile_cert_telecom",
                    "userAgent": ""
                }
            )

        except httpx.RequestError as e:
            raise NetworkError(f"나이스 서버와 통신에 실패했습니다: {str(e)}", 5)
        
        try:
            methodRequest = await self.client.post(
                url = 'https://nice.checkplus.co.kr/cert/mobileCert/method', 
                data = {
                    "accTkInfo": self._SERVICE_INFO,
                    "selectMobileCo": self.cell_corp, 
                    "os": "Windows"
                }
            )

            cert_hash_match = re.search(r'<input\s+type=["\']hidden["\']\s+name=["\']certInfoHash["\']\s+value=["\']([^"\'\']+)["\']>', methodRequest.text)
            if not cert_hash_match:
                raise ParseError("나이스 응답 데이터에서 certInfoHash를 찾을 수 없습니다.")
            certInfoHash = cert_hash_match.group(1)

        except httpx.RequestError as e:
            raise NetworkError(f"나이스 서버와 통신에 실패했습니다: {str(e)}", 7)

        try:
            certProcRequest = await self.client.post(
                url = 'https://nice.checkplus.co.kr/cert/mobileCert/sms/certification',
                data = {
                    "certInfoHash": certInfoHash,
                    "accTkInfo": self._SERVICE_INFO,
                    "mobileCertAgree": "Y"
                }
            )

            captcha_match = re.search(r'const\s+captchaVersion\s*=\s*"([^"]+)"', certProcRequest.text)
            if not captcha_match:
                raise ParseError("나이스 응답 데이터에서 captchaVersion을 찾을 수 없습니다.")
            self._captcha_version = captcha_match.group(1)

        except httpx.RequestError as e:
            raise NetworkError(f"나이스 서버와 통신에 실패했습니다: {str(e)}", 9)

        self._is_initialized = True

        return Result(True, '세션 초기화에 성공했습니다.', 9999)

    async def retrieve_captcha(self) -> Result[bytes]:
        """
        현재 클래스의 초기화된 세션을 기준으로, 인증 요청 전송시에 필요한 캡챠 이미지를 반환합니다.

        Returns:
            Result[bytes]: 성공 시 캡챠 이미지 바이트 데이터를 포함한 Result 객체
            
        Raises:
            SessionNotInitializedError: 세션이 초기화되지 않은 경우
        """ 
        if not self._is_initialized or not hasattr(self, '_captcha_version'):
            raise SessionNotInitializedError("세션이 초기화되지 않았습니다. init_session()을 먼저 호출하세요.")

        try:
            captcha_request = await self.client.get(f'https://nice.checkplus.co.kr/cert/captcha/image/{self._captcha_version}')
            content = captcha_request.content
            
            return Result(True, "캡챠 이미지 확인에 성공했습니다.", 9999, content)
        
        except httpx.RequestError as e:
            raise NetworkError(f"나이스 서버와 통신에 실패했습니다: {str(e)}", 1)

    async def send_sms_verification(
        self, name: str, birthdate: str, gender: Literal[
            "1", "2", "3", "4",  # 내국인
            "5", "6", "7", "8",  # 외국인
        ], phone: str, captcha_answer: str
    ) -> Result:
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

        if not self._is_initialized or not self._captcha_version:
            return Result(False, "해당 함수를 이용하려면 세션 초기화가 필요합니다.", 0)
    
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
                    "myNum1": birthdate,  # TODO: [0:6]이였는데 확인 필요
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
            return Result(False, error_msg, 3)
        
        try:
            smsConfirmRequest = await self.client.post('https://nice.checkplus.co.kr/cert/mobileCert/sms/confirm')
            service_info_match = re.search(r'const\s+SERVICE_INFO\s*=\s*"([^"]+)"', smsConfirmRequest.text)
            if service_info_match:
                self._SERVICE_INFO = service_info_match.group(1)

        except httpx.RequestError as e:
            raise NetworkError(f"나이스 서버와 통신에 실패했습니다: {str(e)}", 4)

        self.name, self.birthdate, self.phone = name, birthdate, phone
        self._is_verify_sent = True

        return Result(True, "휴대폰 본인인증 요청을 성공적으로 전송했습니다.", 9999)

    async def check_sms_verification(self, sms_code: str) -> Result[None]:
        """
        전송된 SMS 코드를 확인합니다.

        Args:
            sms_code: 휴대전화로 전송된 SMS 코드 (6자리)
        
        Returns:
            Result[None]: 성공/실패 결과
            
        Raises:
            SessionNotInitializedError: 세션이 초기화되지 않은 경우
            ValidationError: SMS 코드 형식이 올바르지 않은 경우
        """
        if not self._is_initialized or not hasattr(self, '_captcha_version'):
            raise SessionNotInitializedError("세션이 초기화되지 않았습니다. init_session()을 먼저 호출하세요.")

        if not hasattr(self, '_is_verify_sent') or not self._is_verify_sent:
            return Result(False, "아직 SMS 코드를 전송하지 않았습니다.", 1)

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
            return Result(False, "올바른 인증코드를 입력해주세요.", 4)

        if response_code != "SUCCESS":
            error_msg = response_json.get('message', '인증 확인 도중 문제가 발생하였습니다.')
            return Result(False, error_msg, 5)

        return Result(True, "인증이 완료되었습니다.", 9999)

    async def close(self) -> None:
        """HTTP 클라이언트를 종료합니다."""
        await self.client.aclose()

    async def __aenter__(self):
        """async with 구문 지원"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """async with 구문 지원"""
        await self.close()