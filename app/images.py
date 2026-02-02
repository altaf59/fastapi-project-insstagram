from dotenv import load_dotenv
from imagekitio import ImageKit
import os

load_dotenv()  # Load environment variables from .env file

# Initialize ImageKit (SDK 5.x compatible)
imagekit = ImageKit(
    private_key=os.getenv("IMAGEKIT_PRIVATE_KEY"),
    url_endpoint=os.getenv("IMAGEKIT_URL")
)
