import yaml
print(f"PyYAML version: {yaml.__version__}")
try:
    from yaml import Loader
    print(f"Loader attributes: {dir(Loader)}")
    if hasattr(Loader, 'max_depth'):
        print("Loader has max_depth")
    else:
        print("Loader missing max_depth")
except ImportError:
    print("Could not import Loader from yaml")
