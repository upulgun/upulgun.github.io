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

COLORS = [
    "#C62828", "#AD1457", "#6A1B9A", "#4527A0", "#283593", 
    "#1565C0", "#0277BD", "#00838F", "#00695C", "#2E7D32", 
    "#558B2F", "#EF6C00", "#D84315", "#4E342E", "#37474F"
]

def clean_id(text):
    return re.sub(r'\s+', '', text).upper()

def generate_interactive_map(input_text):
    lines = [line.strip() for line in input_text.strip().split('\n') if line.strip()]
    subjects = {}
    
    for line in lines:
        parts = re.split(r'\t+', line)
        if len(parts) < 2: continue
        year, name = int(parts[0]), parts[1]
        sem = parts[2] if len(parts) > 2 else "All"
        prereqs = [clean_id(p) for p in parts[3:] if p.strip()]
        obj_id = clean_id(name)
        subjects[obj_id] = {"name": name, "year": year, "sem": sem, "prereqs": prereqs}

    # External Nodes logic
    external_nodes = {}
    for sid, info in list(subjects.items()):
        for p in info['prereqs']:
            if p not in subjects and p not in external_nodes:
                sem_val = "Ext_Autumn" if info['sem'] in ["Autumn", "All"] else "Ext_Spring"
                external_nodes[p] = {"name": p, "year": info['year'], "sem": sem_val, "prereqs": []}
    subjects.update(external_nodes)

    COL_MAP = {"Autumn": 0, "Ext_Autumn": 1, "All": 2, "Ext_Spring": 3, "Spring": 4}
    subject_colors = {sid: random.choice(COLORS) for sid in subjects}
    
    BOX_W, BOX_H = 115, 45
    X_GAP, Y_YEAR_GAP = 220, 260
    MARGIN_X, MARGIN_Y = 100, 70
    
    coords = {}
    buckets = {}
    for sid, info in subjects.items():
        key = (info['year'], COL_MAP[info['sem']])
        buckets.setdefault(key, []).append(sid)

    for (year, col_idx), sids in buckets.items():
        for i, sid in enumerate(sids):
            x = MARGIN_X + (col_idx * X_GAP)
            y = MARGIN_Y + (year * Y_YEAR_GAP) + (i * (BOX_H + 20))
            coords[sid] = (x, y, col_idx)

    svg_elements = []
    
    # Draw Paths with Source-Specific Classes
    for sid, info in subjects.items():
        if sid not in coords: continue
        x2, y2, col2 = coords[sid]
        for p in info['prereqs']:
            if p in coords:
                x1, y1, col1 = coords[p]
                color = subject_colors[p]
                
                # Apply the directional logic from previous step
                if col1 == 0 and col2 == 0: # Left Loop
                    path_d = f"M {x1} {y1 + BOX_H/2} C {x1 - 80} {y1 + BOX_H/2}, {x2 - 80} {y2 + BOX_H/2}, {x2} {y2 + BOX_H/2}"
                elif col1 == 4 and col2 == 4: # Right Loop
                    path_d = f"M {x1 + BOX_W} {y1 + BOX_H/2} C {x1 + BOX_W + 80} {y1 + BOX_H/2}, {x2 + BOX_W + 80} {y2 + BOX_H/2}, {x2 + BOX_W} {y2 + BOX_H/2}"
                elif col1 < col2: # Move Right
                    path_d = f"M {x1 + BOX_W} {y1 + BOX_H/2} C {x1 + BOX_W + 50} {y1 + BOX_H/2}, {x2 - 50} {y2 + BOX_H/2}, {x2} {y2 + BOX_H/2}"
                elif col1 > col2: # Move Left
                    path_d = f"M {x1} {y1 + BOX_H/2} C {x1 - 50} {y1 + BOX_H/2}, {x2 + BOX_W + 50} {y2 + BOX_H/2}, {x2 + BOX_W} {y2 + BOX_H/2}"
                else: # Default vertical
                    path_d = f"M {x1 + BOX_W/2} {y1 + BOX_H} Q {x1 + BOX_W/2 - 40} {(y1+y2+BOX_H)/2} {x2 + BOX_W/2} {y2}"

                # Key Change: class="from-{p}" links this line to its prerequisite box
                svg_elements.append(f'<path d="{path_d}" class="connector from-{p}" stroke="{color}" fill="none" marker-end="url(#arrowhead)" stroke-width="2" opacity="0.4" />')

    # Draw Boxes with Hover Events
    for sid, info in subjects.items():
        x, y, _ = coords[sid]
        color = subject_colors[sid]
        # Key Change: onmouseenter/onmouseleave triggers the highlight logic
        g_tag = f'<g class="node" id="node-{sid}" onmouseenter="syncHover(\'{sid}\', true)" onmouseleave="syncHover(\'{sid}\', false)">'
        rect = f'<rect x="{x}" y="{y}" width="{BOX_W}" height="{BOX_H}" fill="{color}" rx="8" style="transform-origin: {x + BOX_W/2}px {y + BOX_H/2}px" />'
        text = f'<text x="{x + BOX_W/2}" y="{y + BOX_H/2 + 5}" text-anchor="middle" font-family="sans-serif" font-size="10" font-weight="bold" fill="white" pointer-events="none">{info["name"]}</text>'
        svg_elements.append(f'{g_tag}{rect}{text}</g>')

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ background: #f4f7f6; display: flex; justify-content: center; padding: 40px; font-family: sans-serif; }}
            svg {{ background: white; border-radius: 15px; box-shadow: 0 20px 50px rgba(0,0,0,0.15); }}
            
            /* Subject Box Hover */
            .node rect {{ transition: transform 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275), filter 0.3s; cursor: pointer; }}
            .node.is-hovered rect {{ transform: scale(1.15); filter: brightness(1.1); box-shadow: 0 5px 15px rgba(0,0,0,0.3); }}
            
            /* Arrow Hover */
            .connector {{ transition: stroke-width 0.3s, opacity 0.3s, stroke 0.3s; pointer-events: none; }}
            .connector.highlight {{ stroke-width: 5; opacity: 1; }}
            
            .year-label {{ fill: #cbd5e0; font-weight: 800; font-size: 16px; pointer-events: none; }}
        </style>
        <script>
            function syncHover(sid, isEntering) {{
                const node = document.getElementById('node-' + sid);
                const arrows = document.querySelectorAll('.from-' + sid);
                
                if (isEntering) {{
                    node.classList.add('is-hovered');
                    arrows.forEach(a => a.classList.add('highlight'));
                }} else {{
                    node.classList.remove('is-hovered');
                    arrows.forEach(a => a.classList.remove('highlight'));
                }}
            }}
        </script>
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
    with open("synchronized_pathway.html", "w") as f: f.write(html)
    print("Interactive map generated: synchronized_pathway.html")

generate_interactive_map(data)