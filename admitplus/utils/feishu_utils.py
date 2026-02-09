import logging
import traceback
from typing import Dict, Any
from datetime import datetime

import httpx

from admitplus.config import settings


async def notify_feishu(feedback: Dict[str, Any]) -> None:
    webhook_url = settings.FEISHU_WEBHOOK_URL

    if not webhook_url:
        logging.warning(
            "[FeishuUtils] [NotifyFeishu] FEISHU_WEBHOOK_URL not configured, skipping notification"
        )
        return

    try:
        created_at = feedback.get("created_at")
        if isinstance(created_at, datetime):
            created_at_str = created_at.strftime("%Y-%m-%d %H:%M:%S")
        else:
            created_at_str = str(created_at)

        message_content = feedback.get("content", "N/A")

        payload = {
            "msg_type": "text",
            "content": {"text": message_content, "created_at": created_at_str},
        }

        logging.info(
            f"[FeishuUtils] [NotifyFeishu] Sending notification for feedback: {feedback.get('feedback_id')}"
        )
        logging.debug(f"[FeishuUtils] [NotifyFeishu] Payload: {payload}")

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                webhook_url, json=payload, headers={"Content-Type": "application/json"}
            )

            logging.debug(
                f"[FeishuUtils] [NotifyFeishu] Response status: {response.status_code}, Response body: {response.text[:200]}"
            )

            if response.status_code == 200:
                result = response.json()
                if result.get("code") == 0:
                    logging.info(
                        f"[FeishuUtils] [NotifyFeishu] Successfully sent notification to Feishu for feedback: {feedback.get('feedback_id')}"
                    )
                else:
                    logging.warning(
                        f"[FeishuUtils] [NotifyFeishu] Feishu API returned error - "
                        f"Code: {result.get('code')}, Msg: {result.get('msg')}"
                    )
            else:
                logging.error(
                    f"[FeishuUtils] [NotifyFeishu] HTTP error - "
                    f"Status: {response.status_code}, Response: {response.text[:200]}"
                )

    except httpx.TimeoutException:
        logging.error(
            f"[FeishuUtils] [NotifyFeishu] Request timeout when sending to Feishu webhook"
        )
    except Exception as e:
        logging.error(
            f"[FeishuUtils] [NotifyFeishu] Error sending notification to Feishu: {str(e)}"
        )
        logging.error(
            f"[FeishuUtils] [NotifyFeishu] Traceback: {traceback.format_exc()}"
        )
