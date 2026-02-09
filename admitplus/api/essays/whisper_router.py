"""
Whisper语音识别代理路由
将前端上传的音频文件转发到Whisper子服务进行语音转文字处理
"""

import logging
import os
from typing import Optional, Dict, Any
import requests
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from admitplus.dependencies.role_check import get_current_user
from admitplus.common.response_schema import Response

# 配置日志
logger = logging.getLogger(__name__)


class TranscriptionResponse(BaseModel):
    """转写响应模型"""

    text: str
    language: Optional[str] = None
    duration: Optional[float] = None
    segments: Optional[list] = None


class WhisperHealthResponse(BaseModel):
    """Whisper服务健康检查响应"""

    ok: bool
    model: str
    device: str
    status: str = "ready"


# 创建路由器
router = APIRouter(prefix="/whisper", tags=["语音识别"])

# Whisper服务配置
WHISPER_SERVICE_URL = os.getenv("STT_URL", "http://localhost:8010")
WHISPER_TIMEOUT = int(os.getenv("WHISPER_TIMEOUT", "60"))  # 60秒超时
MAX_FILE_SIZE = 25 * 1024 * 1024  # 25MB
ALLOWED_EXTENSIONS = ["mp3", "wav", "mp4", "webm", "m4a", "ogg"]


def validate_audio_file(file: UploadFile) -> None:
    """验证音频文件"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="请提供文件名")

    # 检查文件大小
    if file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"文件过大，最大允许 {MAX_FILE_SIZE // 1024 // 1024}MB",
        )

    # 检查文件扩展名
    file_ext = file.filename.split(".")[-1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=415,
            detail=f"不支持的文件格式，支持的格式: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # 检查MIME类型
    if file.content_type and not file.content_type.startswith("audio/"):
        logger.warning(f"文件MIME类型: {file.content_type}")


def check_whisper_service() -> bool:
    """检查Whisper服务是否可用"""
    try:
        response = requests.get(f"{WHISPER_SERVICE_URL}/health", timeout=5)
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Whisper服务连接失败: {e}")
        return False


@router.get(
    "/health", response_model=Response[Dict[str, Any]], summary="检查语音识别服务状态"
)
async def check_whisper_health():
    """检查Whisper子服务健康状态"""
    try:
        response = requests.get(f"{WHISPER_SERVICE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return Response(
                code=200,
                message="Whisper service is healthy",
                data={
                    "whisper_service": data,
                    "proxy_status": "ok",
                    "service_url": WHISPER_SERVICE_URL,
                },
            )
        else:
            raise HTTPException(
                status_code=503,
                detail=f"Whisper服务不可用: HTTP {response.status_code}",
            )
    except requests.RequestException as e:
        logger.error(f"无法连接Whisper服务: {e}")
        raise HTTPException(status_code=503, detail=f"无法连接Whisper服务: {str(e)}")
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        raise HTTPException(status_code=500, detail=f"健康检查失败: {str(e)}")


@router.post(
    "/transcribe", response_model=Response[TranscriptionResponse], summary="语音转文字"
)
async def transcribe_audio(
    file: UploadFile = File(..., description="音频文件"),
    language: Optional[str] = Form(None, description="指定语言代码，如 'zh', 'en'"),
    translate: bool = Form(False, description="是否翻译为英文"),
    prompt: Optional[str] = Form(None, description="提示文本"),
    current_user: dict = Depends(get_current_user),
):
    """
    将音频文件转换为文字

    需要用户认证。音频文件会被转发到Whisper子服务进行处理。

    - **files**: 音频文件 (支持格式: mp3, wav, mp4, webm, m4a, ogg)
    - **language**: 可选，指定音频语言
    - **translate**: 可选，是否翻译为英文
    - **prompt**: 可选，提示文本，可以提高特定词汇的识别准确度
    """

    try:
        # 记录用户信息
        user_id = current_user.get("user_id", "unknown")
        logger.info(f"用户 {user_id} 请求语音转文字服务")

        # 验证文件
        validate_audio_file(file)

        # 检查Whisper服务
        if not check_whisper_service():
            raise HTTPException(
                status_code=503, detail="语音识别服务暂时不可用，请稍后重试"
            )

        # 准备转发请求的数据
        files = {"files": (file.filename, file.file, file.content_type)}
        data = {}

        if language:
            data["language"] = language
        if translate:
            data["translate"] = translate
        if prompt:
            data["prompt"] = prompt

        logger.info(
            f"转发音频文件到Whisper服务: {file.filename}, 大小: {file.size} bytes"
        )

        # 转发请求到Whisper服务
        response = requests.post(
            f"{WHISPER_SERVICE_URL}/transcribe",
            files=files,
            data=data,
            timeout=WHISPER_TIMEOUT,
        )

        # 处理响应
        if response.status_code == 200:
            result = response.json()
            logger.info(
                f"用户 {user_id} 语音转文字成功: {len(result.get('text', ''))} 个字符"
            )
            return Response(
                code=200,
                message="Audio transcribed successfully",
                data=TranscriptionResponse(**result),
            )
        else:
            error_msg = f"Whisper服务错误: HTTP {response.status_code}"
            try:
                error_detail = response.json().get("detail", "未知错误")
                error_msg = f"{error_msg} - {error_detail}"
            except:
                pass

            logger.error(f"用户 {user_id} 语音转文字失败: {error_msg}")
            raise HTTPException(status_code=response.status_code, detail=error_msg)

    except HTTPException:
        raise
    except requests.Timeout:
        logger.error(f"用户 {user_id} 语音转文字超时")
        raise HTTPException(
            status_code=408, detail="语音处理超时，请尝试较短的音频文件"
        )
    except requests.RequestException as e:
        logger.error(f"用户 {user_id} 请求Whisper服务失败: {e}")
        raise HTTPException(status_code=503, detail="语音识别服务暂时不可用")
    except Exception as e:
        logger.error(f"用户 {user_id} 语音转文字异常: {e}")
        raise HTTPException(status_code=500, detail="语音转文字处理失败")
    finally:
        # 确保文件流被重置，避免影响后续处理
        try:
            file.file.seek(0)
        except:
            pass


@router.get(
    "/info", response_model=Response[Dict[str, Any]], summary="获取语音识别服务信息"
)
async def get_service_info():
    """获取语音识别服务配置信息"""
    return Response(
        code=200,
        message="Service info retrieved successfully",
        data={
            "service": "语音识别代理",
            "whisper_service_url": WHISPER_SERVICE_URL,
            "timeout": WHISPER_TIMEOUT,
            "max_file_size_mb": MAX_FILE_SIZE // 1024 // 1024,
            "supported_formats": ALLOWED_EXTENSIONS,
            "description": "将音频文件转发到Whisper子服务进行语音转文字处理",
        },
    )
