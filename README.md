\# FastAPI Instagram Project



This is a FastAPI project for uploading images and videos using ImageKit.  

It includes authentication, user registration, and feed endpoints.



\## Features

\- User authentication (JWT)

\- Image and video upload

\- Feed with posts

\- Delete posts

\- Async database using SQLAlchemy



\## Setup

1\. Clone the repo

2\. Create virtual environment: `python -m venv .venv`

3\. Install requirements: `pip install -r requirements.txt`

4\. Add `.env` file with keys:

&nbsp;  - IMAGEKIT\_PRIVATE\_KEY

&nbsp;  - IMAGEKIT\_PUBLIC\_KEY

&nbsp;  - IMAGEKIT\_URL\_ENDPOINT

5\. Run server: `uvicorn main:app --reload`



