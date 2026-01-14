import json
import os
import math
import re

STATE_FILE = "state.json"
README_FILE = "README.md"

def load_state():
    if not os.path.exists(STATE_FILE):
        # Simpler Tetrahedron Shape
        return {
            "top":   [0.0,   0.0,  10.0],
            "front": [10.0, -6.0, -5.0],
            "left":  [-8.0,  6.0, -5.0],
            "right": [-8.0, -6.0, -5.0]
        }
    with open(STATE_FILE, "r") as f:
        return json.load(f)

def parse_issue_body():
    body = os.environ.get("ISSUE_BODY", "")
    lines = body.split('\n')
    
    vertex_name = None
    axis_name = None
    amount = 0.0
    
    for i, line in enumerate(lines):
        if line.strip() == "### Which point do you want to move?":
            vertex_name = lines[i+2].strip().lower()
        elif line.strip() == "### Which direction?":
            axis_name = lines[i+2].strip()
        elif line.strip() == "### Amount to move (Positive or Negative)":
            try:
                amount = float(lines[i+2].strip())
            except ValueError:
                amount = 0.0
                
    return vertex_name, axis_name, amount

def generate_stl_string(state):
    # Unpack vertices
    t = state["top"]
    f_pt = state["front"]
    l = state["left"]
    r = state["right"]

    stl_content = ["solid simple_tetrahedron"]

    def add_facet(v1, v2, v3):
        ux, uy, uz = v2[0]-v1[0], v2[1]-v1[1], v2[2]-v1[2]
        vx, vy, vz = v3[0]-v1[0], v3[1]-v1[1], v3[2]-v1[2]
        nx, ny, nz = uy*vz - uz*vy, uz*vx - ux*vz, ux*vy - uy*vx
        
        length = math.sqrt(nx*nx + ny*ny + nz*nz)
        if length == 0: length = 1
        
        stl_content.append(f"  facet normal {nx/length:.4f} {ny/length:.4f} {nz/length:.4f}")
        stl_content.append("    outer loop")
        for v in [v1, v2, v3]:
            stl_content.append(f"      vertex {v[0]:.4f} {v[1]:.4f} {v[2]:.4f}")
        stl_content.append("    endloop")
        stl_content.append("  endfacet")

    add_facet(t, f_pt, l)
    add_facet(t, l, r)
    add_facet(t, r, f_pt)
    add_facet(l, f_pt, r)

    stl_content.append("endsolid")
    return "\n".join(stl_content)

def update_readme(new_stl):
    with open(README_FILE, "r") as f:
        content = f.read()

    pattern = r"()(.*?)()"
    
    # FIX: We explicitly add the ```stl and ``` fences here
    # This ensures the output is always a valid code block
    replacement = f"\\1\n```stl\n{new_stl}\n```\n\\3"
    
    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    with open(README_FILE, "w") as f:
        f.write(new_content)

if __name__ == "__main__":
    state = load_state()
    
    if "ISSUE_BODY" in os.environ:
        v_name, axis_str, amount = parse_issue_body()
        axis_idx = 0
        if "Y" in axis_str: axis_idx = 1
        if "Z" in axis_str: axis_idx = 2
        
        if v_name in state:
            state[v_name][axis_idx] += amount
            with open(STATE_FILE, "w") as f:
                json.dump(state, f, indent=2)

    stl_data = generate_stl_string(state)
    update_readme(stl_data)
