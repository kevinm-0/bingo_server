souls =["Dogen 005 - Isolated Platform down the hill", "Dogen 034 - Right of street", "Dogen 061 - Past Statue", "Dogen 092 - Grind x 10", "Dogen 117 - Air x 3", "Dogen 006 - Tricks x 20", "Dogen 035 - Points x 50k", "Dogen 062 - Special (Grind Avenue)", "Shibuya 007 - On top of bus", "Shibuya 093 - Cubby", "Shibuya 119 - Platform", "Shibuya 036 - Grind x 10", "Shibuya 063 - Air x 3", "Shibuya 094 - Tricks x 25", "Shibuya 121 - Points x 100k", "Shibuya 008 - Special (13 platforms)", "Chuo 037 - Right Canal", "Chuo 064 - Cubby", "Chuo 095 - South of Hayashi", "Chuo 122 - Grind x 10", "Chuo 009 - Air x 4", "Chuo 038 - Tricks x 30", "Chuo 065 - Points x 60k", "Chuo 096 - Special (G/W to end)", "RDH 010 - Top of station", "RDH 039 - Platform above Cops 2", "RDH 123 - Sauna", "RDH 067 - Grind x 10", "RDH 097 - Air x 4", "RDH 124 - Tricks x 35", "RDH 011 - Points x 40k", "RDH 040 - Special (Grind Lower Chimney)", "99th 068 - Center of Dark", "99th 098 - Light Wallride", "99th 126 - Wallride TO Dark", "99th 012 - Grind x 15", "99th 041 - Air x 4", "99th 069 - Tricks x 40", "99th 099 - Points x 100k", "99th 127 - Special (Perimeter of Tower)", "Sewers 013 - Entrance", "Sewers 042 - Center Structure", "Sewers 070 - Rail, Floor 1 to 2", "Sewers 100 - Grind x 10", "Sewers 128 - Air x 4", "Sewers 015 - Tricks x 45", "Sewers 043 - Points x 100k", "Sewers 071 - Special (Points x 150k)", "Btm pt. 016 - Catwalk, PJ Room 3", "Btm pt. 101 - Catwalk, near Cube", "Btm pt. 129 - Right halfpipe after winding rails", "Btm pt. 044 - Grind x 10", "Btm pt. 072 - Air x 4", "Btm pt. 102 - Tricks x 50", "Btm pt. 130 - Points x 50k", "Btm pt. 017 - Special (Points x 70k)", "Hikage 045 - Cubby", "Hikage 073 - Crane", "Hikage 103 - Center, floating", "Hikage 131 - Grind x 20", "Hikage 018 - Air x 4", "Hikage 046 - Tricks x 55", "Hikage 074 - Points x 300k", "Hikage 104 - Special (Crane, Top, Bottom)", "Kibo 019 - Under tower", "Kibo 047 - Lower platform, under wires", "Kibo 132 - Upper platform at end", "Kibo 076 - Grind x 20", "Kibo 105 - Air x 4", "Kibo 133 - Tricks x 60", "Kibo 021 - Points x 250k", "Kibo 049 - Special (Walk under gate at top)", "SDPP 077 - Top of Observatory", "SDPP 106 - Floating, Pink Halfpipes", "SDPP 134 - Entrance Pillar", "SDPP 022 - Grind x 20", "SDPP 050 - Air x 4", "SDPP 079 - Tricks x 65", "SDPP 107 - Points x 110k", "SDPP 135 - Special (Circle the Pharaoh)", "HWY0 023 - Directly under entrance", "HWY0 051 - Left alley near tall neon sign", "HWY0 080 - Trash Pit", "HWY0 108 - Grind x 15", "HWY0 136 - Air x 5", "HWY0 024 - Tricks x 70", "HWY0 052 - Points x 90k", "HWY0 081 - Special (Wallride alley)", "Sky Dino 026 - On top of T-rex", "Sky Dino 054 - Under Brontosaurus", "Sky Dino 109 - Platform near starting spiral", "Sky Dino 137 - Platform under first swing", "Sky Dino 082 - Grind x 50", "Sky Dino 110 - Air x 6", "Sky Dino 138 - Tricks x 100", "Sky Dino 027 - Points x 10k", "Sky Dino 055 - Special (Rail, Swing, Rail)", "FRZ 083 - 'Clip' soul, lower area", "FRZ 111 - Middle of upper area, down tube", "FRZ 139 - Very top, End of first Maze", "FRZ 028 - Grind x 10", "FRZ 056 - Air x 8", "FRZ 084 - Tricks x 100", "FRZ 112 - Points x 50k", "FRZ 140 - Special (Grind up the metal)"]
graffiti = ["Dogen Spray 100% GRAFFITI", "Shibuya Spray 100% GRAFFITI", "Chuo Spray 100% GRAFFITI", "RDH Spray 100% GRAFFITI", "99th Spray 100% GRAFFITI", "Sewers Spray 100% GRAFFITI", "Btm pt. Spray 100% GRAFFITI", "Hikage Spray 100% GRAFFITI", "Kibo Spray 100% GRAFFITI", "SDPP Spray 100% GRAFFITI", "HWY0 Spray 100% GRAFFITI", "Sky Dino Spray 100% GRAFFITI", "FRZ Spray 100% GRAFFITI"]
chars = ["RDH Unlock Rhyth", "Kibo Unlock Boogie", "HWY0 Unlock Soda", "Stadium Unlock Jazz", "Btm pt. Unlock Cube"]


import re




def extract_graffiti_id(entry):
    return entry.split(" Spray")[0].strip()

graffiti_map = {extract_graffiti_id(entry): entry for entry in graffiti}
char_map = {entry.split()[-1]: entry for entry in chars}

soul_map = {}
for entry in souls:
    match = re.search(r'\b(\d{3})\b', entry) 
    if match:
        soul_id = match.group(1)
        soul_map[soul_id] = entry

def soulFromID(data):
    _type = data['type']
    unlock = data['id']
    
    if _type == 'Graf':
        return graffiti_map.get(unlock, f"Unknown graffiti for id '{unlock}'")
    elif _type == 'Char':
        return char_map.get(unlock, f"Unknown character for id '{unlock}'")
    elif _type == 'Soul':
        unlock_str = f"{int(unlock):03}" 
        return soul_map.get(unlock_str, f"Unknown soul for id '{unlock}'")
    else:
        print("corrupt data:", data)
        return f"Unknown type '{_type}'"

