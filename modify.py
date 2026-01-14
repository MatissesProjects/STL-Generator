import json
import os
import sys

STATE_FILE = "state.json"

def hex_to_rgb(hex_str):
    """Converts #FF5733 to (1.0, 0.34, 0.2)"""
    hex_str = hex_str.lstrip('#')
    return tuple(int(hex_str[i:i+2], 16) / 255.0 for i in (0, 2, 4))

def load_state():
    if not os.path.exists(STATE_FILE):
        return {"radius": 10, "height": 15, "color": "#0099FF"}
    with open(STATE_FILE, "r") as f:
        return json.load(f)

def parse_issue_body():
    """Reads the issue body passed as an environment variable"""
    body = os.environ.get("ISSUE_BODY", "")
    lines = body.split('\n')
    
    # Simple parser to find data under the headers defined in the YAML
    operation = None
    value = None
    
    for i, line in enumerate(lines):
        if line.strip() == "### What do you want to change?":
            # The next non-empty line is the selection
            operation = lines[i+2].strip()
        if line.strip() == "### New Value":
            value = lines[i+2].strip()
            
    return operation, value

def update_model(state):
    radius = float(state["radius"])
    height = float(state["height"])
    r, g, b = hex_to_rgb(state["color"])

    # 1. Write Material File (.mtl)
    with open("model.mtl", "w") as f:
        f.write("newmtl CrystalMat\n")
        f.write("Ns 96.078\n") # Shininess
        f.write("Ka 1.000 1.000 1.000\n") # Ambient
        f.write(f"Kd {r:.3f} {g:.3f} {b:.3f}\n") # Diffuse Color (The one that matters)
        f.write("Ks 0.500 0.500 0.500\n") # Specular
        f.write("d 1.0\n") # Opacity
        f.write("illum 2\n")

    # 2. Write Geometry File (.obj)
    with open("model.obj", "w") as f:
        f.write("mtllib model.mtl\n") # Link to the color file
        f.write(f"# Crystal State: R={radius} H={height}\n")
        
        # Vertices
        f.write(f"v 0 0 {height}\n")   # Top
        f.write(f"v {radius} 0 0\n")   # Waist 1
        f.write(f"v 0 {radius} 0\n")   # Waist 2
        f.write(f"v -{radius} 0 0\n")  # Waist 3
        f.write(f"v 0 -{radius} 0\n")  # Waist 4
        f.write(f"v 0 0 -{height}\n")  # Bottom

        # Faces with Material
        f.write("usemtl CrystalMat\n")
        # Top Pyramid
        f.write("f 1 2 3\n")
        f.write("f 1 3 4\n")
        f.write("f 1 4 5\n")
        f.write("f 1 5 2\n")
        # Bottom Pyramid
        f.write("f 6 3 2\n")
        f.write("f 6 4 3\n")
        f.write("f 6 5 4\n")
        f.write("f 6 2 5\n")

if __name__ == "__main__":
    state = load_state()
    
    # Check if we are running inside the GitHub Action (updating)
    if "ISSUE_BODY" in os.environ:
        op, val = parse_issue_body()
        print(f"Processing: {op} -> {val}")
        
        if op == "Change Color":
            state["color"] = val # Expecting Hex
        elif op == "Update Height":
            state["height"] = float(val)
        elif op == "Update Radius":
            state["radius"] = float(val)
            
        # Save new state
        with open(STATE_FILE, "w") as f:
            json.dump(state, f, indent=2)

    # Always regenerate the 3D files
    update_model(state)