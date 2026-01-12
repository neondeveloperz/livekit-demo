import torch
import torchaudio
import os

try:
    print(f"Torchaudio version: {torchaudio.__version__}")
    print(f"Torchaudio backends: {torchaudio.list_audio_backends()}")
    
    # Create a dummy wav
    sample_rate = 16000
    waveform = torch.randn(1, 16000)
    torchaudio.save("test.wav", waveform, sample_rate)
    
    print("Testing load with soundfile...")
    wf, sr = torchaudio.load("test.wav", backend="soundfile")
    print(f"Loaded with soundfile. SR: {sr}, Shape: {wf.shape}")
    
    # print("Testing load default...")
    # wf, sr = torchaudio.load("test.wav")
    # print(f"Loaded default. SR: {sr}, Shape: {wf.shape}")

    os.remove("test.wav")
except Exception as e:
    print(f"Error: {e}")
