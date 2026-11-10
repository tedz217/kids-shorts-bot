import os
import json
import asyncio
import requests
import edge_tts
from google import genai
from moviepy import ImageClip, AudioFileClip

# 1. Cấu hình Gemini Client từ Secret
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_KEY:
    print("LỖI: Chưa tìm thấy GEMINI_API_KEY trong Secrets!")
    exit(1)

client = genai.Client(api_key=GEMINI_KEY)

def generate_kids_content():
    """Gọi Gemini lấy kịch bản đố vui hoạt hình cho bé (tiếng Anh)"""
    prompt = """
    Tạo 1 kịch bản video YouTube Shorts đố vui cực ngắn cho trẻ em (tiếng Anh).
    Format bắt buộc là JSON duy nhất, không thêm markdown hay bất kỳ chữ nào khác:
    {
        "animal": "Giraffe",
        "question": "Can you guess this animal? It has a very long neck!",
        "reveal": "It's a Giraffe! Good job little friend!",
        "image_prompt": "cute 3d cartoon baby giraffe smiling, pixar style, vibrant warm colors, 9:16 vertical, clean background"
    }
    """
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)
    except Exception as e:
        print(f"Lỗi gọi Gemini: {e}")
        return None

async def text_to_speech(text, filename):
    """Tạo giọng đọc tiếng Anh trẻ em miễn phí bằng Edge-TTS"""
    communicate = edge_tts.Communicate(text, "en-US-AnaNeural")
    await communicate.save(filename)

def download_image(prompt, filename):
    """Tạo ảnh 3D dọc 9:16 miễn phí bằng Pollinations"""
    clean_prompt = requests.utils.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{clean_prompt}?width=720&height=1280&nologo=true"
    res = requests.get(url, timeout=45)
    if res.status_code == 200:
        with open(filename, 'wb') as f:
            f.write(res.content)
        return True
    return False

def make_short_video():
    print("--- BẮT ĐẦU TẠO VIDEO SHORTS ---")
    data = generate_kids_content()
    if not data:
        print("Không tạo được nội dung từ Gemini. Thoát an toàn.")
        return

    print(f"Chủ đề hôm nay: {data.get('animal', 'Unknown')}")

    # 1. Tải ảnh hoạt hình 9:16
    img_file = "scene.jpg"
    print("Đang tạo ảnh 3D...")
    if not download_image(data["image_prompt"], img_file):
        print("Lỗi tạo ảnh!")
        return

    # 2. Tạo giọng đọc tiếng Anh
    audio_file = "voice.mp3"
    print("Đang tạo giọng đọc...")
    full_text = f"{data['question']} ... 3, 2, 1! {data['reveal']}"
    asyncio.run(text_to_speech(full_text, audio_file))

    # 3. Dựng video bằng MoviePy
    print("Đang ghép video...")
    audio_clip = AudioFileClip(audio_file)
    video_clip = ImageClip(img_file).with_duration(audio_clip.duration + 1)
    video_clip = video_clip.with_audio(audio_clip)

    output_file = "kids_short.mp4"
    video_clip.write_videofile(output_file, fps=24, codec="libx264", audio_codec="aac")
    print(f"SUCCESS: Video đã xuất thành công tại {output_file}!")

if __name__ == "__main__":
    make_short_video()
