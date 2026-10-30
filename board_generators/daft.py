#==================================
#|                                |
#|   Quackthingo Python edition   |
#| v0.1 by DigitalDuck 2021-01-06 |
#|   Ruined by daft7 2022-03-17   |
#|                                |
#==================================

import copy
import random

goals = [['Dogen', '005 - Isolated Platform down the hill', 10], ['Dogen', '006 - Tricks x 20', 20], ['Shibuya', '007 - On top of bus', 10], ['Shibuya', '008 - Special (13 platforms)', 20], ['Chuo', '009 - Air x 4', 20], ['RDH', '010 - Top of station', 10], ['RDH', '011 - Points x 40k', 20], ['99th', '012 - Grind x 15', 20], ['Sewers', '013 - Entrance', 10], ['Sewers', '015 - Tricks x 45', 20], ['Btm pt.', '016 - Catwalk, PJ Room 3', 10], ['Btm pt.', '017 - Special (Points x 70k)', 20], ['Hikage', '018 - Air x 4', 20], ['Kibo', '019 - Under tower', 10], ['Kibo', '021 - Points x 250k', 20], ['SDPP', '022 - Grind x 20', 20], ['HWY0', '023 - Directly under entrance', 10], ['HWY0', '024 - Tricks x 70', 20], ['Sky Dino', '026 - On top of T-rex', 10], ['Sky Dino', '027 - Points x 10k', 20], ['FRZ', '028 - Grind x 10', 20], ['Dogen', '034 - Right of street', 10], ['Dogen', '035 - Points x 50k', 20], ['Shibuya', '036 - Grind x 10', 20], ['Chuo', '037 - Right Canal', 10], ['Chuo', '038 - Tricks x 30', 20], ['RDH', '039 - Platform above Cops 2', 10], ['RDH', '040 - Special (Grind Lower Chimney)', 20], ['99th', '041 - Air x 4', 20], ['Sewers', '042 - Center Structure', 10], ['Sewers', '043 - Points x 100k', 20], ['Btm pt.', '044 - Grind x 10', 20], ['Hikage', '045 - Cubby', 10], ['Hikage', '046 - Tricks x 55', 20], ['Kibo', '047 - Lower platform, under wires', 10], ['Kibo', '049 - Special (Walk under gate at top)', 20], ['SDPP', '050 - Air x 4', 20], ['HWY0', '051 - Left alley near tall neon sign', 10], ['HWY0', '052 - Points x 90k', 20], ['Sky Dino', '054 - Under Brontosaurus', 10], ['Sky Dino', '055 - Special (Rail, Swing, Rail)', 20], ['FRZ', '056 - Air x 8', 20], ['Dogen', '061 - Past Statue', 10], ['Dogen', '062 - Special (Grind Avenue)', 20], ['Shibuya', '063 - Air x 3', 20], ['Chuo', '064 - Cubby', 10], ['Chuo', '065 - Points x 60k', 20], ['RDH', '067 - Grind x 10', 20], ['99th', '068 - Center of Dark', 10], ['99th', '069 - Tricks x 40', 20], ['Sewers', '070 - Rail, Floor 1 to 2', 10], ['Sewers', '071 - Special (Points x 150k)', 20], ['Btm pt.', '072 - Air x 4', 20], ['Hikage', '073 - Crane', 10], ['Hikage', '074 - Points x 300k', 20], ['Kibo', '076 - Grind x 20', 20], ['SDPP', '077 - Top of Observatory', 10], ['SDPP', '079 - Tricks x 65', 20], ['HWY0', '080 - Trash Pit', 10], ['HWY0', '081 - Special (Wallride alley)', 20], ['Sky Dino', '082 - Grind x 50', 20], ['FRZ', "083 - 'Clip' soul, lower area", 10], ['FRZ', '084 - Tricks x 100', 20], ['Dogen', '092 - Grind x 10', 20], ['Shibuya', '093 - Cubby', 10], ['Shibuya', '094 - Tricks x 25', 20], ['Chuo', '095 - South of Hayashi', 10], ['Chuo', '096 - Special (G/W to end)', 20], ['RDH', '097 - Air x 4', 20], ['99th', '098 - Light Wallride', 10], ['99th', '099 - Points x 100k', 20], ['Sewers', '100 - Grind x 10', 20], ['Btm pt.', '101 - Catwalk, near Cube', 10], ['Btm pt.', '102 - Tricks x 50', 20], ['Hikage', '103 - Center, floating', 10], ['Hikage', '104 - Special (Crane, Top, Bottom)', 20], ['Kibo', '105 - Air x 4', 20], ['SDPP', '106 - Floating, Pink Halfpipes', 10], ['SDPP', '107 - Points x 110k', 20], ['HWY0', '108 - Grind x 15', 20], ['Sky Dino', '109 - Platform near starting spiral', 10], ['Sky Dino', '110 - Air x 6', 20], ['FRZ', '111 - Middle of upper area, down tube', 10], ['FRZ', '112 - Points x 50k', 20], ['Dogen', '117 - Air x 3', 20], ['Shibuya', '119 - Platform', 10], ['Shibuya', '121 - Points x 100k', 20], ['Chuo', '122 - Grind x 10', 20], ['RDH', '123 - Sauna', 10], ['RDH', '124 - Tricks x 35', 20], ['99th', '126 - Wallride TO Dark', 10], ['99th', '127 - Special (Perimeter of Tower)', 20], ['Sewers', '128 - Air x 4', 20], ['Btm pt.', '129 - Right halfpipe after winding rails', 10], ['Btm pt.', '130 - Points x 50k', 20], ['Hikage', '131 - Grind x 20', 20], ['Kibo', '132 - Upper platform at end', 10], ['Kibo', '133 - Tricks x 60', 20], ['SDPP', '134 - Entrance Pillar', 10], ['SDPP', '135 - Special (Circle the Pharaoh)', 20], ['HWY0', '136 - Air x 5', 20], ['Sky Dino', '137 - Platform under first swing', 10], ['Sky Dino', '138 - Tricks x 100', 20], ['FRZ', '139 - Very top, End of first Maze', 10], ['FRZ', '140 - Special (Grind up the metal)', 20], ['RDH', 'Unlock Rhyth', 40], ['Kibo', 'Unlock Boogie', 40], ['HWY0', 'Unlock Soda', 40], ['Stadium', 'Unlock Jazz', 40], ['Btm pt.', 'Unlock Cube', 40], ['Dogen', 'Spray 100% GRAFFITI', 100], ['Shibuya', 'Spray 100% GRAFFITI', 100], ['Chuo', 'Spray 100% GRAFFITI', 100], ['RDH', 'Spray 100% GRAFFITI', 100], ['99th', 'Spray 100% GRAFFITI', 100], ['Sewers', 'Spray 100% GRAFFITI', 100], ['Btm pt.', 'Spray 100% GRAFFITI', 100], ['Hikage', 'Spray 100% GRAFFITI', 100], ['Kibo', 'Spray 100% GRAFFITI', 100], ['SDPP', 'Spray 100% GRAFFITI', 100], ['HWY0', 'Spray 100% GRAFFITI', 100], ['Sky Dino', 'Spray 100% GRAFFITI', 100], ['FRZ', 'Spray 100% GRAFFITI', 100]]
 

# No need to reference file. Could be cleaner but it is portable.
# Contains all 105 in-level souls, 13 graffitis, and 5 character unlocks
def maingen():
   
    # Set desired number of graffiti squares. Set to 15 to retain randomness
    graffiti = 15

    # Initialize graffiti count for check, if used
    graffiti_count = 0

    # Pick 25 goals
    def goal_function():
        global goals
        goals_temp = goals
        seed = random.randint(0, 2147483647)
        random.seed(seed)
        board = []
        obj_string = []
        graffiti_count = 0
        for i in range(0, 25):
            index = random.randint(0, len(goals_temp)-1)
            board.append(goals_temp[index])
            goals_temp = goals_temp[:index]+goals_temp[index+1:]
            obj_string.append(board[i][1])
        board_string = '-'.join(obj_string)
        graffiti_count = board_string.count('graffiti')
        return seed, board, graffiti_count
        
    if graffiti == 15:
        seed, board, graffiti_count = goal_function()
    else:
        while graffiti != graffiti_count:
            seed, board, graffiti_count = goal_function()

    # Balance board
    indices = [[0,1,2,3,4],[5,6,7,8,9],[10,11,12,13,14],[15,16,17,18,19],[20,21,22,23,24],
                [0,5,10,15,20],[1,6,11,16,21],[2,7,12,17,22],[3,8,13,18,23],[4,9,14,19,24],
                [0,6,12,18,24],[4,8,12,16,20]]
    threshold = 0
    flag = True
    while flag:
        flag = False
        # Get weights of each line
        weights = []
        for i in range(0, 25):
            weights.append(board[i][2])
        linetotals = []
        lines = []
        for i in range(0, 12):
            linetotals.append(0)
            lines.append([])
            for j in range(0, 5):
                lines[i].append(weights[indices[i][j]])
                linetotals[i] += lines[i][j]
        # Find highest and lowest weighted lines
        maxweight = max(weights)
        maxtotal = max(linetotals)
        mintotal = min(linetotals)
        maxi = linetotals.index(maxtotal)
        mini = linetotals.index(mintotal)
        if maxtotal-mintotal > maxweight*threshold:
            # Not balanced enough, let's swap the biggest outliers
            maxj = lines[maxi].index(max(lines[maxi]))
            minj = lines[mini].index(min(lines[mini]))
            temp = copy.deepcopy(board[indices[maxi][maxj]])
            board[indices[maxi][maxj]] = copy.deepcopy(board[indices[mini][minj]])
            board[indices[mini][minj]] = copy.deepcopy(temp)
            # In order to prevent being stuck in a local minimum, we also do a random swap
            swap1 = random.randint(0, 24)
            swap2 = random.randint(0, 24)
            temp = copy.deepcopy(board[swap1])
            board[swap1] = copy.deepcopy(board[swap2])
            board[swap2] = copy.deepcopy(temp)
            # Increase threshold so we can always eventually escape
            threshold += 0.04
            flag = True
        # Create JSON
        infostring = []
        for square in board:
            ds = str(square[0]+' '+square[1].strip())
            infostring.append({"name": ds})

    return infostring