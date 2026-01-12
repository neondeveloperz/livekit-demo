import yaml
import sys

print(f"PyYAML version: {yaml.__version__}")
try:
    from yaml import CLoader
    print("CLoader is available")
except ImportError:
    print("CLoader is NOT available")

print(f"yaml.Loader is: {yaml.Loader}")

# Try the patch
print("Applying patch...")
try:
    setattr(yaml.Loader, 'max_depth', 10000)
    print("Set max_depth on yaml.Loader class.")
except Exception as e:
    print(f"Failed to set on class: {e}")

# Instantiate
try:
    loader = yaml.Loader("")
    print(f"Instance created: {loader}")
    if hasattr(loader, 'max_depth'):
        print(f"Instance has max_depth: {loader.max_depth}")
    else:
        print("Instance does NOT have max_depth")
except Exception as e:
    print(f"Instantiation failed: {e}")

# Check with HyperPyYAML if possible
try:
    import hyperpyyaml
    print(f"HyperPyYAML version: {hyperpyyaml.__version__}")
except AttributeError:
    print("HyperPyYAML imported but has no __version__")
except ImportError:
    print("HyperPyYAML not found")

try:
    import ruamel.yaml
    print(f"ruamel.yaml imported. Loader: {ruamel.yaml.Loader}")
    
    print("Applying patch to ruamel.yaml...")
    setattr(ruamel.yaml.Loader, 'max_depth', 10000)
    print("Set max_depth on ruamel.yaml.Loader class.")
    
    r_loader = ruamel.yaml.Loader("")
    if hasattr(r_loader, 'max_depth'):
        print(f"ruamel instance has max_depth: {r_loader.max_depth}")
    else:
        print("ruamel instance does NOT have max_depth")
        
except ImportError:
    print("ruamel.yaml not found")
except Exception as e:
    print(f"Failed to patch/test ruamel.yaml: {e}")
