import sys
import os
import torch
import yaml

# --- Patch PyYAML and ruamel.yaml ---
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

patch_yaml()
# ------------------------------------------------

# --- Patch torchaudio.load to bypass TorchCodec/backend issues ---
try:
    import torchaudio
    import soundfile as sf
    import numpy as np

    def patched_torchaudio_load(filepath, **kwargs):
        # Ignore backend kwargs etc
        data, sample_rate = sf.read(filepath)
        # data is numpy array
        # Torchaudio load returns (Tensor[channels, samples], sample_rate)
        if data.ndim == 1:
            data = data.reshape(-1, 1) # (samples, 1)
        
        # sf read is (samples, channels), convert to (channels, samples)
        data = data.T 
        
        tensor = torch.from_numpy(data).float() 
        return tensor, sample_rate

    print("Patching torchaudio.load with soundfile...")
    torchaudio.load = patched_torchaudio_load
except ImportError as e:
    print(f"Warning: Could not patch torchaudio: {e}")

# Add paths
sys.path.append(os.path.join(os.getcwd(), "Fun-Audio-Chat/third_party/CosyVoice"))

from cosyvoice.cli.cosyvoice import CosyVoice, CosyVoice2, CosyVoice3

# Path to model
model_path = "Fun-Audio-Chat/pretrained_models/Fun-CosyVoice3-0.5B-2512"

if not os.path.exists(model_path):
    print(f"Model path not found: {model_path}")
    sys.exit(1)

print(f"Loading model from {model_path}...")
try:
    # Try loading as CosyVoice3
    model = CosyVoice3(model_path)
    print("Loaded as CosyVoice3")
except Exception as e:
    print(f"Failed to load as CosyVoice3: {e}")
    try:
         model = CosyVoice2(model_path)
         print("Loaded as CosyVoice2")
    except Exception as e2:
         print(f"Failed to load as CosyVoice2: {e2}")
         model = CosyVoice(model_path)
         print("Loaded as CosyVoice (V1)")

print("\n--- Available Speakers ---")
if hasattr(model, 'list_available_spks'):
    spks = model.list_available_spks()
    print(spks)
else:
    print("list_available_spks not supported")

print("\n--- Testing Thai Synthesis (Cross-Lingual) ---")
text = "สวัสดีครับ วันนี้อากาศดีมาก"
prompt_wav_path = "Fun-Audio-Chat/third_party/CosyVoice/asset/zero_shot_prompt.wav"

if not os.path.exists(prompt_wav_path):
    print(f"Prompt wav not found: {prompt_wav_path}")
    sys.exit(1)

print(f"Using prompt wav: {prompt_wav_path}")

try:
    print(f"Synthesizing '{text}'...")
    # inference_cross_lingual(tts_text, prompt_wav, zero_shot_spk_id='', stream=False, speed=1.0)
    output = model.inference_cross_lingual(text, prompt_wav_path, stream=False)
    
    # Consume generator
    count = 0
    for item in output:
        count += 1
    print(f"Synthesis successful! Yielded {count} chunks.")

except Exception as e:
    print(f"Synthesis failed: {e}")
    import traceback
    traceback.print_exc()
