import re
import random

data = """
0	MATH 1021	All		
1	ELEC 1003	Spring		
1	ELEC 1006	Autumn		
1	ENGR 1018	Spring		
1	ENGR 1011	Autumn		
1	ENGR 1024	Autumn		
1	MATH 1016	All	MATH1021	 readiness_test
1	MATH 1019	All	MATH1016	
1	PROC 1008	Spring		
2	ELEC 1001	Autumn		
2	ELEC 2001	Autumn	ELEC1003	MATH1019
2	ELEC 2004	Autumn	ELEC1003	
2	ELEC 2006	Spring	MATH1019	ENGR1011
2	ELEC 2009	Spring	ELEC1001	
2	ELEC 2011	Autumn	MATH1019	ELEC1003
2	ELEC 3011	Spring	ELEC2001	
2	ENGR 3006	Spring	ELEC2011	
3	ELEC 2007	Autumn	ELEC1006	ELEC2009
3	ELEC 3001	Autumn	ELEC2011	
3	ELEC 3002	Spring	ELEC2011	
3	ELEC 3003	Spring	ELEC2011	
3	ELEC 3004	Spring	ELEC1001	
3	ELEC 3006	Autumn	ELEC3011	
3	ELEC 3009	Spring	ELEC3011 	
4	ENGR 3004	Spring	ELEC2001	
4	ELEC 4002	Autumn	ELEC2004	
4	ELEC 4003	Autumn	150CPs	
4	ELEC 4004	Spring	ELEC3001	
4	ELEC 4005	Autumn	ELEC3009	
4	ELEC 4006	Spring		
4	ELEC 4007	Autumn	ELEC3001	
4	ELEC 4008	Spring	ELEC3006	
4	ELEC 4009	Spring	ELEC2001	
4	ENGR 4041	All	200CPs	
4	ENGR 4042	All	ENGR4041	
"""

# Professional palette
COLORS = [
    "#C62828", "#AD1457", "#6A1B9A", "#4527A0", "#283593", 
    "#1565C0", "#0277BD", "#00838F", "#00695C", "#2E7D32", 
    "#558B2F", "#EF6C00", "#D84315", "#4E342E", "#37474F"
]

def clean_id(text):
    return re.sub(r'\s+', '', text).upper()

def generate_exterior_loop_map(input_text):
    lines = [line.strip() for line in input_text.strip().split('\n') if line.strip()]
    subjects = {}
    
    # 1. Parsing
    for line in lines:
        parts = re.split(r'\t+', line)
        if len(parts) < 2: continue
        year = int(parts[0])
        name = parts[1]
        sem = parts[2] if len(parts) > 2 else "All"
        prereqs = [clean_id(p) for p in parts[3:] if p.strip()]
        obj_id = clean_id(name)
        subjects[obj_id] = {"name": name, "year": year, "sem": sem, "prereqs": prereqs, "ext": False}

    # 2. External Nodes
    external_nodes = {}
    for sid, info in list(subjects.items()):
        for p in info['prereqs']:
            if p not in subjects and p not in external_nodes:
                sem_val = "Ext_Autumn" if info['sem'] in ["Autumn", "All"] else "Ext_Spring"
                external_nodes[p] = {"name": p, "year": info['year'], "sem": sem_val, "prereqs": [], "ext": True}
    subjects.update(external_nodes)

    # 3. Layout Constants
    # Columns: 0:Autumn, 1:Ext_Aut, 2:All, 3:Ext_Spr, 4:Spring
    COL_MAP = {"Autumn": 0, "Ext_Autumn": 1, "All": 2, "Ext_Spring": 3, "Spring": 4}
    subject_colors = {sid: random.choice(COLORS) for sid in subjects}
    
    BOX_W, BOX_H = 115, 45
    X_GAP, Y_YEAR_GAP = 220, 260
    MARGIN_X, MARGIN_Y = 100, 70
    
    buckets = {}
    for sid, info in subjects.items():
        key = (info['year'], COL_MAP[info['sem']])
        buckets.setdefault(key, []).append(sid)

    coords = {}
    for (year, col_idx), sids in buckets.items():
        for i, sid in enumerate(sids):
            x = MARGIN_X + (col_idx * X_GAP)
            y = MARGIN_Y + (year * Y_YEAR_GAP) + (i * (BOX_H + 20))
            coords[sid] = (x, y, col_idx)

    # 4. SVG Drawing
    svg_elements = []
    
    # Year background markers
    for year in range(5):
        y_pos = MARGIN_Y + (year * Y_YEAR_GAP) + 20
        svg_elements.append(f'<text x="20" y="{y_pos}" font-family="sans-serif" font-size="14" fill="#ddd" font-weight="bold">YEAR {year}</text>')

    # Draw Paths
    for sid, info in subjects.items():
        if sid not in coords: continue
        x2, y2, col2 = coords[sid]
        
        for p in info['prereqs']:
            if p in coords:
                x1, y1, col1 = coords[p]
                color = subject_colors[p]
                
                # Logic: Same Column Loop for Autumn (Left-to-Left)
                if col1 == 0 and col2 == 0:
                    start_x, start_y = x1, y1 + BOX_H/2
                    end_x, end_y = x2, y2 + BOX_H/2
                    # Curve outward to the left margin
                    path_d = f"M {start_x} {start_y} C {start_x - 80} {start_y}, {end_x - 80} {end_y}, {end_x} {end_y}"
                
                # Logic: Same Column Loop for Spring (Right-to-Right)
                elif col1 == 4 and col2 == 4:
                    start_x, start_y = x1 + BOX_W, y1 + BOX_H/2
                    end_x, end_y = x2 + BOX_W, y2 + BOX_H/2
                    # Curve outward to the right margin
                    path_d = f"M {start_x} {start_y} C {start_x + 80} {start_y}, {end_x + 80} {end_y}, {end_x} {end_y}"

                # Logic: Moving Right (Across columns)
                elif col1 < col2:
                    start_x, start_y = x1 + BOX_W, y1 + BOX_H/2
                    end_x, end_y = x2, y2 + BOX_H/2
                    path_d = f"M {start_x} {start_y} C {start_x + 50} {start_y}, {end_x - 50} {end_y}, {end_x} {end_y}"

                # Logic: Moving Left (Across columns)
                elif col1 > col2:
                    start_x, start_y = x1, y1 + BOX_H/2
                    end_x, end_y = x2 + BOX_W, y2 + BOX_H/2
                    path_d = f"M {start_x} {start_y} C {start_x - 50} {start_y}, {end_x + 50} {end_y}, {end_x} {end_y}"

                # Logic: Default vertical for "All" or same gutter
                else:
                    start_x, start_y = x1 + BOX_W/2, y1 + BOX_H
                    end_x, end_y = x2 + BOX_W/2, y2
                    path_d = f"M {start_x} {start_y} Q {start_x - 40} {(start_y+end_y)/2} {end_x} {end_y}"

                svg_elements.append(f'<path d="{path_d}" stroke="{color}" fill="none" marker-end="url(#arrowhead)" stroke-width="2.5" opacity="0.65" />')

    # Draw Boxes
    for sid, info in subjects.items():
        x, y, _ = coords[sid]
        color = subject_colors[sid]
        rect = f'<rect x="{x}" y="{y}" width="{BOX_W}" height="{BOX_H}" fill="{color}" rx="8" />'
        text = f'<text x="{x + BOX_W/2}" y="{y + BOX_H/2 + 5}" text-anchor="middle" font-family="sans-serif" font-size="10" font-weight="bold" fill="white">{info["name"]}</text>'
        svg_elements.append(f'<g class="node">{rect}{text}</g>')

    # 5. HTML Wrapper
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ background: #f8f9fa; display: flex; justify-content: center; padding: 30px; }}
            svg {{ background: white; border-radius: 15px; box-shadow: 0 20px 40px rgba(0,0,0,0.1); }}
            path {{ transition: stroke-width 0.2s, opacity 0.2s; }}
            path:hover {{ stroke-width: 6; opacity: 1; }}
            .node:hover rect {{ filter: brightness(1.15); cursor: default; }}
        </style>
    </head>
    <body>
        <svg width="1300" height="1550" viewBox="0 0 1300 1550">
            <defs>
                <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="10" refY="3.5" orient="auto">
                    <polygon points="0 0, 10 3.5, 0 7" fill="context-stroke" />
                </marker>
            </defs>
            {chr(10).join(svg_elements)}
        </svg>
    </body>
    </html>
    """
    with open("exterior_loop_pathway.html", "w") as f: f.write(html)
    print("Map generated: exterior_loop_pathway.html")

generate_exterior_loop_map(data)