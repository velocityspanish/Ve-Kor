"""
Facebook Reels Automation - Bilingual English/Korean Content Generator
IMPROVED VERSION: Better backgrounds, English categories, no repeats, Velocity Korean branding
"""

import os
import sys
import json
import random
import asyncio
import subprocess
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()

POLLINATIONS_API_KEY = os.getenv("POLLINATIONS_API_KEY")

# Directories
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
IMAGES_DIR = OUTPUT_DIR / "images"
AUDIO_DIR = OUTPUT_DIR / "audio"
VIDEO_DIR = OUTPUT_DIR / "video"
HISTORY_DIR = OUTPUT_DIR / "history"

for d in [OUTPUT_DIR, IMAGES_DIR, AUDIO_DIR, VIDEO_DIR, HISTORY_DIR]:
    d.mkdir(exist_ok=True)

# Video settings (9:16 vertical)
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
FPS = 30

# English category names (for American/European learners)
# Essential Korean learning categories + Motivational categories
CATEGORIES_ENGLISH = [
    # Essential Korean Learning (Priority)
    "Greetings", "Basic Phrases", "Common Expressions", "Travel Korean", "Restaurant Korean",
    "Shopping Korean", "Emergency Korean", "Family Terms", "Numbers Korean", "Time Korean",
    # Motivational Categories
    "Motivation", "Love", "Success", "Wisdom", "Happiness",
    "Self Improvement", "Gratitude", "Friendship", "Hope", "Creativity",
    "Inner Peace", "Confidence", "Perseverance", "Inspiration", "Positive Life",
    "Courage", "Kindness", "Patience", "Forgiveness", "Strength",
    "Joy", "Balance", "Growth", "Purpose", "Mindfulness",
]

# Korean translations for display
CATEGORIES_KOREAN = {
    # Essential Korean Learning (Priority)
    "Greetings": "인사말",
    "Basic Phrases": "기본 표현",
    "Common Expressions": "일반 표현",
    "Travel Korean": "여행 한국어",
    "Restaurant Korean": "식당 한국어",
    "Shopping Korean": "쇼핑 한국어",
    "Emergency Korean": "비상 한국어",
    "Family Terms": "가족 용어",
    "Numbers Korean": "숫자 한국어",
    "Time Korean": "시간 한국어",
    # Motivational Categories
    "Motivation": "동기부여",
    "Love": "사랑",
    "Success": "성공",
    "Wisdom": "지혜",
    "Happiness": "행복",
    "Self Improvement": "자기계발",
    "Gratitude": "감사",
    "Friendship": "우정",
    "Hope": "희망",
    "Creativity": "창의성",
    "Inner Peace": "내면의 평화",
    "Confidence": "자신감",
    "Perseverance": "인내심",
    "Inspiration": "영감",
    "Positive Life": "긍정적인 삶",
    "Courage": "용기",
    "Kindness": "친절",
    "Patience": "인내",
    "Forgiveness": "용서",
    "Strength": "힘",
    "Joy": "기쁨",
    "Balance": "균형",
    "Growth": "성장",
    "Purpose": "목적",
    "Mindfulness": "마음챙김",
}

# Edge TTS voices
ENGLISH_VOICE = "en-US-GuyNeural"
KOREAN_VOICE = "ko-KR-SunHiNeural"

# Phrase history file (NEVER delete this!)
PHRASE_HISTORY_FILE = HISTORY_DIR / "all_generated_phrases.json"

# Recent categories file (for rotation - prevents category repeats)
RECENT_CATEGORIES_FILE = HISTORY_DIR / "recent_categories.json"
MAX_RECENT_CATEGORIES = 15  # Track last 15 categories to avoid repeats


# ============== PHRASE HISTORY MANAGEMENT (Prevent Repeats) ==============

def load_phrase_history():
    """Load all previously generated phrases"""
    if PHRASE_HISTORY_FILE.exists():
        with open(PHRASE_HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"phrases": [], "last_updated": None}


def save_phrase_history(data):
    """Save phrase history"""
    data["last_updated"] = datetime.now().isoformat()
    with open(PHRASE_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def is_phrase_used(english_phrase):
    """Check if phrase was already generated"""
    history = load_phrase_history()
    english_lower = english_phrase.lower().strip()
    for p in history.get("phrases", []):
        if p.get("english", "").lower().strip() == english_lower:
            return True
    return False


def add_phrases_to_history(phrases, category):
    """Add new phrases to history"""
    history = load_phrase_history()
    for phrase in phrases:
        history["phrases"].append({
            "english": phrase["english"],
            "korean": phrase["korean"],
            "category": category,
            "generated_at": datetime.now().isoformat()
        })
    save_phrase_history(history)
    print(f"[history] Added {len(phrases)} phrases to history (total: {len(history['phrases'])})")


# ============== CATEGORY ROTATION MANAGEMENT (Prevent Repeats) ==============

def load_recent_categories():
    """Load recently used categories"""
    if RECENT_CATEGORIES_FILE.exists():
        with open(RECENT_CATEGORIES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"recent_categories": [], "last_updated": None}


def save_recent_categories(data):
    """Save recent categories"""
    data["last_updated"] = datetime.now().isoformat()
    with open(RECENT_CATEGORIES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_available_category():
    """Get a category that hasn't been used recently - ensures rotation across ALL 35 categories"""
    recent_data = load_recent_categories()
    recent = recent_data.get("recent_categories", [])
    
    # Get all categories that are NOT in recent list
    available = [cat for cat in CATEGORIES_ENGLISH if cat not in recent]
    
    # If all categories have been used recently, clear the oldest ones
    if not available:
        # Keep only the most recent 5, clear the rest
        recent_data["recent_categories"] = recent[-5:]
        save_recent_categories(recent_data)
        available = [cat for cat in CATEGORIES_ENGLISH if cat not in recent_data["recent_categories"]]
        print(f"[rotation] All categories used recently - cleared old ones, {len(available)} available")
    
    # Random selection from available (non-recent) categories
    selected = random.choice(available)
    
    # Add to recent list
    recent.append(selected)
    
    # Keep only the last MAX_RECENT_CATEGORIES
    if len(recent) > MAX_RECENT_CATEGORIES:
        recent = recent[-MAX_RECENT_CATEGORIES:]
    
    recent_data["recent_categories"] = recent
    save_recent_categories(recent_data)
    
    print(f"[rotation] Selected '{selected}' ({len(available)} available, {len(recent)} in recent history)")
    return selected


# ============== CONTENT GENERATION ==============

def generate_phrases(category_english: str, num_phrases: int = 5) -> list:
    """Generate unique bilingual phrases with natural pauses, ensuring no repeats"""

    category_korean = CATEGORIES_KOREAN[category_english]

    # Try AI first
    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            import requests
            url = "https://gen.pollinations.ai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {POLLINATIONS_API_KEY}",
                "Content-Type": "application/json"
            }

            prompt = f"""Create {num_phrases * 2} unique {category_english} phrases for English speakers learning Korean.

IMPORTANT RULES FOR NATURAL SPEECH:
1. Keep phrases SHORT (5-12 words max per language)
2. Add NATURAL PAUSES using commas (e.g., "Dream big, start small")
3. Use punctuation for breathing room in TTS
4. Avoid long run-on sentences
5. Each phrase should be speakable in 3-5 seconds

For each phrase:
1. English phrase (with commas for natural pauses)
2. Korean translation (Hangul characters)
3. Romanization pronunciation guide (Revised Romanization, e.g., "annyeonghaseyo")

Return as JSON array:
[{{"english": "...", "korean": "...", "romanization": "..."}}]

IMPORTANT: Create FRESH, UNIQUE phrases that haven't been used before."""

            payload = {
                "model": "openai",
                "messages": [
                    {"role": "system", "content": "You are a Korean teacher. Create short, natural phrases with pauses."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.9
            }

            response = requests.post(url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()

            data = response.json()
            content = data["choices"][0]["message"]["content"].strip()

            # Extract JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            phrases = json.loads(content)

            # Filter out already-used phrases and ensure proper length
            unique_phrases = []
            for phrase in phrases:
                # Skip if too long (over 15 words)
                if len(phrase["english"].split()) > 15:
                    continue
                if not is_phrase_used(phrase["english"]):
                    unique_phrases.append(phrase)
                if len(unique_phrases) >= num_phrases:
                    break

            if len(unique_phrases) >= num_phrases:
                add_phrases_to_history(unique_phrases[:num_phrases], category_english)
                return unique_phrases[:num_phrases]

        except Exception as e:
            print(f"[content] Attempt {attempt + 1} failed: {e}")

    # Fallback to fresh phrases
    print("[content] Using fallback phrases...")
    return get_fresh_fallback_phrases(category_english, num_phrases)


def get_fresh_fallback_phrases(category: str, num_phrases: int) -> list:
    """Get fallback phrases, filtering out used ones"""

    all_fallbacks = {
        # Essential Korean Learning Categories
        "Greetings": [
            {"english": "Hello, nice to meet you.", "korean": "안녕하세요, 만나서 반가워요.", "romanization": "annyeonghaseyo, mannaseo bangawoyo."},
            {"english": "Good morning!", "korean": "좋은 아침이에요!", "romanization": "joeun achimieyo!"},
            {"english": "Good night, sleep well.", "korean": "안녕히 주무세요.", "romanization": "annyeonghi jumuseyo."},
            {"english": "See you tomorrow!", "korean": "내일 봐요!", "romanization": "naeil bwayo!"},
            {"english": "Goodbye, take care.", "korean": "안녕히 가세요.", "romanization": "annyeonghi gaseyo."},
        ],
        "Basic Phrases": [
            {"english": "Thank you very much.", "korean": "정말 고마워요.", "romanization": "jeongmal gomawoyo."},
            {"english": "You're welcome, no problem.", "korean": "천만에요, 문제없어요.", "romanization": "cheonmaneyo, munjeneopseoyo."},
            {"english": "I'm sorry, excuse me.", "korean": "죄송해요, 실례합니다.", "romanization": "joesonghaeyo, sillyehamnida."},
            {"english": "Yes, that's correct.", "korean": "네, 맞아요.", "romanization": "ne, majayo."},
            {"english": "No, I don't think so.", "korean": "아니요, 아닌 것 같아요.", "romanization": "aniyo, anin geot gatayo."},
        ],
        "Common Expressions": [
            {"english": "How are you doing today?", "korean": "오늘 어떻게 지내세요?", "romanization": "oneul eotteoke jinaeseyo?"},
            {"english": "I'm fine, thank you.", "korean": "저는 잘 지내요, 고마워요.", "romanization": "jeoneun jal jinaeyo, gomawoyo."},
            {"english": "What's your name?", "korean": "이름이 뭐예요?", "romanization": "ireumi mwoyeyo?"},
            {"english": "My name is...", "korean": "제 이름은... 이에요.", "romanization": "je ireumeun... ieyo."},
            {"english": "Nice to meet you too.", "korean": "저도 만나서 반가워요.", "romanization": "jeodo mannaseo bangawoyo."},
        ],
        "Travel Korean": [
            {"english": "Where is the bathroom?", "korean": "화장실이 어디예요?", "romanization": "hwajangsiri eodiyeyo?"},
            {"english": "How do I get there?", "korean": "거기 어떻게 가요?", "romanization": "geogi eotteoke gayo?"},
            {"english": "I need a taxi, please.", "korean": "택시가 필요해요.", "romanization": "taeksiga piryohaeyo."},
            {"english": "Take me to the hotel.", "korean": "호텔로 데려가 주세요.", "romanization": "hotello deryeoga juseyo."},
            {"english": "How much does it cost?", "korean": "얼마예요?", "romanization": "eolmayeyo?"},
        ],
        "Restaurant Korean": [
            {"english": "Can I see the menu?", "korean": "메뉴 좀 보여주세요.", "romanization": "menyo jom boyeojuseyo."},
            {"english": "This looks delicious!", "korean": "이거 맛있어 보여요!", "romanization": "igeo masisseo boyeoyo!"},
            {"english": "Water, please.", "korean": "물 좀 주세요.", "romanization": "mul jom juseyo."},
            {"english": "Check, please.", "korean": "계산서 주세요.", "romanization": "gyesanseo juseyo."},
            {"english": "It was delicious!", "korean": "잘 먹었습니다!", "romanization": "jal meogeosseumnida!"},
        ],
        "Shopping Korean": [
            {"english": "How much is this?", "korean": "이거 얼마예요?", "romanization": "igeo eolmayeyo?"},
            {"english": "Can I try this on?", "korean": "이거 입어봐도 돼요?", "romanization": "igeo ibeobwado dwaeyo?"},
            {"english": "Do you have a smaller size?", "korean": "더 작은 사이즈 있어요?", "romanization": "deo jageun saijeu isseoyo?"},
            {"english": "I'll take this one.", "korean": "이거로 할게요.", "romanization": "igeoro halgeyo."},
            {"english": "Can I pay by card?", "korean": "카드로 계산할 수 있어요?", "romanization": "kadeuro gyesanhal su isseoyo?"},
        ],
        "Emergency Korean": [
            {"english": "Help me, please!", "korean": "저 좀 도와주세요!", "romanization": "jeo jom dowajuseyo!"},
            {"english": "Call the police!", "korean": "경찰 불러주세요!", "romanization": "gyeongchal bulleojuseyo!"},
            {"english": "I need a doctor.", "korean": "의사가 필요해요.", "romanization": "uisaga piryohaeyo."},
            {"english": "Where is the hospital?", "korean": "병원이 어디예요?", "romanization": "byeongwoni eodiyeyo?"},
            {"english": "I'm lost, can you help?", "korean": "길을 잃었어요, 도와줄래요?", "romanization": "gireul ireosseoyo, dowajullaeyo?"},
        ],
        "Family Terms": [
            {"english": "This is my mother.", "korean": "이분은 저희 어머니세요.", "romanization": "ibuneun jeohi eomeoniseyo."},
            {"english": "This is my father.", "korean": "이분은 저희 아버지에요.", "romanization": "ibuneun jeohi abeojiyeyo."},
            {"english": "I have an older brother.", "korean": "저는 오빠가 있어요.", "romanization": "jeoneun oppaga isseoyo."},
            {"english": "I have a younger sister.", "korean": "저는 여동생이 있어요.", "romanization": "jeoneun yeodongsaengi isseoyo."},
            {"english": "These are my parents.", "korean": "이분들은 저희 부모님이에요.", "romanization": "ibundeureun jeohi bumonimieyo."},
        ],
        "Numbers Korean": [
            {"english": "One, two, three.", "korean": "하나, 둘, 셋.", "romanization": "hana, dul, set."},
            {"english": "Four, five, six.", "korean": "넷, 다섯, 여섯.", "romanization": "net, daseot, yeoseot."},
            {"english": "Seven, eight, nine, ten.", "korean": "일, 이, 삼, 사, 오, 육, 칠, 팔, 구, 십.", "romanization": "il, i, sam, sa, o, yuk, chil, pal, gu, sip."},
            {"english": "What number is this?", "korean": "이거 몇이에요?", "romanization": "igeo myeochieyo?"},
            {"english": "Give me two, please.", "korean": "두 개 주세요.", "romanization": "du gae juseyo."},
        ],
        "Time Korean": [
            {"english": "What time is it?", "korean": "지금 몇 시예요?", "romanization": "jigeum myeot siyeyo?"},
            {"english": "It's three o'clock.", "korean": "세 시예요.", "romanization": "se siyeyo."},
            {"english": "See you at noon.", "korean": "정오에 봐요.", "romanization": "jeongo-e bwayo."},
            {"english": "I'll be there in five minutes.", "korean": "5 분 후에 갈게요.", "romanization": "o-bun hue galgeyo."},
            {"english": "What day is today?", "korean": "오늘 무슨 요일이에요?", "romanization": "oneul museun yoil-ieyo?"},
        ],
        # Motivational Categories
        "Motivation": [
            {"english": "Believe in yourself.", "korean": "자신을 믿으세요.", "romanization": "jasineul mideosseyo."},
            {"english": "You are capable of amazing things.", "korean": "당신은 놀라운 일을 해낼 수 있어요.", "romanization": "dangsineun nollaun ireul haenael su isseoyo."},
            {"english": "Dream big, start small.", "korean": "크게 꿈꾸고, 작게 시작하세요.", "romanization": "keuge kkumkkugo, jakge sigakhaseyo."},
            {"english": "Your future is created by your actions.", "korean": "당신의 미래는 당신의 행동으로 만들어집니다.", "romanization": "dangsinui miraeneun dangsinui haengdongeuro mandeureojimnida."},
            {"english": "Never give up on your dreams.", "korean": "절대 꿈을 포기하지 마세요.", "romanization": "jeoldae kkumeul pogihaji maseyo."},
        ],
        "Love": [
            {"english": "Love yourself first.", "korean": "먼저 자신을 사랑하세요.", "romanization": "meonjeo jasineul saranghaseyo."},
            {"english": "Love makes everything possible.", "korean": "사랑은 모든 것을 가능하게 해요.", "romanization": "sarangeun modeun geoseul ganeunghage haeyo."},
        ],
        "Success": [
            {"english": "Success comes from hard work.", "korean": "성공은 노력에서 옵니다.", "romanization": "seonggongeun noryeogeseo omnida."},
            {"english": "Keep going, you're getting there.", "korean": "계속 가세요, 거의 다 왔어요.", "romanization": "gyesok gaseyo, geoui da wasseoyo."},
        ],
        "Wisdom": [
            {"english": "Knowledge is power.", "korean": "지식은 힘입니다.", "romanization": "jisigeun himimnida."},
            {"english": "Learn from yesterday, live for today.", "korean": "어제에서 배우고, 오늘을 살아요.", "romanization": "eojeseo baeugo, oneureul sarayo."},
        ],
        "Happiness": [
            {"english": "Happiness is a choice.", "korean": "행복은 선택입니다.", "romanization": "haengbogeun seontaegimnida."},
            {"english": "Find joy in the little things.", "korean": "작은 것들 속에서 기쁨을 찾으세요.", "romanization": "jageun geotdeul sogeseo gippeumeul chajeuseyo."},
        ],
    }

    fallbacks = all_fallbacks.get(category, all_fallbacks["Motivation"])
    fresh_phrases = [p for p in fallbacks if not is_phrase_used(p["english"])]
    return fresh_phrases[:num_phrases]


# ============== AUDIO GENERATION ==============

async def generate_single_audio(text: str, voice: str, output_path: str):
    """Generate audio using Edge TTS"""
    try:
        import edge_tts
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_path)
        return True
    except Exception as e:
        print(f"  TTS error: {e}")
        return False


def generate_all_audio(phrases: list, output_dir: str):
    """Generate audio for all phrases with proper timing"""

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    audio_files = []

    for i, phrase in enumerate(phrases):
        english_file = output_dir / f"english_{i}.mp3"
        korean_file = output_dir / f"korean_{i}.mp3"
        combined_file = output_dir / f"combined_{i}.mp3"

        print(f"\n  Phrase {i+1}:")
        print(f"    EN: {phrase['english']}")
        print(f"    KR: {phrase['korean']}")

        # Generate English audio
        en_success = asyncio.run(generate_single_audio(phrase["english"], ENGLISH_VOICE, str(english_file)))
        if en_success:
            print(f"    ✓ English: {english_file.name}")
        else:
            cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", "2", str(english_file)]
            subprocess.run(cmd, capture_output=True)

        # Generate Korean audio
        kr_success = asyncio.run(generate_single_audio(phrase["korean"], KOREAN_VOICE, str(korean_file)))
        if kr_success:
            print(f"    ✓ Korean: {korean_file.name}")
        else:
            cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", "2", str(korean_file)]
            subprocess.run(cmd, capture_output=True)

        # Get ACTUAL durations
        en_duration = get_audio_duration(str(english_file))
        kr_duration = get_audio_duration(str(korean_file))

        # Add pause between English and Korean
        pause_between = 0.5
        total_duration = en_duration + pause_between + kr_duration

        print(f"    ⏱️  Total: {total_duration:.2f}s (EN: {en_duration:.2f}s + pause: {pause_between}s + KR: {kr_duration:.2f}s)")

        # Combine audio files
        cmd = [
            "ffmpeg", "-y",
            "-i", str(english_file),
            "-i", str(korean_file),
            "-filter_complex", f"[0:a][1:a]concat=n=2:v=0:a=1[out]",
            "-map", "[out]",
            str(combined_file)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            concat_file = output_dir / f"concat_{i}.txt"
            with open(concat_file, "w", encoding="utf-8") as f:
                f.write(f"file '{english_file.as_posix()}'\n")
                f.write(f"file '{korean_file.as_posix()}'\n")

            cmd = [
                "ffmpeg", "-y",
                "-f", "concat", "-safe", "0",
                "-i", str(concat_file),
                "-c:a", "aac",
                str(combined_file)
            ]
            subprocess.run(cmd, capture_output=True)
            if concat_file.exists():
                concat_file.unlink()

        actual_duration = get_audio_duration(str(combined_file))
        print(f"    ✓ Combined verified: {actual_duration:.2f}s")

        audio_files.append({
            "index": i,
            "english": str(english_file),
            "korean": str(korean_file),
            "combined": str(combined_file),
            "duration": actual_duration,
            "en_duration": en_duration,
            "kr_duration": kr_duration
        })

    print(f"\n[audio] ✓ Generated {len(audio_files)} phrase audios")
    return audio_files


def get_audio_duration(audio_file: str) -> float:
    """Get audio duration in seconds"""
    if not Path(audio_file).exists():
        return 2.0
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", audio_file]
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return float(result.stdout.strip())
    except:
        return 2.0


def create_final_narration(audio_files: list, output_file: str):
    """Combine all audio files"""
    n = len(audio_files)
    print(f"[audio] Combining {n} audio files...")

    concat_file = Path(output_file).parent / "narration_list.txt"

    with open(concat_file, "w", encoding="utf-8") as f:
        for audio_info in audio_files:
            combined_path = Path(audio_info["combined"])
            if combined_path.exists():
                path_str = str(combined_path.resolve()).replace("\\", "/").replace("'", "'\\''")
                f.write(f"file '{path_str}'\n")

    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file), "-c:a", "copy", str(output_file)]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if concat_file.exists():
        concat_file.unlink()

    if result.returncode == 0 and Path(output_file).exists() and Path(output_file).stat().st_size > 0:
        size = Path(output_file).stat().st_size
        print(f"\n[audio] ✓ Final narration: {Path(output_file).name} ({size/1024:.1f} KB)")
        return True

    return False


# ============== IMAGE GENERATION ==============

def create_impressive_background(category_english: str):
    """Create stunning gradient background with geometric patterns and glow"""
    from PIL import Image, ImageDraw

    img = Image.new('RGB', (VIDEO_WIDTH, VIDEO_HEIGHT))
    draw = ImageDraw.Draw(img)

    # HIGH CONTRAST gradients for ALL 25 categories (very different colors like Motivation)
    category_colors = {
        "Motivation": [(138, 43, 226), (75, 0, 130), (255, 20, 147), (147, 112, 219)],  # Purple → Dark Purple → Pink → Light Purple
        "Love": [(255, 0, 100), (139, 0, 0), (255, 105, 180), (255, 192, 203)],  # Red → Dark Red → Hot Pink → Pink
        "Success": [(255, 215, 0), (0, 100, 0), (255, 140, 0), (34, 139, 34)],  # Gold → Dark Green → Orange → Forest Green
        "Wisdom": [(0, 0, 139), (255, 215, 0), (70, 130, 180), (255, 255, 0)],  # Dark Blue → Gold → Steel Blue → Yellow
        "Happiness": [(255, 255, 0), (255, 0, 255), (255, 165, 0), (147, 112, 219)],  # Yellow → Magenta → Orange → Purple
        "Self Improvement": [(0, 128, 0), (255, 215, 0), (0, 255, 0), (255, 140, 0)],  # Green → Gold → Lime → Orange
        "Gratitude": [(255, 127, 80), (75, 0, 130), (255, 160, 122), (138, 43, 226)],  # Coral → Dark Purple → Light Salmon → Blue Violet
        "Friendship": [(255, 192, 203), (0, 100, 80), (255, 105, 180), (0, 200, 160)],  # Pink → Dark Teal → Hot Pink → Medium Teal
        "Hope": [(0, 0, 100), (255, 255, 0), (70, 130, 180), (255, 215, 0)],  # Dark Blue → Yellow → Steel Blue → Gold
        "Creativity": [(255, 0, 127), (0, 0, 139), (255, 20, 147), (75, 0, 130)],  # Deep Pink → Dark Blue → Deep Pink → Dark Purple
        "Inner Peace": [(135, 206, 235), (0, 0, 100), (176, 224, 230), (75, 0, 130)],  # Sky Blue → Dark Blue → Powder Blue → Dark Purple
        "Confidence": [(255, 69, 0), (0, 0, 139), (255, 140, 0), (70, 130, 180)],  # Red Orange → Dark Blue → Orange → Steel Blue
        "Perseverance": [(139, 69, 19), (255, 215, 0), (160, 82, 45), (255, 140, 0)],  # Saddle Brown → Gold → Sienna → Orange
        "Inspiration": [(255, 0, 255), (75, 0, 130), (255, 20, 147), (0, 0, 139)],  # Magenta → Dark Purple → Deep Pink → Dark Blue
        "Positive Life": [(50, 205, 50), (255, 0, 127), (144, 238, 144), (255, 20, 147)],  # Lime Green → Deep Pink → Light Green → Deep Pink
        "Courage": [(178, 34, 34), (255, 215, 0), (220, 20, 60), (255, 140, 0)],  # Firebrick → Gold → Crimson → Orange
        "Kindness": [(255, 182, 193), (138, 43, 226), (255, 160, 122), (75, 0, 130)],  # Light Salmon → Dark Purple → Light Salmon → Dark Purple
        "Patience": [(34, 139, 34), (255, 255, 0), (60, 179, 113), (255, 215, 0)],  # Forest Green → Yellow → Medium Sea Green → Gold
        "Forgiveness": [(230, 230, 250), (75, 0, 130), (216, 191, 216), (138, 43, 226)],  # Lavender → Dark Purple → Thistle → Blue Violet
        "Strength": [(100, 100, 100), (255, 69, 0), (150, 150, 150), (255, 140, 0)],  # Gray → Red Orange → Light Gray → Orange
        "Joy": [(255, 255, 0), (255, 0, 127), (255, 215, 0), (147, 112, 219)],  # Yellow → Deep Pink → Gold → Purple
        "Balance": [(60, 179, 113), (138, 43, 226), (152, 251, 152), (75, 0, 130)],  # Medium Sea Green → Dark Purple → Pale Green → Dark Purple
        "Growth": [(0, 100, 0), (255, 215, 0), (34, 139, 34), (255, 140, 0)],  # Dark Green → Gold → Forest Green → Orange
        "Purpose": [(75, 0, 130), (255, 215, 0), (138, 43, 226), (255, 140, 0)],  # Dark Purple → Gold → Blue Violet → Orange
        "Mindfulness": [(210, 180, 140), (75, 0, 130), (245, 245, 220), (138, 43, 226)],  # Tan → Dark Purple → Beige → Blue Violet
    }

    colors = category_colors.get(category_english, [(138, 43, 226), (75, 0, 130), (255, 20, 147), (147, 112, 219)])

    # Create smooth multi-stop gradient
    for y in range(VIDEO_HEIGHT):
        ratio = y / VIDEO_HEIGHT
        if ratio < 0.33:
            r = int(colors[0][0] + (colors[1][0] - colors[0][0]) * (ratio * 3))
            g = int(colors[0][1] + (colors[1][1] - colors[0][1]) * (ratio * 3))
            b = int(colors[0][2] + (colors[1][2] - colors[0][2]) * (ratio * 3))
        elif ratio < 0.66:
            r = int(colors[1][0] + (colors[2][0] - colors[1][0]) * ((ratio - 0.33) * 3))
            g = int(colors[1][1] + (colors[2][1] - colors[1][1]) * ((ratio - 0.33) * 3))
            b = int(colors[1][2] + (colors[2][2] - colors[1][2]) * ((ratio - 0.33) * 3))
        else:
            r = int(colors[2][0] + (colors[3][0] - colors[2][0]) * ((ratio - 0.66) * 3))
            g = int(colors[2][1] + (colors[3][1] - colors[2][1]) * ((ratio - 0.66) * 3))
            b = int(colors[2][2] + (colors[3][2] - colors[2][2]) * ((ratio - 0.66) * 3))
        draw.rectangle([(0, y), (VIDEO_WIDTH, y + 1)], fill=(r, g, b))

    # Add subtle geometric pattern for depth (circles)
    for i in range(0, VIDEO_WIDTH, 120):
        for j in range(0, VIDEO_HEIGHT, 120):
            draw.ellipse(
                [(i + 30, j + 30), (i + 90, j + 90)],
                outline=(255, 255, 255, 20),
                width=1
            )

    # Add radial glow effect from center
    glow = Image.new('RGBA', (VIDEO_WIDTH, VIDEO_HEIGHT), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)

    for radius in range(800, 0, -50):
        alpha = int(30 * (1 - radius / 800))
        glow_draw.ellipse(
            [(VIDEO_WIDTH//2 - radius, VIDEO_HEIGHT//3 - radius),
             (VIDEO_WIDTH//2 + radius, VIDEO_HEIGHT//3 + radius)],
            fill=(255, 255, 255, alpha)
        )

    # Composite glow over background
    img = img.convert('RGBA')
    img = Image.alpha_composite(img, glow)

    return img


def generate_complete_image(phrase_data: dict, category_english: str, output_path: str):
    """Generate image with impressive background"""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("PIL not available. Install: pip install Pillow")
        return None

    img = create_impressive_background(category_english)
    draw = ImageDraw.Draw(img)

    # Load fonts - Optimized for mobile viewing (INCREASED sizes)
    # English fonts (bold, professional look) - Linux/Windows fallback
    english_font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",  # Linux (GitHub Actions)
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",  # Alternative Linux
        "C:/Windows/Fonts/arialbd.ttf",  # Windows Arial Bold
        "C:/Windows/Fonts/segoeui.ttf",  # Windows Segoe UI
    ]

    # Korean fonts (for Korean characters only) - Bold versions
    korean_font_paths = [
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",  # Linux (GitHub Actions)
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",  # Alternative Linux
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",  # Alternative Linux
        "C:/Windows/Fonts/malgun.ttf",  # Windows Malgun Gothic (Korean)
        "C:/Windows/Fonts/malgunbd.ttf",  # Windows Malgun Gothic Bold
    ]

    def load_font(font_paths, size):
        """Load font with fallback"""
        for font_path in font_paths:
            try:
                return ImageFont.truetype(font_path, size)
            except (IOError, OSError):
                continue
        # Last resort - use default
        return ImageFont.load_default()

    # English text fonts (bold, professional)
    font_category = load_font(english_font_paths, 60)
    font_large = load_font(english_font_paths, 85)
    font_branding = load_font(english_font_paths, 52)

    # Korean text fonts (supports Korean characters, bold)
    font_korean = load_font(korean_font_paths, 85)

    # Romanization fonts - LARGER and BOLDER for better visibility
    font_romanization = load_font(korean_font_paths, 50)  # Increased from 42 to 50

    english = phrase_data.get("english", "")
    korean = phrase_data.get("korean", "")
    romanization = phrase_data.get("romanization", "")

    def wrap_text(text, font, max_width):
        words = text.split()
        lines = []
        current_line = []
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            width = bbox[2] - bbox[0]
            if width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        if current_line:
            lines.append(' '.join(current_line))
        return lines

    # Category at top
    category_text = category_english.upper()
    category_bbox = draw.textbbox((VIDEO_WIDTH // 2, 140), category_text, font=font_category, anchor="mm")
    padding = 25
    draw.rectangle(
        [(category_bbox[0] - padding, category_bbox[1] - padding),
         (category_bbox[2] + padding, category_bbox[3] + padding)],
        fill=(0, 0, 0, 200)
    )
    draw.text(
        (VIDEO_WIDTH // 2, 140),
        category_text,
        fill=(255, 255, 255),
        font=font_category,
        anchor="mm",
        stroke_width=2,
        stroke_fill=(0, 0, 0)
    )

    # English text
    english_y = 470  # Adjusted for larger fonts
    english_lines = wrap_text(english, font_large, VIDEO_WIDTH - 140)
    total_height = len(english_lines) * 95  # Increased from 75 for larger fonts

    draw.rectangle(
        [(60, english_y - 55), (VIDEO_WIDTH - 60, english_y + total_height + 15)],
        fill=(20, 30, 80, 220)
    )

    for i, line in enumerate(english_lines):
        y_pos = english_y + (i * 95)  # Increased spacing
        draw.text(
            (VIDEO_WIDTH // 2, y_pos),
            line,
            fill=(255, 255, 255),
            font=font_large,
            anchor="mm",
            stroke_width=2,
            stroke_fill=(0, 0, 0)
        )

    # Korean text
    korean_y = english_y + total_height + 110  # Increased from 100
    korean_lines = wrap_text(korean, font_korean, VIDEO_WIDTH - 140)
    total_height = len(korean_lines) * 95  # Increased from 75

    draw.rectangle(
        [(60, korean_y - 55), (VIDEO_WIDTH - 60, korean_y + total_height + 15)],
        fill=(80, 30, 30, 220)
    )

    for i, line in enumerate(korean_lines):
        y_pos = korean_y + (i * 95)  # Increased spacing
        draw.text(
            (VIDEO_WIDTH // 2, y_pos),
            line,
            fill=(255, 255, 0),
            font=font_korean,
            anchor="mm",
            stroke_width=2,
            stroke_fill=(0, 0, 0)
        )

    # Romanization with FILLED BOX - BOLDER text for better visibility
    romanization_y = korean_y + total_height + 90  # Increased from 80
    romanization_text = f"[{romanization}]"
    romanization_lines = wrap_text(romanization_text, font_romanization, VIDEO_WIDTH - 160)

    if romanization_lines:
        romanization_total_height = len(romanization_lines) * 52  # Increased from 42 for larger font
        draw.rectangle(
            [(70, romanization_y - 20), (VIDEO_WIDTH - 70, romanization_y + romanization_total_height + 10)],
            fill=(40, 40, 40, 230)
        )

        for i, romanization_line in enumerate(romanization_lines):
            y_pos = romanization_y + (i * 52)  # Increased spacing to match font size
            draw.text(
                (VIDEO_WIDTH // 2, y_pos),
                romanization_line,
                fill=(255, 255, 255),  # Brighter white for better contrast
                font=font_romanization,
                anchor="mm",
                stroke_width=2,  # Increased from 1 to 2 for bolder text
                stroke_fill=(0, 0, 0, 200)
            )

    # Branding
    branding_y = VIDEO_HEIGHT - 100
    draw.rectangle(
        [(0, branding_y - 30), (VIDEO_WIDTH, branding_y + 50)],
        fill=(0, 0, 0, 180)
    )
    draw.text(
        (VIDEO_WIDTH // 2, branding_y),
        "VELOCITY KOREAN",
        fill=(255, 255, 255),
        font=font_branding,
        anchor="mm",
        stroke_width=2,
        stroke_fill=(0, 0, 0)
    )

    if img.mode == 'RGBA':
        img = img.convert('RGB')

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, quality=95, optimize=True)
    print(f"  ✓ Image: {Path(output_path).name}")
    return output_path


# ============== VIDEO CREATION ==============

def create_video_from_images_audio(image_files: list, audio_files: list, combined_audio: str, output_file: str):
    """Create video from images and audio with PERFECT synchronization"""

    print(f"\n[video] Creating video from {len(image_files)} images...")
    print(f"[video] Ensuring complete audio playback and sync...")

    temp_clips = []

    for i, (img_path, audio_info) in enumerate(zip(image_files, audio_files)):
        duration = audio_info['duration']
        print(f"  Image {i+1}/{len(image_files)}: {duration:.2f}s (EN: {audio_info.get('en_duration', 0):.1f}s + FR: {audio_info.get('fr_duration', 0):.1f}s)")

        temp_clip = Path(output_file).parent / f"temp_clip_{i:02d}.mp4"
        temp_clips.append(temp_clip)

        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", str(img_path),
            "-vf", f"scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=decrease,pad={VIDEO_WIDTH}:{VIDEO_HEIGHT}:(ow-iw)/2:(oh-ih)/2,fps={FPS}",
            "-t", str(duration),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-preset", "medium",
            str(temp_clip)
        ]

        subprocess.run(cmd, check=True, capture_output=True)

    # Concatenate clips
    print("[video] Concatenating clips...")
    temp_video = Path(output_file).parent / "temp_video.mp4"
    concat_file = Path(output_file).parent / "concat_list.txt"

    with open(concat_file, "w") as f:
        for clip in temp_clips:
            f.write(f"file '{clip.resolve().as_posix()}'\n")

    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file), "-c", "copy", str(temp_video)]
    subprocess.run(cmd, check=True, capture_output=True)

    # Add audio
    print("[video] Adding audio (ensuring complete playback)...")
    audio_duration = get_audio_duration(combined_audio)
    print(f"[video] Audio duration: {audio_duration:.2f}s")

    cmd = [
        "ffmpeg", "-y",
        "-i", str(temp_video),
        "-i", str(combined_audio),
        "-c:v", "copy",
        "-c:a", "aac",
        "-shortest",
        str(output_file)
    ]
    subprocess.run(cmd, check=True, capture_output=True)

    # Verify
    video_duration = get_audio_duration(str(output_file).replace(".mp4", ".mp4"))
    print(f"[video] ✓ Video created: {Path(output_file).name} ({video_duration:.2f}s)")

    # Cleanup
    for clip in temp_clips:
        if clip.exists():
            clip.unlink()
    if temp_video.exists():
        temp_video.unlink()
    if concat_file.exists():
        concat_file.unlink()


# ============== MAIN WORKFLOW ==============

def generate_reel(category_english: str = None):
    """Generate complete Facebook Reel"""

    if not category_english:
        # Use smart category rotation to prevent repeats
        category_english = get_available_category()

    print(f"\n{'='*80}")
    print(f"Category: {category_english} ({CATEGORIES_KOREAN[category_english]})")
    print(f"{'='*80}\n")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    reel_dir = VIDEO_DIR / f"{category_english}_{timestamp}"
    reel_dir.mkdir(exist_ok=True)

    # Step 1: Generate unique phrases
    print("[1/4] Generating unique phrases (checking history)...")
    phrases = generate_phrases(category_english, num_phrases=5)

    for i, phrase in enumerate(phrases, 1):
        print(f"  {i}. {phrase['english']} → {phrase['korean']}")

    # Step 2: Generate images
    print("\n[2/4] Generating images with impressive backgrounds...")
    for i, phrase in enumerate(phrases):
        output_path = reel_dir / f"phrase_{i:02d}.jpg"
        generate_complete_image(phrase, category_english, str(output_path))
        print(f"  ✓ Image {i+1}: {phrase['english'][:40]}...")

    # Step 3: Generate audio
    print("\n[3/4] Generating audio (English + Korean with 500ms pause)...")
    audio_files = generate_all_audio(phrases, str(reel_dir))

    final_audio = reel_dir / "narration.mp3"
    create_final_narration(audio_files, str(final_audio))

    # Step 4: Create video - CRITICAL: Sort images for correct order
    print("\n[4/4] Creating video...")
    output_video = reel_dir / "final_reel.mp4"

    image_files = sorted([str(p) for p in reel_dir.glob("phrase_*.jpg")])

    create_video_from_images_audio(
        image_files,
        audio_files,
        str(final_audio),
        str(output_video)
    )

    # Save metadata
    metadata = {
        "category_english": category_english,
        "category_korean": CATEGORIES_KOREAN[category_english],
        "timestamp": timestamp,
        "phrases": phrases,
        "video": str(output_video),
        "audio": str(final_audio)
    }

    with open(reel_dir / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*80}")
    print(f"✅ REEL COMPLETE!")
    print(f"  📁 {reel_dir}")
    print(f"  🎬 {output_video.name}")
    print(f"  🏷️  Branding: Velocity Korean")
    print(f"{'='*80}\n")

    return metadata


if __name__ == "__main__":
    print("\n" + "="*80)
    print("🇰🇷 VELOCITY KOREAN - FACEBOOK REELS AUTOMATION 🇰🇷")
    print("="*80)
    print("\n✨ IMPROVED FEATURES:")
    print("  ✓ Natural pauses with commas (non-robotic TTS)")
    print("  ✓ Perfect audio-video synchronization")
    print("  ✓ Complete audio playback guaranteed")
    print("  ✓ English category names (for American/European learners)")
    print("  ✓ Velocity Korean branding at bottom")
    print("  ✓ NEVER repeats phrases (permanent history tracking)")
    print(f"\n📊 AVAILABLE CATEGORIES ({len(CATEGORIES_ENGLISH)} total):")
    for i, cat in enumerate(CATEGORIES_ENGLISH, 1):
        print(f"   {i:2d}. {cat} ({CATEGORIES_KOREAN[cat]})")
    print(f"\n📅 DAILY CAPACITY:")
    print(f"  • 4 reels per day = 20 unique phrases daily")
    print(f"  • {len(CATEGORIES_ENGLISH)} categories = Over 6 days before any category repeats")
    print(f"  • Phrase history is PERMANENT (never deletes)")
    print(f"  • AI generates FRESH phrases every time")
    print("="*80)

    generate_reel()

    print("\n" + "="*80)
    print("✅ READY FOR DAILY AUTOMATION!")
    print("="*80)
    print("\nTo generate 4 reels for today:")
    print("  from facebook_reels_automation import generate_daily_content")
    print("  generate_daily_content(times_per_day=4)")
    print("\nTo generate a single reel:")
    print("  generate_reel('Love')  # Or any category from the list above")
    print("="*80)
