# สร้าง Virtual Environment
python3.11 -m venv venv
source venv/bin/activate

# ลง Lib หลัก และ Plugin ของ OpenAI (สำหรับ LLM/TTS) และ Silero (สำหรับ VAD)
pip install livekit-agents livekit-plugins-openai livekit-plugins-silero python-dotenv