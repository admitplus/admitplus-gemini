import re
import logging
from typing import Optional
from fastapi import HTTPException


class ValidationUtils:
    """通用验证工具类"""

    @staticmethod
    def validate_email_format(email: str) -> bool:
        """验证邮箱格式"""
        if not email:
            return True  # 允许空邮箱
        try:
            email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
            return bool(re.match(email_pattern, email))
        except Exception as e:
            logging.warning(f"[Validation Utils] Email validation error: {str(e)}")
            return False

    @staticmethod
    def validate_phone_number(phone_number: str) -> bool:
        """验证手机号格式"""
        if not phone_number:
            return True  # 允许空手机号
        try:
            # 支持国际格式的手机号验证
            phone_pattern = r"^[\+]?[1-9][\d]{0,15}$"
            cleaned_phone = (
                phone_number.replace(" ", "")
                .replace("-", "")
                .replace("(", "")
                .replace(")", "")
            )
            return bool(re.match(phone_pattern, cleaned_phone))
        except Exception as e:
            logging.warning(f"[Validation Utils] Phone validation error: {str(e)}")
            return False

    @staticmethod
    def validate_name(name: str, field_name: str, max_length: int = 100) -> bool:
        """验证姓名格式"""
        if not name:
            return True  # 允许空姓名

        name = name.strip()
        if len(name) < 1:
            raise HTTPException(status_code=400, detail=f"{field_name} cannot be empty")

        if len(name) > max_length:
            raise HTTPException(
                status_code=400,
                detail=f"{field_name} is too long (max {max_length} characters)",
            )

        return True

    @staticmethod
    def validate_string_length(
        value: str, field_name: str, max_length: int = 255, min_length: int = 0
    ) -> bool:
        """验证字符串长度"""
        if not value:
            return True  # 允许空值

        if len(value) < min_length:
            raise HTTPException(
                status_code=400,
                detail=f"{field_name} is too short (min {min_length} characters)",
            )

        if len(value) > max_length:
            raise HTTPException(
                status_code=400,
                detail=f"{field_name} is too long (max {max_length} characters)",
            )

        return True

    @staticmethod
    def validate_email_duplicate(
        email: str, existing_email: Optional[str] = None
    ) -> bool:
        """验证邮箱是否重复"""
        if not email or email == existing_email:
            return True  # 允许空邮箱或相同邮箱

        # 这里可以添加数据库查询逻辑来检查重复
        # 暂时返回 True，实际实现时需要查询数据库
        return True

    @staticmethod
    def validate_phone_duplicate(
        phone_number: str, existing_phone: Optional[str] = None
    ) -> bool:
        """验证手机号是否重复"""
        if not phone_number or phone_number == existing_phone:
            return True  # 允许空手机号或相同手机号

        # 这里可以添加数据库查询逻辑来检查重复
        # 暂时返回 True，实际实现时需要查询数据库
        return True
