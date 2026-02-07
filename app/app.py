from fastapi import FastAPI, File, UploadFile, Form, Depends, HTTPException
from app.schema import UserRead, UserCreate, UserUpdate
from app.db import Post, create_db_and_tables, get_async_session, User
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager
from sqlalchemy.future import select
from app.images import imagekit
from app.users import auth_backend, fastapi_users, current_active_user
import shutil
import os
import tempfile
import uuid

# ------------------- App Lifespan -------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)

# ------------------- Auth Routes -------------------
app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"],
)

app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)

app.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="/auth",
    tags=["auth"],
)

app.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"],
)

# ------------------- Upload Endpoint -------------------
@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    caption: str = Form(""),
    user: User = Depends(current_active_user), # Yeh line route ko protect karti hai
    session: AsyncSession = Depends(get_async_session),
):

    temp_file_path = None
    try:
        suffix = os.path.splitext(file.filename)[1] if file.filename else ""
        print(f"Uploading file: {file.filename}, type: {file.content_type}")

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file_path = temp_file.name
            shutil.copyfileobj(file.file, temp_file)

        print(f"Temp file created at: {temp_file_path}")

        with open(temp_file_path, "rb") as image_file:
            upload_result = imagekit.files.upload(
                file=image_file,
                file_name=file.filename or f"upload_{uuid.uuid4()}",
                use_unique_file_name=True,
                tags=["backend_upload"]
            )

        print(f"ImageKit upload successful: {upload_result.url}")

        content_type = file.content_type or ""
        file_type = "video" if content_type.startswith("video/") else "image"

        new_post = Post(
            user_id=user.id,
            caption=caption,
            url=upload_result.url,
            file_type=file_type,
            file_name=upload_result.name,
        )

        session.add(new_post)
        await session.commit()
        await session.refresh(new_post)
        print(f"Post saved to DB: {new_post.id}")
        return new_post

    except Exception as e:
        print(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        file.file.close()

# ------------------- Feed Endpoint -------------------
@app.get("/feed")
async def get_feed(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user)
):
    try:
        # Join with User table to get author emails
        result = await session.execute(
            select(Post, User)
            .join(User, Post.user_id == User.id)
            .order_by(Post.created_at.desc())
        )
        
        posts_with_users = result.all()
        
        feed_data = []
        for post, author in posts_with_users:
            feed_data.append({
                "id": post.id,
                "user_id": str(post.user_id),
                "caption": post.caption,
                "url": post.url,
                "file_type": post.file_type,
                "file_name": post.file_name,
                "created_at": post.created_at.isoformat(),
                "is_owner": post.user_id == current_user.id,
                "email": author.email  # Author's email
            })
            
        return {"posts": feed_data}
        
    except Exception as e:
        print(f"Feed load error: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# ------------------- Delete Post -------------------
@app.delete("/posts/{post_id}")
async def delete_post(
    post_id: str,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user)
):
    result = await session.execute(
        select(Post).where(
            Post.id == post_id,
            Post.user_id == user.id
        )
    )

    post = result.scalars().first()

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if post.user_id != user.id:
        raise HTTPException(status_code=403, detail="You are not authorized to delete this post")


    await session.delete(post)
    await session.commit()

    return {"success": True, "message": "Post deleted successfully"}
