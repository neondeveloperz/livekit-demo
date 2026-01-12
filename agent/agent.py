import asyncio
from dotenv import load_dotenv

load_dotenv()

from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli, llm
from livekit.agents.voice import Agent, AgentSession
from livekit.plugins import openai, silero
from fun_audio import SenseVoiceSTT, CosyVoiceTTS

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("agent")

async def entrypoint(ctx: JobContext):
    logger.info(f"Connecting to room: {ctx.room.name}")
    # 1. เชื่อมต่อเข้าห้อง (Connect)
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    logger.info("Connected to room")

    # 2. สร้าง Agent (Configuration)
    agent = Agent(
        vad=silero.VAD.load(),
        stt=SenseVoiceSTT(), # Using FunAudioLLM SenseVoice
        llm=openai.LLM(model="gpt-4o"),
        tts=CosyVoiceTTS(),  # Using FunAudioLLM CosyVoice
        instructions="คุณคือผู้ช่วย AI อารมณ์ดี ชื่อจาวิส พูดภาษาไทยเป็นหลัก สั้นกระชับและเป็นกันเอง",
    )

    # 3. เริ่มทำงาน (Start Session)
    session = AgentSession()
    await session.start(agent, room=ctx.room)

    await asyncio.sleep(1)
    await session.say("สวัสดีครับ มีอะไรให้ผมช่วยไหมครับ", allow_interruptions=True)

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))