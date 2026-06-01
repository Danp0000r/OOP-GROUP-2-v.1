import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, ROOT_DIR)

from __init__ import create_app

from models.cpu import CPU

# Try importing optional component handlers
try:
    from models.gpu import GPU
except:
    GPU = None

try:
    from models.ram import RAM
except:
    RAM = None

try:
    from models.motherboard import Motherboard
except:
    Motherboard = None

try:
    from models.psu import PSU
except:
    PSU = None

try:
    from models.storage import Storage
except:
    Storage = None

try:
    from models.cooling import Cooling
except:
    Cooling = None

try:
    from models.case import Case
except:
    Case = None


# Folder containing models
MODELS_FOLDER = os.path.join(ROOT_DIR, "models")

required_models = [
    "component.py",
    "cpu.py",
    "gpu.py",
    "ram.py",
    "motherboard.py",
    "psu.py",
    "storage.py",
    "cooling.py",
    "case.py",
    "user.py",
    "build.py",
    "link.py"
]

print("\n========== MODEL CHECKER ==========\n")

# CHECK FILES
for model_file in required_models:

    path = os.path.join(MODELS_FOLDER, model_file)

    if not os.path.exists(path):

        print(f"❌ {model_file} -> FILE NOT FOUND")

    else:

        try:

            with open(path, "r", encoding="utf-8") as file:

                source = file.read()

                compile(source, model_file, "exec")

            print(f"✅ {model_file}")

        except Exception as e:

            print(f"❌ {model_file} -> ERROR")
            print(f"   {e}")

print("\n========== DATABASE CHECK ==========\n")

app = create_app()

with app.app_context():

    component_handlers = [
        ("CPU", CPU, "get_all_cpus"),
        ("GPU", GPU, "get_all_gpus"),
        ("RAM", RAM, "get_all_rams"),
        ("Motherboard", Motherboard, "get_all_motherboards"),
        ("PSU", PSU, "get_all_psus"),
        ("Storage", Storage, "get_all_storage"),
        ("Cooling", Cooling, "get_all_cooling"),
        ("Case", Case, "get_all_cases")
    ]

    for component_name, handler, method_name in component_handlers:

        print(f"[{component_name}]")

        if handler is None:

            print(" ❌ Model not implemented.\n")

            continue

        try:

            method = getattr(handler, method_name)

            components = method()

            if not components:

                print(" No components found.\n")

            else:

                for component in components:

                    print(f" • {component.name}")

                print()

        except Exception as e:

            print(f" ❌ Database read failed")
            print(f"   {e}\n")

print("=====================================\n")
input ();
