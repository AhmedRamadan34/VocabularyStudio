from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import shutil
import os
import asyncio
from video_generator import generate_video
from fastapi.responses import JSONResponse, FileResponse

app = FastAPI()

app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static"
)

templates = Jinja2Templates(directory="templates")

UPLOAD_FOLDER = "uploads"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.get("/")
async def home(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="index.html"
    )

@app.post("/generate")
async def generate(request: Request):

    form = await request.form()
    
    logo = form.get("logo")

    logo_path = ""

    if logo and logo.filename:

        logo_path = os.path.join(
            UPLOAD_FOLDER,
            logo.filename
        )

        with open(logo_path, "wb") as buffer:

            shutil.copyfileobj(
                logo.file,
                buffer
            )

    signature = form.get("signature", "")
    academy = form.get("academy", "")
    voice = form.get(
        "voice",
        "en-US-JennyNeural"
    )

    speed = form.get(
        "speed",
        "+0%"
    )

    count = int(form.get("count", 0))

    print("Signature:", signature)
    print("Academy:", academy)

    words = []

    for i in range(count):

        word = form.get(f"word_{i}")
        arabic = form.get(f"arabic_{i}")

        image = form.get(f"image_{i}")

        image_path = ""

        if image and image.filename:

            image_path = os.path.join(
                UPLOAD_FOLDER,
                image.filename
            )

            with open(image_path, "wb") as buffer:

                shutil.copyfileobj(
                    image.file,
                    buffer
                )

        words.append({

            "word": word,
            "arabic": arabic,
            "image": image_path

        })

    print(words)

    await generate_video(
        words,
        signature,
        academy,
        logo_path,
        voice,
        speed
    )

    return JSONResponse({

        "message": "Video Generated Successfully"

    })

@app.get("/download")
async def download():

    return FileResponse(
        "output/Vocabulary.mp4",
        media_type="video/mp4",
        filename="Vocabulary.mp4"
    )