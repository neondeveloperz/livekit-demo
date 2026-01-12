import sys
import os
import asyncio
from typing import AsyncGenerator
import logging
# --- 1. Aggressive YAML Patch (Nuclear Option) ---
import yaml

def patch_yaml():
    # Patch PyYAML
    loaders = [
        'Loader', 'SafeLoader', 
        'CLoader', 'CSafeLoader',
        'FullLoader', 'UnsafeLoader'
    ]
    
    for name in loaders:
        try:
            loader_cls = getattr(yaml, name, None)
            if loader_cls:
                setattr(loader_cls, 'max_depth', 10000)
        except Exception as e:
            print(f"Warning: Could not patch yaml.{name}: {e}")

    # Patch ruamel.yaml (Crucial for HyperPyYAML/CosyVoice)
    try:
        import ruamel.yaml
        ruamel_loaders = ['Loader', 'SafeLoader', 'RoundTripLoader']
        for name in ruamel_loaders:
             try:
                loader_cls = getattr(ruamel.yaml, name, None)
                if loader_cls:
                    setattr(loader_cls, 'max_depth', 10000)
             except Exception as e:
                print(f"Warning: Could not patch ruamel.yaml.{name}: {e}")
    except ImportError:
        print("Warning: ruamel.yaml not found, skipping patch.")
    except Exception as e:
        print(f"Warning: Error patching ruamel.yaml: {e}")

# เรียกใช้งานทันทีก่อนจะ import library อื่น
patch_yaml()
# ------------------------------------------------
# --- Patch ModelScope to use HuggingFace ---
# This ensures that internal downloads (like wetext) use HF instead of ModelScope
try:
    import modelscope
    from huggingface_hub import snapshot_download as hf_snapshot_download
    import logging
    
    logger = logging.getLogger("FunAudio")

    def patched_snapshot_download(model_id, *args, **kwargs):
        logger.info(f"Intercepted ModelScope download for {model_id}. Redirecting to HuggingFace...")
        # Map known ModelScope IDs to HF IDs if they differ, otherwise assume same
        if model_id == "pengzhendong/wetext":
            # The repo_id on HF is the same
            pass
            
        # Filter out arguments that might not be compatible if needed, 
        # but snapshot_download signatures are similar enough for basic usage.
        # safely remove 'cache_dir' if it's None to let HF use default or specific one
        if 'cache_dir' in kwargs and kwargs['cache_dir'] is None:
            del kwargs['cache_dir']
            
        return hf_snapshot_download(repo_id=model_id, *args, **kwargs)

    modelscope.snapshot_download = patched_snapshot_download
    logger.info("Successfully patched modelscope.snapshot_download to use huggingface_hub configuration.")

except ImportError:
    print("Warning: modelscope or huggingface_hub not found, skipping patch.")
except Exception as e:
    print(f"Warning: Failed to patch modelscope: {e}")


from livekit import rtc
from livekit.agents import stt, tts, utils, DEFAULT_API_CONNECT_OPTIONS, APIConnectOptions
from livekit.agents.utils import AudioBuffer
import numpy as np
import yaml

# --- 1. Monkey-patch PyYAML AND PyTorch Audio Load ---
try:
    if not hasattr(yaml.Loader, 'max_depth'):
        yaml.Loader.max_depth = 10000
    if not hasattr(yaml.SafeLoader, 'max_depth'):
        yaml.SafeLoader.max_depth = 10000
except Exception:
    pass

try:
    # Patch torchaudio.load to use soundfile directly (bypass TorchCodec issue)
    import torchaudio
    import soundfile as sf
    import torch

    def patched_torchaudio_load(filepath, **kwargs):
        # Ignore backend kwargs etc
        data, sample_rate = sf.read(filepath)
        if data.ndim == 1:
            data = data.reshape(-1, 1) # (samples, 1)
        data = data.T # (channels, samples)
        tensor = torch.from_numpy(data).float() 
        return tensor, sample_rate

    logger.info("Patching torchaudio.load with soundfile...")
    torchaudio.load = patched_torchaudio_load
except ImportError as e:
    logger.warning(f"Could not patch torchaudio: {e}")
except Exception as e:
    logger.warning(f"Error patching torchaudio: {e}")

# --- 2. Path Setup ---
# หา Path ของ Project Root ให้แม่นยำขึ้น
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# สมมติว่า fun_audio.py อยู่ในโฟลเดอร์ agent/ หรือ root ของ project
# ปรับให้ชี้ไปที่ Root หลักที่มีโฟลเดอร์ Fun-Audio-Chat
# ถ้าโครงสร้างคือ: /Users/.../Sources/livekit-demo/agent/fun_audio.py
# และ model อยู่: /Users/.../Sources/livekit-demo/Fun-Audio-Chat/pretrained_models
PROJECT_ROOT = os.path.dirname(CURRENT_DIR) 

# ถ้า fun_audio.py อยู่ใน livekit-demo เลย ให้ใช้ CURRENT_DIR
# PROJECT_ROOT = CURRENT_DIR 

COSYVOICE_PATH = os.path.join(PROJECT_ROOT, "Fun-Audio-Chat/third_party/CosyVoice")
if COSYVOICE_PATH not in sys.path:
    sys.path.append(COSYVOICE_PATH)

logger = logging.getLogger("fun_audio")

# --- 3. Patch load_wav BEFORE importing CosyVoice ---
# This fixes "TorchCodec is required" error by ensuring we use a working backend
try:
    import cosyvoice.utils.file_utils
    import torchaudio
    import torch
    
    # Original load_wav might be failing. specific to this environment.
    def patched_load_wav(wav, target_sr, min_sr=16000):
        # Generic load, let torchaudio decide backend or default
        try:
            # Try loading without enforcing backend first (newer torchaudio might prefer this)
            speech, sample_rate = torchaudio.load(wav) 
        except Exception:
            # Fallback to soundfile explicit
            speech, sample_rate = torchaudio.load(wav, backend='soundfile')
            
        speech = speech.mean(dim=0, keepdim=True)
        if sample_rate != target_sr:
            assert sample_rate >= min_sr, 'wav sample rate {} must be greater than {}'.format(sample_rate, target_sr)
            # Use Resample. Note: this might be slow on CPU but standard.
            speech = torchaudio.transforms.Resample(orig_freq=sample_rate, new_freq=target_sr)(speech)
        return speech

    cosyvoice.utils.file_utils.load_wav = patched_load_wav
    logger.info("Successfully monkey-patched cosyvoice.utils.file_utils.load_wav")

except ImportError:
    pass
except Exception as e:
    logger.warning(f"Failed to patch load_wav: {e}")

# --- 5. Monkey-Patch CosyVoice TransformerLM.sampling_ids (Fix RuntimeError crash) ---
# This fixes "sampling reaches max_trials" error in Thai/Cross-Lingual
try:
    from cosyvoice.llm.llm import TransformerLM
    
    # Original sampling_ids raises RuntimeError if it can't find a token.
    # We patch it to return the token anyway (best effort) after warnings.
    def patched_sampling_ids(self, weighted_scores, decoded_tokens, sampling, ignore_eos=True):
        num_trials, max_trials = 0, 200 # Increased from 100
        while True:
            top_ids = self.sampling(weighted_scores, decoded_tokens, sampling)
            if (not ignore_eos) or (top_ids < self.speech_token_size):
                break
            num_trials += 1
            if num_trials > max_trials:
                # logger.debug(f"sampling reaches max_trials {max_trials} and still get eos. Force returning EOS.")
                break # Just return attempts to avoid crash
        return top_ids

    TransformerLM.sampling_ids = patched_sampling_ids
    logger.info("Successfully monkey-patched TransformerLM.sampling_ids")
except ImportError:
    pass
except Exception as e:
    logger.warning(f"Failed to patch sampling_ids: {e}")

# --- 6. Try Import Libraries ---
try:
    from cosyvoice.cli.cosyvoice import CosyVoice, CosyVoice2, CosyVoice3
    from cosyvoice.utils.file_utils import load_wav
    HAS_COSYVOICE = True
except ImportError as e:
    logger.warning(f"CosyVoice library import failed: {e}")
    HAS_COSYVOICE = False

try:
    from funasr import AutoModel
    # from funasr.utils.postprocess_utils import rich_transcription_postprocess
    HAS_FUNASR = True
except ImportError:
    HAS_FUNASR = False




class SenseVoiceSTT(stt.STT):
    def __init__(self, model_path: str = "Fun-Audio-Chat/pretrained_models/SenseVoiceSmall", device: str = "cpu"):
        super().__init__(capabilities=stt.STTCapabilities(streaming=False, interim_results=False))
        self._model = None
        
        full_model_path = os.path.join(PROJECT_ROOT, model_path)
        
        if HAS_FUNASR:
            logger.info(f"Loading SenseVoice model from: {full_model_path}")
            try:
                if os.path.exists(full_model_path):
                    self._model = AutoModel(model=full_model_path, device=device)
                    logger.info("SenseVoice model loaded successfully")
                else:
                    logger.error(f"SenseVoice model path not found: {full_model_path}")
            except Exception as e:
                logger.error(f"Failed to load SenseVoice model: {e}")
        else:
            logger.warning("funasr not installed. SenseVoiceSTT will not function.")

    async def _recognize_impl(self, buffer: AudioBuffer, *, language: str | None = None, conn_options: APIConnectOptions = DEFAULT_API_CONNECT_OPTIONS) -> stt.SpeechEvent:
        if not HAS_FUNASR or not self._model:
            # logger.warning("SenseVoice model not active, returning empty transcript")
            return stt.SpeechEvent(type=stt.SpeechEventType.FINAL_TRANSCRIPT, alternatives=[])

        raw_bytes = b""
        if isinstance(buffer, rtc.AudioFrame):
            raw_bytes = buffer.data.tobytes()
        elif hasattr(buffer, 'frames'):
             raw_bytes = b"".join([f.data.tobytes() for f in buffer.frames])
        elif hasattr(buffer, 'data'):
             raw_bytes = buffer.data.tobytes()
        else:
             return stt.SpeechEvent(type=stt.SpeechEventType.FINAL_TRANSCRIPT, alternatives=[])
        
        # LiveKit audio is 16-bit PCM
        audio_np = np.frombuffer(raw_bytes, dtype=np.int16).astype(np.float32) / 32768.0

        try:
            res = self._model.generate([audio_np], language=language if language else "th", use_itn=False)
            if res and len(res) > 0 and 'text' in res[0]:
                text = res[0]['text']
                return stt.SpeechEvent(
                    type=stt.SpeechEventType.FINAL_TRANSCRIPT,
                    alternatives=[stt.SpeechData(text=text, confidence=1.0, language=language or "th")]
                )
        except Exception as e:
            logger.error(f"SenseVoice generation error: {e}")
        
        return stt.SpeechEvent(type=stt.SpeechEventType.FINAL_TRANSCRIPT, alternatives=[])


class CosyVoiceTTS(tts.TTS):
    def __init__(self, model_path: str = "Fun-Audio-Chat/pretrained_models/Fun-CosyVoice3-0.5B-2512", device: str = "cpu"):
        # LiveKit TTS usually expects sample rate matching the output
        super().__init__(capabilities=tts.TTSCapabilities(streaming=True), sample_rate=22050, num_channels=1)
        self._model = None
        self._device = device
        self.voice = "default" # Default to 'default' (zero-shot/cross-lingual) for Thai support
        
        full_model_path = os.path.join(PROJECT_ROOT, model_path)
        logger.info(f"Checking CosyVoice model at: {full_model_path}")

        if HAS_COSYVOICE:
             if os.path.exists(full_model_path):
                 logger.info(f"Found model folder. Loading CosyVoice...")
                 try:
                    # Implement robust AutoModel logic
                    # Check for specific YAMLs first to determine version
                    if os.path.exists(os.path.join(full_model_path, 'cosyvoice3.yaml')):
                        logger.info("Detected CosyVoice3 model.")
                        self._model = CosyVoice3(full_model_path)
                    elif os.path.exists(os.path.join(full_model_path, 'cosyvoice2.yaml')):
                         logger.info("Detected CosyVoice2 model.")
                         self._model = CosyVoice2(full_model_path)
                    else:
                         logger.info("Detected CosyVoice(V1) model.")
                         self._model = CosyVoice(full_model_path)
                         
                    logger.info("CosyVoice model loaded successfully!")
                 except Exception as e:
                    logger.error(f"Failed to load CosyVoice model (Exception): {e}")
             else:
                 logger.error(f"CosyVoice model NOT found at {full_model_path}. Please check path.")
        else:
             logger.warning("CosyVoice library not loaded.")

    def synthesize(self, text: str, *, conn_options: APIConnectOptions = DEFAULT_API_CONNECT_OPTIONS) -> tts.ChunkedStream:
        return CosyVoiceStream(self, text, conn_options)


class CosyVoiceStream(tts.ChunkedStream):
    def __init__(self, tts: CosyVoiceTTS, text: str, conn_options: APIConnectOptions):
        super().__init__(tts=tts, input_text=text, conn_options=conn_options)
        self._text = text

    async def _run(self, output_emitter: tts.AudioEmitter) -> None:
        # Initialize Emitter
        output_emitter.initialize(
            request_id=utils.shortuuid("tts_req_"),
            sample_rate=22050, # CosyVoice บังคับ 22050 (ถ้าแก้ตรงนี้ Model จริงเสียงจะเพี้ยน)
            num_channels=1,
            mime_type="audio/pcm"
        )

        # Helper to push silence
        def push_silence(duration_ms=500): 
            # Ensure emitter is initialized first
            try:
                output_emitter.initialize(
                     request_id=utils.shortuuid("tts_sil_"),
                     sample_rate=22050, 
                     num_channels=1, 
                     mime_type="audio/pcm"
                )
            except RuntimeError:
                pass # Already initialized
            
            samples = int(22050 * (duration_ms / 1000.0))
            silent_data = np.zeros(samples, dtype=np.int16).tobytes()
            output_emitter.push(silent_data)

        if not self._tts._model:
            logger.error("CosyVoice model not loaded.")
            push_silence()
            return
            
        audio_frames_generated = False
        try:
             # Basic inference
             logger.info(f"Synthesizing text: {self._text}")
             
             # Use Cross-Lingual Inference to support Thai
             prompt_wav_path = os.path.join(COSYVOICE_PATH, "asset/zero_shot_prompt.wav")
             
             if not os.path.exists(prompt_wav_path):
                 prompt_wav_path = os.path.join(COSYVOICE_PATH, "asset/cross_lingual_prompt.wav")
             
             if not os.path.exists(prompt_wav_path):
                 logger.error(f"Prompt wav not found at {prompt_wav_path}. Cannot perform cross-lingual synthesis.")
                 raise FileNotFoundError("Prompt wav not found")

             logger.info(f"Using prompt wav for Cross-Lingual: {prompt_wav_path}")
             # CosyVoice internals will load the wav using patched torchaudio.load
             model_output = self._tts._model.inference_cross_lingual(self._text, prompt_wav_path, stream=True)
             
             logger.info("Starting CosyVoice generator execution...")
             
             # Initialize Emitter for raw PCM BEFORE generating or pushing
             # Initialize Emitter (moved from top)
             try:
                 output_emitter.initialize(
                     request_id=utils.shortuuid("tts_req_"),
                     sample_rate=22050, # CosyVoice output
                     num_channels=1,
                     mime_type="audio/pcm"
                 )
             except Exception:
                 pass # Might be initialized if we switch logic later, but good for safety

             try:
                 for i, item in enumerate(model_output):
                     # logger.debug(f"Received chunk {i} keys: {list(item.keys())}") 
                     if 'tts_speech' in item:
                         audio_tensor = item['tts_speech']
                         
                         # Convert torch tensor to numpy safely
                         audio_float = audio_tensor.detach().cpu().numpy().flatten()
                         
                         # Convert to int16 PCM
                         audio_int16 = (audio_float * 32768).astype(np.int16)
                         
                         # PUSH RAW BYTES
                         chunk_bytes = audio_int16.tobytes()
                         if len(chunk_bytes) > 0:
                             output_emitter.push(chunk_bytes)
                             audio_frames_generated = True
                             logger.info(f"Pushed chunk {i} bytes successfully")
                         
             except RuntimeError as e:
                 # CosyVoice sometimes fails with "sampling reaches max_trials" for short/difficult inputs
                 if "sampling reaches max_trials" in str(e):
                      logger.warning(f"CosyVoice generation ended early due to sampling error: {e}")
                 else:
                      logger.error(f"CosyVoice runtime error during generation: {e}")
                 
                 # If we already generated audio, don't raise exception to keep stream alive
                 if not audio_frames_generated:
                     raise e
             except Exception as e:
                 import traceback
                 logger.error(f"Error during CosyVoice stream iteration: {e}\n{traceback.format_exc()}")
                 if not audio_frames_generated:
                     raise e
             except Exception as e:
                 import traceback
                 logger.error(f"Error during CosyVoice stream iteration: {e}\n{traceback.format_exc()}")
                 if not audio_frames_generated:
                     raise e
             
             logger.info(f"CosyVoice generator finished. Audio frames generated: {audio_frames_generated}")
                         
        except Exception as e:
             logger.error(f"CosyVoice synthesis failed: {e}")
             
        if not audio_frames_generated:
            logger.warning("No audio frames generated via CosyVoice. Pushing silence.")
            push_silence()