import os
import asyncio
import edge_tts
import arabic_reshaper
import uuid
import gc

from bidi.algorithm import get_display

from moviepy import (
    ImageClip,
    TextClip,
    AudioFileClip,
    CompositeVideoClip,
    concatenate_videoclips
)

WIDTH = 540
HEIGHT = 960

VOICE = "en-US-JennyNeural"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

FONT = os.path.join(BASE_DIR, "fonts", "tahoma.ttf")
print("FONT =", FONT)
print("FONT EXISTS =", os.path.exists(FONT))

OUTPUT_FOLDER = os.path.join(BASE_DIR, "output")
TEMP_FOLDER = os.path.join(BASE_DIR, "temp")

os.makedirs(TEMP_FOLDER, exist_ok=True)


def fix_arabic(text):

    if not text:
        return ""

    reshaped = arabic_reshaper.reshape(str(text))

    return get_display(reshaped)


async def make_audio(
    text,
    filename,
    voice,
    speed
):

    communicate = edge_tts.Communicate(
        text=text,
        voice=voice,
        rate=speed
    )

    await communicate.save(filename)


def create_clip(
    word,
    arabic,
    image_path,
    audio_file,
    signature,
    academy,
    logo_path
):

    audio = AudioFileClip(audio_file)

    bg = (
        ImageClip(image_path)
        .resized((WIDTH, HEIGHT))
        .with_duration(audio.duration + 1)
    )

    english = (
        TextClip(
            text=word,
            font=FONT,
            font_size=90,
            color="white",
            stroke_color="black",
            stroke_width=3
        )
        .with_position(("center", 700))
        .with_duration(audio.duration + 1)
    )

    clips = [bg, english]

    if arabic:

        arabic = fix_arabic(arabic)

        arabic_clip = (
            TextClip(
                text=arabic,
                font=FONT,
                font_size=60,
                color="yellow",
                stroke_color="black",
                stroke_width=2
            )
            .with_position(("center", 770))
            .with_duration(audio.duration + 1)
        )

        clips.append(arabic_clip)

    if signature:

        signature_clip = (
            TextClip(
                text=signature,
                font=FONT,
                font_size=18,
                color="white",
                stroke_color="black",
                stroke_width=1,
                size=(420, None),
                method="caption"
            )
            .with_position((100, HEIGHT - 92))
            .with_duration(audio.duration + 1)
        )

        clips.append(signature_clip)

    if academy:

        academy_clip = (
            TextClip(
                text=academy,
                font=FONT,
                font_size=15,
                color="#d9d9d9",
                stroke_color="black",
                stroke_width=1,
                size=(420, None),
                method="caption"
            )
            .with_position((100, HEIGHT - 65))
            .with_duration(audio.duration + 1)
        )

        clips.append(academy_clip)

    if logo_path and os.path.exists(logo_path):

        logo = (
            ImageClip(logo_path)
            .resized(width=70)
            .with_position((20, HEIGHT - 105))
            .with_duration(audio.duration + 1)
        )

        clips.append(logo)

    video = CompositeVideoClip(
        clips,
        size=(WIDTH, HEIGHT)
    )

    return video.with_audio(audio)


async def generate_video(
    words,
    signature,
    academy,
    logo_path,
    voice,
    speed
):
    
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    video_name = f"{uuid.uuid4().hex}.mp4"

    output_path = os.path.join(
        OUTPUT_FOLDER,
        video_name
    )

    clips = []

    for i, item in enumerate(words):

        print("Generating:", item["word"])

        audio_file = os.path.join(
            TEMP_FOLDER,
            f"{i}.mp3"
        )

        await make_audio(
            item["word"],
            audio_file,
            voice,
            speed
    )

        clip = create_clip(

            item["word"],
            item["arabic"],
            item["image"],
            audio_file,
            signature,
            academy,
            logo_path

        )

        clips.append(clip)

    final = concatenate_videoclips(clips)

    print("Saving video to:", output_path)

    try:
        print("IMAGE =", item["image"])
        print("IMAGE EXISTS =", os.path.exists(item["image"]))
        final.write_videofile(
            output_path,
            fps=30,
            codec="libx264",
            audio_codec="aac",
            preset="ultrafast",
            threads=1,
            logger="bar"
        )
    except Exception as e:
        print("VIDEO ERROR:", repr(e))
        raise

    finally:
        for clip in clips:
            clip.close()

        final.close()

        gc.collect()

    return output_path