# agent.py
import sys
import yaml
import logging

# --- CRITICAL FIX: Patch PyYAML for HyperPyYAML/CosyVoice ---
# ต้องทำสิ่งนี้เป็นบรรทัดแรกๆ ก่อน import livekit หรือ fun_audio
def patch_yaml_aggressive():
    print("Applying Aggressive PyYAML Patch...")
    try:
        # Patch Base Loader
        setattr(yaml.Loader, 'max_depth', 10000)
        
        # Patch CLoader (ตัวที่ Mac/Linux ชอบใช้และทำให้เกิดบั๊ก)
        if hasattr(yaml, 'CLoader'):
            setattr(yaml.CLoader, 'max_depth', 10000)
            
        # Patch SafeLoader และอื่นๆ เผื่อไว้
        if hasattr(yaml, 'SafeLoader'):
            setattr(yaml.SafeLoader, 'max_depth', 10000)
    except Exception as e:
        print(f"YAML Patch Warning: {e}")

patch_yaml_aggressive()
# ------------------------------------------------------------

import asyncio
from dotenv import load_dotenv

load_dotenv()

from livekit import rtc
from livekit.agents import JobContext, WorkerOptions, cli, tokenize, tts, AutoSubscribe
from livekit.agents.llm import ChatContext, ChatMessage
from livekit.agents.voice import Agent, AgentSession
from livekit.plugins import silero, openai
from fun_audio import SenseVoiceSTT, CosyVoiceTTS # import หลัง patch แล้ว
# from mock_llm import MockLLM

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("agent")

async def entrypoint(ctx: JobContext):
    logger.info(f"Connecting to room: {ctx.room.name}")
    
    # 1. เชื่อมต่อ
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    logger.info("Connected to room")

    # 2. เตรียม TTS Adapter
    # หมายเหตุ: CosyVoice ใช้ 22050Hz แต่อาจจะต้องเช็คว่า LiveKit รองรับไหม
    # ถ้า Model โหลดผ่าน Error เรื่อง Audio Frame จะหายไปเอง
    tts_adapter = tts.StreamAdapter(
        tts=CosyVoiceTTS(),
        sentence_tokenizer=tokenize.basic.SentenceTokenizer()
    )

    # 3. สร้าง Agent
    initial_ctx = ChatContext(
        items=[
            ChatMessage(
                role="system",
                content=["คุณคือผู้ช่วย AI อารมณ์ดี ชื่อจาวิส พูดภาษาไทยเป็นหลัก สั้นกระชับและเป็นกันเอง"]
            )
        ]
    )

    agent = Agent(
        vad=silero.VAD.load(),
        stt=SenseVoiceSTT(),
        llm=openai.LLM(
            model="qwen2.5:7b",
            base_url="http://localhost:11434/v1",
            api_key="ollama", # Dummy key required by OpenAI client
        ),
        tts=tts_adapter,
        chat_ctx=initial_ctx,
        instructions="คุณคือผู้ช่วย AI อารมณ์ดี ชื่อจาวิส พูดภาษาไทยเป็นหลัก สั้นกระชับและเป็นกันเอง",
    )

    # 4. เริ่มทำงาน
    # 4. สร้างและเริ่ม Session
    # AgentSession เป็นตัวจัดการ Runtime (Connection, STT, LLM, TTS loop)
    # เราต้องสร้าง session ขึ้นมาก่อน
    # หมายเหตุ: AgentSession รับ args ต่างๆ เป็น optional ถ้าเราส่ง agent ไปใน start() มันจะใช้ค่าจาก agent
    session = AgentSession() 
    
    # รอ Participant (ถ้าจำเป็น) 
    # ปกติ AgentSession จะจัดการ connection ให้ แต่การ wait_for_participant ช่วยให้แน่ใจว่ามีคนเข้าห้องแล้ว
    participant = await ctx.wait_for_participant()
    logger.info(f"Starting agent for participant: {participant.identity}")
    
    # เริ่มทำงาน
    # start() เป็น async function
    await session.start(agent, room=ctx.room)
    
    # Loop to keep process alive is handled by session usually?
    # No, AgentSession.start usually starts tasks and returns properly?
    # Let's check if we need to wait.
    # The original code awaited session.start
    
    # If session.start returns, does it mean it's done? 
    # Usually usage is: async with session.start(...) ? NO, standard start returns RunResult or None.
    # The session runs tasks in background.
    
    # To keep the entrypoint alive while session is running:
    # We can await ctx.room.disconnect logic or similar.
    # But usually the JobContext keeps it alive?
    # Let's just await session.start and see. 
    # If it exits immediately, we might need a keep-alive loop.
    
    # However, standard example often just awaits start. 
    # Let's try to just await start for now, but to be safe against immediate exit,
    # I will add a small sleep loop monitoring the room state if start returns immediately.
    
    # Actually, looking at source code, start() returns RunResult. It likely starts background tasks.
    # We need to keep the entrypoint alive.
    
    while ctx.room.connection_state == rtc.ConnectionState.CONN_CONNECTED:
        await asyncio.sleep(1)

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))