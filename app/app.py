from fastapi import FastAPI, File, UploadFile, Form, Depends, HTTPException
from app.db import Post, create_async_engine, create_db_and_tables, get_async_session
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager
from sqlalchemy.future import select
from app.images import imagekit
import shutil
import os
import tempfile

# ---------------- App Lifespan (DB tables create karne ke liye) ----------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)

# ------------------- Upload Endpoint -------------------
@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    caption: str = Form(""),
    session: AsyncSession = Depends(get_async_session)
):
    temp_file_path = None
    try:
        # 1️⃣ File extension nikalna
        suffix = os.path.splitext(file.filename)[1]
        
        # 2️⃣ Temporary file create karna
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file_path = temp_file.name
            shutil.copyfileobj(file.file, temp_file)

        # 3️⃣ ImageKit par upload
        with open(temp_file_path, "rb") as image_file:
            upload_result = imagekit.upload_file(
                file=image_file,
                file_name=file.filename,
                options={"use_unique_file_name": True, "tags": ["backend_upload"]}
            )

        # 4️⃣ Check upload status
        if upload_result.response_metadata.http_status_code == 200:
            file_type = "video" if file.content_type.startswith("video/") else "image"

            # 5️⃣ Save in DB
            new_post = Post(
                caption=caption,
                url=upload_result.url,
                file_type=file_type,
                file_name=upload_result.name
            )
            session.add(new_post)
            await session.commit()
            await session.refresh(new_post)
            return new_post

        else:
            raise HTTPException(
                status_code=upload_result.response_metadata.http_status_code,
                detail="Upload failed"
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        # 6️⃣ Cleanup: temp file delete karna
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        file.file.close()

# ------------------- Feed Endpoint -------------------
@app.get("/feed")
async def get_feed(session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(
        select(Post).order_by(Post.created_at.desc())
    )
    posts = [row[0] for row in result.all()]

    posts_data = []
    for post in posts:
        posts_data.append({
            "id": str(post.id),
            "caption": post.caption,
            "url": post.url,
            "file_type": post.file_type,
            "file_name": post.file_name,
            "created_at": post.created_at.isoformat()
        })
    return posts_data
