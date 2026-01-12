from __future__ import annotations
import asyncio
from livekit.agents.llm import LLM, LLMStream, ChatContext, ChatChunk, ChoiceDelta
from livekit.agents import utils, APIConnectOptions

class MockLLM(LLM):
    def __init__(self):
        super().__init__()

    def chat(self, chat_ctx: ChatContext, **kwargs) -> LLMStream:
        return MockLLMStream(self, chat_ctx)

class MockLLMStream(LLMStream):
    def __init__(self, llm: LLM, chat_ctx: ChatContext):
        super().__init__(
            llm, 
            chat_ctx=chat_ctx, 
            tools=[], 
            conn_options=APIConnectOptions()
        )
        self._closing = False

    async def _run(self):
        # Determine response based on last user message
        user_msg = ""
        for msg in reversed(self._chat_ctx.items):
            if msg.role == "user":
                if isinstance(msg.content, list):
                    user_msg = " ".join([str(c) for c in msg.content])
                else:
                    user_msg = str(msg.content)
                break
        
        response_text = f"คุณพูดว่า: {user_msg} (นี่คือระบบตอบกลับอัตโนมัติ)"
        if not user_msg:
            response_text = "สวัสดีครับ ผมจาวิสเองครับ มีอะไรให้ช่วยไหมครับ"

        # Simulate streaming delay
        chunk_size = 5
        for i in range(0, len(response_text), chunk_size):
            if self._closing:
                break
            
            chunk_content = response_text[i:i+chunk_size]
            chunk = ChatChunk(
                id=utils.shortuuid("chunk_"),
                delta=ChoiceDelta(role="assistant", content=chunk_content)
            )
            # Use internal event emitter to yield chunk
            self._event_ch.send_nowait(chunk)
            await asyncio.sleep(0.1)
        
        # Signal completion
        self._event_ch.close()

    async def aclose(self):
        self._closing = True
        await super().aclose()
