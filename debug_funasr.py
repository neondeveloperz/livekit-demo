import sys
import traceback

print(f"Python: {sys.executable}")

try:
    print("Attempting: from funasr import AutoModel")
    from funasr import AutoModel
    print("Success: AutoModel")
except Exception as e:
    print(f"FAILED: AutoModel - {e}")
    traceback.print_exc()

try:
    print("Attempting: from funasr.utils.postprocess_utils import rich_transcription_postprocess")
    from funasr.utils.postprocess_utils import rich_transcription_postprocess
    print("Success: rich_transcription_postprocess")
except Exception as e:
    print(f"FAILED: rich_transcription_postprocess - {e}")
    traceback.print_exc()
