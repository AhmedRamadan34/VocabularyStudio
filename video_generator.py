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
    duration = audio.duration + 1

    bg = (
        ImageClip(image_path)
        .resized((WIDTH, HEIGHT))
        .with_duration(duration)
    )

    clips = [bg]

    # ---------------------------------------------------------
    # الكلمة الإنجليزية
    # ---------------------------------------------------------
    english = TextClip(
        text=word,
        font=FONT,
        font_size=52,
        color="white",
        stroke_color="black",
        stroke_width=2,
        method="caption",
        size=(480, 120),
        text_align="center",
        horizontal_align="center",
        vertical_align="center",
        interline=0
    ).with_duration(duration)

    # نبدأ الكتلة النصية كلها من نقطة ثابتة فوق منتصف الشاشة شوية
    text_block_top = 600

    english = english.with_position(("center", text_block_top))
    clips.append(english)

    # نحسب أسفل الكلمة الإنجليزية فعليًا (ارتفاعها الحقيقي بعد الرسم)
    current_y = text_block_top + english.h + 12

    # ---------------------------------------------------------
    # الكلمة العربية
    # ---------------------------------------------------------
    if arabic:

        arabic_fixed = fix_arabic(arabic)

        arabic_clip = TextClip(
            text=arabic_fixed,
            font=FONT,
            font_size=38,
            color="yellow",
            stroke_color="black",
            stroke_width=1,
            method="caption",
            size=(480, 100),
            text_align="center",
            horizontal_align="center",
            vertical_align="center",
            interline=0
        ).with_duration(duration)

        arabic_clip = arabic_clip.with_position(("center", current_y))
        clips.append(arabic_clip)

        current_y += arabic_clip.h + 12

    # ---------------------------------------------------------
    # شريط المعلومات السفلي: لوجو + توقيع + اسم الأكاديمية
    # كلهم بيتحسبوا بالنسبة لبعض عشان محدش يقص التاني
    # ---------------------------------------------------------
    bottom_margin = 25
    logo_size = 70

    footer_top = HEIGHT - bottom_margin - logo_size

    has_logo = logo_path and os.path.exists(logo_path)
    text_x_start = 20 + logo_size + 10 if has_logo else 30
    text_width = WIDTH - text_x_start - 20

    if has_logo:
        logo = (
            ImageClip(logo_path)
            .resized(width=logo_size)
            .with_position((20, footer_top))
            .with_duration(duration)
        )
        clips.append(logo)

    # نبني الـ clips الأول عشان نعرف ارتفاعهم الحقيقي، وبعدين نوسطهم
    # رأسيًا بالنسبة لمنطقة اللوجو (وليس بترتيب تنازلي ثابت زي الأول)
    sig_clip = None
    academy_clip = None

    if signature:
        sig_clip = TextClip(
            text=signature,
            font=FONT,
            font_size=20,
            color="white",
            stroke_color="black",
            stroke_width=1,
            size=(text_width, 34),
            method="caption",
            text_align="left",
            horizontal_align="left",
            vertical_align="center",
            interline=0
        ).with_duration(duration)

    if academy:
        academy_clip = TextClip(
            text=academy,
            font=FONT,
            font_size=16,
            color="#d9d9d9",
            stroke_color="black",
            stroke_width=1,
            size=(text_width, 28),
            method="caption",
            text_align="left",
            horizontal_align="left",
            vertical_align="center",
            interline=0
        ).with_duration(duration)

    # ارتفاع الكتلة الكلية (توقيع + أكاديمية) عشان نوسطها مع اللوجو
    block_h = (sig_clip.h if sig_clip else 0) + (academy_clip.h if academy_clip else 0)
    block_top = footer_top + (logo_size - block_h) // 2

    current_text_y = block_top

    if sig_clip:
        sig_clip = sig_clip.with_position((text_x_start, current_text_y))
        clips.append(sig_clip)
        current_text_y += sig_clip.h

    if academy_clip:
        academy_clip = academy_clip.with_position((text_x_start, current_text_y))
        clips.append(academy_clip)

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