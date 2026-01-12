import asyncio
import logging
from livekit.agents import tts, utils, APIConnectOptions, DEFAULT_API_CONNECT_OPTIONS
import edge_tts

logger = logging.getLogger("edge_tts_plugin")

class EdgeTTS(tts.TTS):
    def __init__(self, voice: str = "th-TH-PremwadeeNeural"):
        # EdgeTTS produces MP3 by default which LiveKit can decode
        super().__init__(capabilities=tts.TTSCapabilities(streaming=False), sample_rate=24000, num_channels=1)
        self.voice = voice

    def synthesize(self, text: str, *, conn_options: APIConnectOptions = DEFAULT_API_CONNECT_OPTIONS) -> tts.ChunkedStream:
        return EdgeTTSStream(self, text, conn_options)

class EdgeTTSStream(tts.ChunkedStream):
    def __init__(self, tts_instance: EdgeTTS, text: str, conn_options: APIConnectOptions):
        super().__init__(tts=tts_instance, input_text=text, conn_options=conn_options)
        self._tts = tts_instance

    async def _run(self, output_emitter: tts.AudioEmitter) -> None:
        try:
            communicate = edge_tts.Communicate(self._input_text, self._tts.voice)
            
            # EdgeTTS outputs MP3 audio (audio/mpeg)
            output_emitter.initialize(
                request_id=utils.shortuuid("tts_req_"),
                sample_rate=24000, 
                num_channels=1,
                mime_type="audio/mpeg" 
            )

            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    output_emitter.push(chunk["data"])
            
            logger.info(f"EdgeTTS finished synthesizing: {len(self._input_text)} chars")

        except Exception as e:
            logger.error(f"EdgeTTS failed: {e}")
