import os
import json
import time
import asyncio
import datetime
import requests
import edge_tts
from google import genai
from moviepy import ImageClip, AudioFileClip

# 1. Cấu hình Gemini Client từ Secret GitHub
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_KEY:
    print("LỖI: Chưa tìm thấy GEMINI_API_KEY trong Secrets!")
    exit(1)

client = genai.Client(api_key=GEMINI_KEY)

def detect_current_season_and_event():
    """Tự động kiểm tra thời gian thực để xác định mùa và sự kiện lễ hội đang diễn ra"""
    now = datetime.datetime.now()
    month = now.month

    if month == 12:
        return "Christmas and Winter Holiday season (Snow, Santa, Reindeer, Gingerbread, Christmas gifts)"
    elif month == 10:
        return "Halloween and Autumn season (Pumpkins, cute costumes, autumn leaves, friendly ghosts)"
    elif month in [1, 2]:
        return "New Year celebration and Winter season (Cold weather, snowflakes, celebrations)"
    elif month in [3, 4, 5]:
        return "Spring season (Blooming flowers, baby animals, Easter eggs, sunny outdoors)"
    elif month in [6, 7, 8]:
        return "Summer season (Beach, sunshine, ocean animals, fruits, ice cream)"
    else:
        return "Autumn season (Falling colorful leaves, cozy woodland animals)"

def generate_kids_content():
    """Gọi Gemini tạo kịch bản đố vui với cơ chế retry và kịch bản dự phòng"""
    current_context = detect_current_season_and_event()
    print(f"Bối cảnh thời gian: {current_context}")

    prompt = f"""
    You are creating a fun, interactive YouTube Shorts educational guessing quiz for toddlers and young kids.
    CURRENT TIME CONTEXT: {current_context}.

    RECURRING MAIN CHARACTER:
    - Name: Lily (a sweet, adorable 5-year-old cartoon girl, big sparkling eyes, cute brown pigtails hair, friendly Pixar 3D animated style).
    - Lily must appear in the scene, dressed appropriately for the current season/event, interacting happily with the quiz subject.

    Format MUST be strict valid JSON only, no markdown formatting, no extra explanation:
    {{
        "subject": "Name of the item or animal being guessed",
        "question": "Lily's playful riddle or question asking little friends to guess (English, 1-2 short sentences)",
        "reveal": "Lily happily announcing the answer with words of encouragement (English, 1-2 short sentences)",
        "image_prompt": "detailed visual prompt describing cute little girl Lily with brown pigtails in Pixar 3D style, dressed for {current_context}, smiling warmly next to the subject, vertical 9:16 aspect ratio, vibrant colors, warm cinematic lighting, high resolution, clean animated background"
    }}
    """

    for attempt in range(1, 4):
        try:
            print(f"Đang gọi Gemini (lần thử {attempt}/3)...")
            response = client.models.generate_content(
                model='gemini-3.8-flash',
                contents=prompt
            )
            text = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(text)
        except Exception as e:
            print(f"Lỗi gọi Gemini ở lần {attempt}: {e}")
            if attempt < 3:
                time.sleep(5)

    # Dự phòng an toàn nếu Google AI Studio tạm thời quá tải
    print("Dùng kịch bản dự phòng mùa đông cho bé Lily để bảo đảm có video xuất xưởng...")
    return {
        "subject": "Cute Snowman",
        "question": "Can you guess who is standing next to me? He has a carrot nose and loves cold snow!",
        "reveal": "It's our friendly Snowman! Great job little friends!",
        "image_prompt": "cute 5-year-old girl Lily with brown pigtails wearing a cozy red winter coat and warm knitted scarf, standing next to a smiling 3D snowman with carrot nose, soft snow falling, warm festive glow, Pixar 3D style, vibrant colors, vertical 9:16 aspect ratio, high resolution"
    }

async def text_to_speech(text, filename):
    """Giọng đọc tiếng Anh bé gái vui nhộn bằng Edge-TTS"""
    communicate = edge_tts.Communicate(text, "en-US-AnaNeural")
    await communicate.save(filename)

def download_image(prompt, filename):
    """Tải ảnh 3D chuẩn 9:16 miễn phí từ Pollinations"""
    clean_prompt = requests.utils.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{clean_prompt}?width=720&height=1280&nologo=true"
    res = requests.get(url, timeout=45)
    if res.status_code == 200:
        with open(filename, 'wb') as f:
            f.write(res.content)
        return True
    return False

def make_short_video():
    print("--- BẮT ĐẦU TẠO VIDEO SHORTS TỰ ĐỘNG ---")
    data = generate_kids_content()

    print(f"Nhân vật chính: Bé Lily")
    print(f"Chủ đề hôm nay: {data.get('subject', 'Kids Special')}")

    # 1. Tải ảnh 3D nhân vật Lily cùng chủ đề
    img_file = "scene.jpg"
    print("Đang tạo ảnh hoạt hình 3D...")
    if not download_image(data["image_prompt"], img_file):
        print("Lỗi tạo ảnh!")
        return

    # 2. Tạo voice đọc câu hỏi và đáp án
    audio_file = "voice.mp3"
    print("Đang tạo giọng lồng tiếng...")
    full_text = f"Hi friends! {data['question']} ... Let's count down! 3, 2, 1! {data['reveal']}"
    asyncio.run(text_to_speech(full_text, audio_file))

    # 3. Dựng video bằng MoviePy
    print("Đang dựng video...")
    audio_clip = AudioFileClip(audio_file)
    video_clip = ImageClip(img_file).with_duration(audio_clip.duration + 1)
    video_clip = video_clip.with_audio(audio_clip)

    output_file = "kids_short.mp4"
    video_clip.write_videofile(output_file, fps=24, codec="libx264", audio_codec="aac")
    print(f"SUCCESS: Video đã xuất thành công tại {output_file}!")

if __name__ == "__main__":
    make_short_video()
