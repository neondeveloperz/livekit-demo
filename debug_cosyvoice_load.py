import sys
import os
import yaml

# Apply patches first
def patch_yaml():
    loaders = ['Loader', 'SafeLoader', 'CLoader', 'CSafeLoader', 'FullLoader', 'UnsafeLoader']
    for name in loaders:
        try:
            loader_cls = getattr(yaml, name, None)
            if loader_cls:
                setattr(loader_cls, 'max_depth', 10000)
        except Exception:
            pass
    try:
        import ruamel.yaml
        for name in ['Loader', 'SafeLoader', 'RoundTripLoader']:
            try:
                loader_cls = getattr(ruamel.yaml, name, None)
                if loader_cls:
                    setattr(loader_cls, 'max_depth', 10000)
            except Exception:
                pass
    except ImportError:
        pass

patch_yaml()

# Setup paths
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# Assuming this script is in livekit-demo/
PROJECT_ROOT = CURRENT_DIR
# Adjust if needed based on where script is run. User said fun_audio is in agent/ 
# but if I put this in livekit-demo/, then:
# CosyVoice is in Fun-Audio-Chat/third_party/CosyVoice

COSYVOICE_PATH = os.path.join(PROJECT_ROOT, "Fun-Audio-Chat/third_party/CosyVoice")
if COSYVOICE_PATH not in sys.path:
    print(f"Adding to sys.path: {COSYVOICE_PATH}")
    sys.path.append(COSYVOICE_PATH)

try:
    from cosyvoice.cli.cosyvoice import CosyVoice, CosyVoice3
    
    # Path to model
    model_path = os.path.join(PROJECT_ROOT, "Fun-Audio-Chat/pretrained_models/Fun-CosyVoice3-0.5B-2512")
    print(f"Attempting to load CosyVoice from: {model_path}")
    
    if not os.path.exists(model_path):
        print("ERROR: Path does not exist!")
    else:
        # Check for CosyVoice3 specifically
        if os.path.exists(os.path.join(model_path, 'cosyvoice3.yaml')):
             print("Detected CosyVoice3, using CosyVoice3 class.")
             model = CosyVoice3(model_path)
        else:
             print("Using generic CosyVoice class.")
             model = CosyVoice(model_path)
             
        print("Successfully loaded CosyVoice model!")
        
        if hasattr(model, 'list_available_spks'):
            spks = model.list_available_spks()
            print(f"Available speakers ({len(spks)}): {spks}")
        else:
            print("Model does not have list_available_spks method.")
        
except Exception as e:
    print(f"Caught exception: {e}")
    import traceback
    traceback.print_exc()
