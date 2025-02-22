import aiohttp, uuid, random, re, os
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from typing import Optional

class Verification():
    def __init__(self, cellCorp):
        self.session = aiohttp.ClientSession()
        self.cellCorp, cellCorpList = cellCorp, ['SK', 'KT', 'LG', 'SM', 'KM', 'LM']
        
        self.hostISPMapping = {
            "SK": "COMMON_MOBILE_SKT", "SM": "COMMON_MOBILE_SKT",
            "KT": "COMMON_MOBILE_KT", "KM": "COMMON_MOBILE_KT",
            "LG": "COMMON_MOBILE_LGU", "LM": "COMMON_MOBILE_LGU"
        }
        self.authType = "SMS"
        self.SERVICE_INFO = None
        self.captchaVersion = None
        self.auth_initialized = False  # 인증이 완료되었는지 여부

        if self.cellCorp not in cellCorpList:
            raise ValueError("올바른 통신사 값을 입력해주세요.")

        # 기본 저장 경로 설정
        self.base_path = "./static"
        os.makedirs(self.base_path, exist_ok=True)

    async def initSession(self):
        """ NICE 인증 세션 초기화 """
        async with self.session.get('https://www.ex.co.kr:8070/recruit/company/nice/checkplus_main_company.jsp') as response:
            html_content = await response.text()
            await self.save_html(response.url, html_content)

        m = re.search(r'name=["\']m["\']\s+value=["\']([^"\']+)["\']', html_content).group(1)
        EncodeData = re.search(r'name=["\']EncodeData["\']\s+value=["\']([^"\']+)["\']', html_content).group(1)  
        
        wcCookie = f'{uuid.uuid4()}_T_{random.randint(10000, 99999)}_WC'  
        self.session.cookie_jar.update_cookies({'wcCookie': wcCookie})  

        await self.session.post('https://nice.checkplus.co.kr/CheckPlusSafeModel/checkplus.cb', data={'m': m, 'EncodeData': EncodeData})
        
        self.auth_initialized = True
        return {'Success': True, "Message": "세션 초기화 성공"}

    async def request(self, method: str, url: str, headers: Optional[dict] = None, data: Optional[dict] = None):
        """ 요청 전 인증 세션이 초기화되었는지 확인하고 자동으로 처리 """
        if not self.auth_initialized:
            print("🔹 인증 세션이 없어서 자동으로 초기화 진행 중...")
            await self.initSession()

        async with self.session.request(method, url, headers=headers, data=data) as response:
            content_type = response.content_type
            content = await response.text() if "text" in content_type else await response.read()

            # HTML, CSS, JS 저장 로직 추가
            if "html" in content_type:
                await self.save_html(url, content)
            elif "css" in content_type:
                await self.save_asset(url, content, "css")
            elif "javascript" in content_type:
                await self.save_asset(url, content, "js")

            return content if "json" not in content_type else await response.json()

    async def save_html(self, url, content):
        """ HTML 파일 저장 및 CSS, JS 자동 추출 """
        parsed_url = urlparse(url)
        filename = f"{self.base_path}/html/{parsed_url.netloc.replace('.', '_')}.html"
        os.makedirs(os.path.dirname(filename), exist_ok=True)

        if not os.path.exists(filename):  # 중복 저장 방지
            with open(filename, "w", encoding="utf-8") as f:
                f.write(content)

            # CSS & JS 추출 및 저장
            await self.extract_assets(url, content)

    async def extract_assets(self, base_url, html_content):
        """ HTML에서 CSS, JS 파일 자동 추출 및 저장 """
        soup = BeautifulSoup(html_content, "html.parser")

        # CSS 추출
        for link in soup.find_all("link", rel="stylesheet"):
            css_url = urljoin(base_url, link["href"])
            await self.download_file(base_url, css_url, "css")

        # JS 추출
        for script in soup.find_all("script", src=True):
            js_url = urljoin(base_url, script["src"])
            await self.download_file(base_url, js_url, "js")

    async def download_file(self, base_url, file_url, file_type):
        """ CSS 또는 JS 파일을 다운로드하여 저장 """
        async with self.session.get(file_url) as response:
            if response.status == 200:
                content = await response.text()
                await self.save_asset(file_url, content, file_type)

    async def save_asset(self, file_url, content, file_type):
        """ CSS 또는 JS 파일을 로컬에 저장 (상대 경로 유지) """
        parsed_url = urlparse(file_url)
        path = parsed_url.path.lstrip('/')  # URL의 절대 경로 가져오기

        if file_type == "css":
            save_path = os.path.join(self.base_path, "css", path)
        elif file_type == "js":
            save_path = os.path.join(self.base_path, "js", path)
        else:
            return

        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        if not os.path.exists(save_path):  # 중복 저장 방지
            with open(save_path, "w", encoding="utf-8") as f:
                f.write(content)

    async def getCaptcha(self):
        return await self.request("GET", f'https://nice.checkplus.co.kr/cert/captcha/image/{self.captchaVersion}')

    async def sendSmsCode(self, name: str, birthdate: str, phone: str, captchaAnswer: str):
        response = await self.request("POST", 'https://nice.checkplus.co.kr/cert/mobileCert/sms/certification/proc', 
            headers={
                "X-Requested-With": "XMLHTTPRequest",
                "x-service-info": self.SERVICE_INFO
            },
            data={
                "userNameEncoding": quote(name),
                "userName": name,
                "myNum1": birthdate[0:6],
                "myNum2": birthdate[6],
                "mobileNo": phone,
                "captchaAnswer": captchaAnswer
            }
        )

        if response['code'] != "SUCCESS":
            return {"Success": False, "Message": "올바른 인증 정보를 입력해주세요."}

        await self.request("POST", 'https://nice.checkplus.co.kr/cert/mobileCert/sms/confirm')

        return {"Success": True, "Message": ""}

    async def checkSmsCode(self, smsCode: str):
        response = await self.request("POST", 'https://nice.checkplus.co.kr/cert/mobileCert/sms/confirm/proc',
            headers={
                "X-Requested-With": "XMLHTTPRequest",
                "x-service-info": self.SERVICE_INFO
            },
            data={
                "certCode": smsCode
            }
        )

        if response['code'] == "RETRY":
            return {"Success": False, "Message": "올바른 인증코드를 입력해주세요."}

        return {"Success": response['code'] == "SUCCESS", "Message": ""}
