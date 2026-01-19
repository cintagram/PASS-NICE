"""
PASS-NICE 타입 정의
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Generic, Literal, Optional, TypeVar

T = TypeVar("T")

@dataclass(frozen=True)
class Result(Generic[T]):
    """API 호출 결과를 나타내는 제네릭 데이터 클래스"""
    status: bool
    message: str
    data: Optional[T] = None
    
    @property
    def success(self) -> bool:
        """성공 여부를 반환"""
        return self.status
    
    @property
    def failed(self) -> bool:
        """실패 여부를 반환"""
        return not self.status
    
    def to_dict(self) -> dict[str, Any]:
        """딕셔너리 형태로 변환 (하위 호환성)"""
        result = {
            "Success": self.status,
            "Message": self.message
        }
        if self.data is not None:
            result["Content"] = self.data
        return result

@dataclass(frozen=True)
class VerificationData():
    """본인인증 데이터를 나타내는 데이터 클래스"""
    name: str
    birthdate: datetime
    gender: Literal["1", "2"] # 남자, 여자
    phone_number: str
    mobile_carrier: Literal["SK", "KT", "LG", "SM", "KM", "LM"]