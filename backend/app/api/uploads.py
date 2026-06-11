from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from app.core.config import settings
from app.core.deps import get_current_user
from app.models.models import User

router = APIRouter()


@router.get("/{user_id}/{year_month}/{filename}")
async def serve_upload(
    user_id: str,
    year_month: str,
    filename: str,
    current_user: User = Depends(get_current_user),
):
    # Ensure the file belongs to the current user
    if user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")

    file_path = Path(settings.UPLOAD_PATH) / user_id / year_month / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(str(file_path), media_type="image/jpeg")
