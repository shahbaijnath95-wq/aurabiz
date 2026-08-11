import os
import uuid
from typing import Optional
from pathlib import Path


class MediaHandler:
    def __init__(self, whatsapp_client=None):
        self.whatsapp_client = whatsapp_client
        self.media_dir = Path("media")
        self.media_dir.mkdir(exist_ok=True)

    async def download_media(self, media_id: str) -> bytes:
        if not self.whatsapp_client:
            raise ValueError("WhatsApp client configured nahi hai")
        return await self.whatsapp_client.download_media(media_id)

    async def upload_media(self, file_data: bytes, media_type: str) -> dict:
        filename = f"{uuid.uuid4()}.{media_type}"
        file_path = self.media_dir / filename
        file_path.write_bytes(file_data)
        return {"file_path": str(file_path), "filename": filename, "size": len(file_data)}

    async def process_incoming_media(self, message: dict) -> dict:
        media = message.get("media", {})
        media_id = media.get("id")
        media_type = media.get("type", "unknown")

        if media_id and self.whatsapp_client:
            file_data = await self.download_media(media_id)
            result = await self.upload_media(file_data, media_type)
            return {
                "media_id": media_id,
                "media_type": media_type,
                "mime_type": media.get("mime_type"),
                "file_path": result["file_path"],
                "size": result["size"],
            }
        return {"media_type": media_type, "error": "Media download failed"}

    async def get_media_type(self, file_data: bytes) -> str:
        if file_data[:8] == b'\x89PNG\r\n\x1a\n':
            return "image"
        if file_data[:3] == b'\xff\xd8\xff':
            return "image"
        if file_data[:4] == b'RIFF' and file_data[8:12] == b'WEBP':
            return "image"
        if file_data[:4] == b'RIFF':
            return "audio"  # WAV
        if file_data[:4] == b'OggS':
            return "audio"  # OGG/Opus (WhatsApp voice messages)
        if file_data[:4] == b'\x1a\x45\xdf\xa3':
            return "video"  # Matroska/WebM
        if file_data[:3] == b'ID3' or file_data[:2] == b'\xff\xfb':
            return "audio"  # MP3
        if file_data[:4] == b'ftyp' or file_data[4:8] == b'ftyp':
            return "video"  # MP4/MOV
        return "document"

    async def store_media_locally(self, media_data: bytes, business_id: str) -> str:
        business_dir = self.media_dir / business_id
        business_dir.mkdir(exist_ok=True)
        filename = f"{uuid.uuid4()}"
        file_path = business_dir / filename
        file_path.write_bytes(media_data)
        return str(file_path)

    async def cleanup_old_media(self, max_age_days: int = 30) -> int:
        import time
        count = 0
        cutoff = time.time() - (max_age_days * 86400)
        for file_path in self.media_dir.rglob("*"):
            if file_path.is_file() and file_path.stat().st_mtime < cutoff:
                file_path.unlink()
                count += 1
        return count
