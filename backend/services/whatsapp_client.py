import httpx
import asyncio
import random
from typing import Optional
from config import settings


class WhatsAppClient:
    def __init__(self, config=None):
        self.config = config or settings
        self.base_url = f"{self.config.WHATSAPP_BASE_URL}/{self.config.WHATSAPP_API_VERSION}"
        self.headers = {
            "Authorization": f"Bearer {self.config.WHATSAPP_ACCESS_TOKEN}",
            "Content-Type": "application/json",
        }

    def _get_phone_id(self, phone_number_id: Optional[str] = None) -> str:
        return phone_number_id or self.config.WHATSAPP_PHONE_NUMBER_ID

    async def _request(self, method: str, endpoint: str, data: dict = None) -> dict:
        url = f"{self.base_url}/{endpoint}"
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(method, url, headers=self.headers, json=data)
            response.raise_for_status()
            return response.json()

    async def send_message(self, to: str, message_type: str, content: dict, phone_number_id: Optional[str] = None) -> dict:
        phone_id = self._get_phone_id(phone_number_id)
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": message_type,
            message_type: content,
        }
        return await self._request("POST", f"{phone_id}/messages", payload)

    async def send_text(self, to: str, text: str, phone_number_id: Optional[str] = None) -> dict:
        return await self.send_message(to, "text", {"preview_url": False, "body": text}, phone_number_id)

    async def send_template(self, to: str, template_name: str, language_code: str = "hi", components: list = None, phone_number_id: Optional[str] = None) -> dict:
        template_data = {
            "name": template_name,
            "language": {"code": language_code},
        }
        if components:
            template_data["components"] = components
        return await self.send_message(to, "template", template_data, phone_number_id)

    async def send_image(self, to: str, image_id: str, caption: Optional[str] = None, phone_number_id: Optional[str] = None) -> dict:
        content = {"id": image_id}
        if caption:
            content["caption"] = caption
        return await self.send_message(to, "image", content, phone_number_id)

    async def send_audio(self, to: str, audio_id: str, phone_number_id: Optional[str] = None) -> dict:
        return await self.send_message(to, "audio", {"id": audio_id}, phone_number_id)

    async def send_video(self, to: str, video_id: str, caption: Optional[str] = None, phone_number_id: Optional[str] = None) -> dict:
        content = {"id": video_id}
        if caption:
            content["caption"] = caption
        return await self.send_message(to, "video", content, phone_number_id)

    async def send_document(self, to: str, document_id: str, caption: Optional[str] = None, phone_number_id: Optional[str] = None) -> dict:
        content = {"id": document_id}
        if caption:
            content["caption"] = caption
        return await self.send_message(to, "document", content, phone_number_id)

    async def send_location(self, to: str, latitude: float, longitude: float, name: Optional[str] = None, address: Optional[str] = None, phone_number_id: Optional[str] = None) -> dict:
        content = {"latitude": latitude, "longitude": longitude}
        if name:
            content["name"] = name
        if address:
            content["address"] = address
        return await self.send_message(to, "location", content, phone_number_id)

    async def send_sticker(self, to: str, sticker_id: str, phone_number_id: Optional[str] = None) -> dict:
        return await self.send_message(to, "sticker", {"id": sticker_id}, phone_number_id)

    async def send_interactive_buttons(self, to: str, text: str, buttons: list, phone_number_id: Optional[str] = None) -> dict:
        content = {
            "type": "button",
            "body": {"text": text},
            "action": {"buttons": buttons},
        }
        return await self.send_message(to, "interactive", content, phone_number_id)

    async def send_interactive_list(self, to: str, title: str, body: str, button_text: str, sections: list, phone_number_id: Optional[str] = None) -> dict:
        content = {
            "type": "list",
            "header": {"type": "text", "text": title},
            "body": {"text": body},
            "action": {"button": button_text, "sections": sections},
        }
        return await self.send_message(to, "interactive", content, phone_number_id)

    async def download_media(self, media_id: str) -> bytes:
        url_info = await self.get_media_url(media_id)
        media_url = url_info.get("url")
        if not media_url:
            raise ValueError("Media URL nahi mila")
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(media_url, headers={"Authorization": f"Bearer {self.config.WHATSAPP_ACCESS_TOKEN}"})
            response.raise_for_status()
            return response.content

    async def get_media_url(self, media_id: str) -> dict:
        return await self._request("GET", f"{media_id}")

    async def mark_as_read(self, message_id: str) -> dict:
        phone_id = self._get_phone_id()
        return await self._request("POST", f"{phone_id}/messages", {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id,
        })

    async def send_typing_indicator(self, to: str, phone_number_id: Optional[str] = None) -> dict:
        """Send typing indicator via Cloud API presence endpoint."""
        phone_id = self._get_phone_id(phone_number_id)
        return await self._request("POST", f"{phone_id}/presence", {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "presence": "composing",
        })

    async def get_business_profile(self, phone_number_id: Optional[str] = None) -> dict:
        phone_id = self._get_phone_id(phone_number_id)
        return await self._request("GET", f"{phone_id}/whatsapp_business_profile")
