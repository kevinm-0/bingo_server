import asyncio
import websockets
import json
from pathlib import Path
import datetime as dt
import signal
import sys
import re
import copy
import time

from kevingo_pocketbase import committodb
from soul_identifier import soulFromID
from board_generators.daft import maingen as daftgen
from board_generators.bgen import BGen

import dotenv

HEX_COLOR_PATTERN = re.compile(r'^#(?:[0-9a-fA-F]{3}){1,2}$')
bingochance = [[0, 1, 2, 3, 4], [5, 6, 7, 8, 9], [10, 11, 12, 13, 14], 
               [15, 16, 17, 18, 19], [20, 21, 22, 23, 24], [0, 5, 10, 15, 20], 
               [1, 6, 11, 16, 21], [2, 7, 12, 17, 22], [3, 8, 13, 18, 23], 
               [4, 9, 14, 19, 24], [0, 6, 12, 18, 24], [4, 8, 12, 16, 20]]

colors = [{ "#D3D3D3": "#D3D3D3" },
{ "#ff4f4f" : "#DB1111" },
{ "#4fd6ff": "#195BD7" },
{"#80ff93": "#159C0E" },
{ "#ff80fd": "#FF69B4" },
{ "#a480ff": "#8013E0" }]


class IRCChatServer:
    def __init__(self, host='0.0.0.0', port=12001):
        self.clients = {}
        self.host = host
        self.port = port
        self.messages_file = Path('messages.json')
        self.load_messages()
        self.board_file = Path("board.json")
        self.load_board()
        self.bgen = BGen("bgen_history.json")
        self.teams = []
        self.game_active = False
        self.start_time = None
        self.automark_names = []
        self.queue = []
        self.lastsnipe = None
        self.snipenumber = 0
        self.timer_active = False
        self.pause_active = False
        self.pause_start_time = None
        self.game_task = None

    def has_won(self, board, teams):
        #calculate points per team
        team_points = {}
        for square in board:
            color = square['color']
            if color != "#101010":  #ignore empty squares
                team_points[color] = team_points.get(color, 0) + 1

        if not team_points:
            return None  #no winner if no points

        #determine the team with the most points
        winner = max(team_points, key=team_points.get)
        winnerUsers = []
        for player in teams:
            if player['team'] == winner:
                winnerUsers.append(player['name'])
        

        self.game_active = False
        duration = (time.time_ns() - self.start_time) /1000
        if duration > 1:
            committodb(self.init_board[:], self.queue[:], winnerUsers, duration, self.start_time, self.teams)
        
        return winner


    def load_messages(self):
        
        if self.messages_file.exists():
            with open(self.messages_file, 'r') as f:
                try:
                    self.messages = json.load(f)
                except json.JSONDecodeError:
                    self.messages = []
        else:
            self.messages = []

    def load_board(self):
    #load board data from board.json file.
        if self.board_file.exists():
            with open(self.board_file, 'r') as f:
                try:
                    self.board = json.load(f)
                    # ensure that each board item has a 'color' field
                    for item in self.board:
                        if 'color' not in item:
                            item['color'] = "#101010"  # default color
                    self.init_board = copy.deepcopy(self.board)  # make a deep copy
                
                except json.JSONDecodeError:
                    print("Invalid JSON in board.json. Initializing default board.")
                    self.initialize_default_board()
        else:
            print("board.json file not found. Initializing default board.")
            self.initialize_default_board()


    def initialize_default_board(self):
        
        default_names = [f"Tile-{i+1}" for i in range(25)]
        self.board = [{"name": name, "color": "#101010"} for name in default_names]
        self.save_board()
        self.init_board = self.board

    def save_messages(self):
        
        with open(self.messages_file, 'w') as f:
            json.dump(self.messages, f, indent=4)

    def save_board(self):
        with open(self.board_file, 'w') as f:
            json.dump(self.board, f, indent=4)

    async def send_teams(self, websocket):
        if self.teams:
            await websocket.send(json.dumps({"type": "user_list", "data": self.teams}))

    async def register(self, websocket, username):
        self.clients[websocket] = username
        await self.send_previous_messages(websocket)
        await self.send_board(websocket)
        await self.send_teams(websocket)
        await self.send_time(websocket)
        print(f"New client connected: {websocket.remote_address} as {username}")

    async def unregister(self, websocket):

        username_data = self.clients.pop(websocket, "Unknown")
        
        #check if username_data is actually JSON and extract the username
        try:
            username = json.loads(username_data).get("username", "Unknown")
        except json.JSONDecodeError:
            username = username_data  # If it's not JSON, use it as is
        
        #filter out the player by username
        self.teams = [player for player in self.teams if player.get('name') != username]

        if username == "automarker":
            self.automark_names = []
            await self.set_automark(self.automark_names)
        
        if self.teams == []:
            self.game_active = False
        
        await self.broadcast(json.dumps({"type": "user_list", "data": self.teams}))
        print(f"Client disconnected: {websocket.remote_address} ({username})")

        await websocket.close()

    async def send_previous_messages(self, websocket):
        
        if self.messages:
            await websocket.send(json.dumps({"type": "history", "data": self.messages}))

    async def send_time(self, websocket):
        try :   
            if self.game_active:
                await websocket.send(json.dumps({"type" : "game_start", "data" : { "result": "true", "timestamp": str(self.start_time)} }))
        except Exception as e:
            print(f"Error sending time {e}")
    async def send_board(self, websocket):
        
        if self.board:
            await websocket.send(json.dumps({"type": "board", "data": self.board}))

    async def broadcast(self, message):
        if not self.clients:
            return

        dead_clients = []

        async def send_safe(client):
            try:
                await client.send(message)
            except Exception as e:
                dead_clients.append(client)
                print(f"Client disconnected: {e}")

        await asyncio.gather(*(send_safe(client) for client in self.clients))

        for client in dead_clients:
            await self.unregister(client)

    # blegh get usernanme
    def client_username(self, username_data):
        try:
            return json.loads(username_data).get("username", "Unknown")
        except json.JSONDecodeError:
            return username_data

    def connected_username(self, websocket):
        return self.client_username(self.clients.get(websocket, "Unknown"))

    # Broadcast clone to only send to automarker
    async def broadcast_to_automarker(self, message):
        if not self.clients:
            return

        dead_clients = []

        async def send_safe(client):
            try:
                await client.send(message)
            except Exception as e:
                dead_clients.append(client)
                print(f"Client disconnected: {e}")

        automarker_clients = [
            client
            for client, username_data in self.clients.items()
            if self.client_username(username_data) == "automarker"
        ]

        await asyncio.gather(*(send_safe(client) for client in automarker_clients))

        for client in dead_clients:
            await self.unregister(client)

    async def broadcast_board(self, new):
        if self.clients:
            message_type = "new_board" if new else "board"
            board_message = json.dumps({"type": message_type, "data": self.board})
            await self.broadcast(board_message)


    async def detect_snipes(self):
        seen = {}
        msgs = []
        for entry in self.queue:
            idx = entry['index']
            user = entry['user']
            time = entry['time']
            
            if idx in seen:
                previous = seen[idx]
                target = f"{previous['user']}"
                time_diff = (time - previous['time']) / 1000
                if user != target:
                    message = json.dumps({"sniper" : target, "sniped" : user, "goal" : self.board[idx].get('name'), "time" :  time_diff})
                    msgs.append((message))
            seen[idx] = entry
        
        self.snipenumber = len(msgs)
        if len(msgs) > 0:
            self.lastsnipe = msgs[-1]
        return msgs

    async def pause_game(self):
        self.pause_time = time.time_ns()
        self.pause_active = True
        print("paused!!")
        await self.broadcast(json.dumps({
            "type" : "pause",
            "data" : {
                "pause_time" : self.pause_time
            }
        }))
    
    async def unpause_game(self):
        self.pause_active = False
        print("unpaused!!")
        await self.broadcast(json.dumps({
            "type" : "unpause"
        }))

    async def handle_message(self, message):
        
        try:
            #get username and message content
            username = message["username"]
            content = message["content"]
            color = next((k for d in colors for k, v in d.items() if v == message.get("selectedColor")), "#ffffff")
            if content == "gg":
                if self.game_active or self.timer_active :
                    result = self.has_won(self.board, self.teams) if self.game_active else None
                    await self.stop_game(reason="manual", winner=result)
            elif content == "start":
                await self.check_game_start()
            elif content == "snipes":
                return
            elif content == "pause":
                if self.game_active or self.timer_active:
                    print("pausing..")
                    await self.pause_game()
                    print("pawsed")
            elif content == "unpause":
                if self.pause_active:
                    await self.unpause_game()
            elif content == "autokick":
                await self.kick({"kicker" : username, "user" : "automarker"})
                return


            
            #prepare to export message content
            message_data = {}
            message_data["content"] = content
            message_data["username"] = username
            message_data["color"] = color
            message_data["timestamp"] = str(dt.datetime.now(dt.UTC))
            if self.game_active:
                message_data["in_game_time"] = (time.time_ns() - self.start_time) // 1000000000
            else:
                message_data["in_game_time"] = None
            #save formatted data
            self.messages.append(message_data)
            self.save_messages()
            #broadcast to everyone
            await self.broadcast(json.dumps({"type": "message", "data": message_data}))
        except json.JSONDecodeError:
            print("Received an invalid JSON message.")
        except Exception as e:
            print(f"Error handling message: {e}")


    async def handle_board_update(self, websocket, update_data, automark):
        try:
            data = update_data.get("data", {})

            index = data.get("index")
            new_color = data.get("color")
            user = data.get("user")
            time_val = data.get("timern")

            print(index, user, time_val, new_color)

            if index is None or new_color is None:
                print("Invalid board update data received.")
                return

            if not HEX_COLOR_PATTERN.match(new_color):
                print(f"Invalid color code received: {new_color}")
                return

            if not (0 <= index < len(self.board)):
                print(f"Board index {index} out of range.")
                return

            #ADD TO GAME QUEUE
            self.queue.append({
                "index": index,
                "color": new_color,
                "user": user,
                "time": time_val,
                "source": "automark" if automark else "manual"
            })

            self.queue.sort(key=lambda x: x["time"])

            updated_board = copy.deepcopy(self.init_board)

            curr_snipes = 0

            for event in self.queue:
                i = event["index"]
                color = event["color"]
                source = event["source"]

                tile = updated_board[i]

                #MANUAL MARK / UNMARK CAN DO WHATEVER THEY WANT
                if source == "manual":
                    if tile["color"] == color: #UNMARK
                        tile["color"] = "#101010" 
                    elif tile["color"] == "#101010": #MARK THAT SHIT
                        tile["color"] = color
                else: #AUTOMARK IS FREAKY
                    if tile["color"] == "#101010": #THIS IS MARKING A SQUARE IM HAPPY
                        tile["color"] = color
                    else:
                        curr_snipes += 1
    
            #SNIPE DETECTION 
            if curr_snipes != self.snipenumber:
                print("snipe detected!")
                await self.detect_snipes()
                await self.broadcast(json.dumps({"type" : "notification", "data" : {
                    "type" : "snipe",
                    "data" : self.lastsnipe
                    }}))
                
            #LOGGING
            if self.board != updated_board:
                tile_name = self.board[index]['name']
                marked = new_color != "#101010"

                action = "marked" if marked else "unmarked"
                auto_text = " [AUTOMARK]" if automark else ""

                update_log = f"{auto_text} {user} {action} {tile_name}"

                await self.handle_message({
                    'content': update_log,
                    'username': user,
                    'selectedColor': new_color
                })

                if marked:
                    await self.broadcast(json.dumps({"type" : "square_marked", "data" : {
                        "user": user,
                        "text": tile_name,
                        "index": index,
                        "source": "automark" if automark else "manual"
                    }}))


            self.board = updated_board
            self.save_board()
            await self.broadcast_board(False)

        except Exception as e:
            print(f"Error handling board update: {e}")



    async def handle_new_board(self, new_board_data):
        try:
            print(new_board_data)
            self.board = new_board_data
            self.bgen.record_board(new_board_data)
            self.snipenumber = 0
            self.queue.clear()
            for item in self.board:
                if not item.get('name'):
                    item['name'] = f"Tile-{self.board.index(item) + 1}"
                if 'color' not in item:
                    item['color'] = "#101010"  
            self.save_board()
            await self.broadcast_board(True)
            self.init_board = new_board_data
            print("New board created and broadcasted.")
            await self.broadcast(json.dumps({
                "type": "user_list",
                "data": self.teams
                }))
        except Exception as e:
            print(f"Error creating new board: {e}")
    
    async def team_handler(self, websocket, data):
        
        name = data.get("user")
        new_team = data.get("color")

        if not name or not new_team:
            await websocket.send("Invalid data format")
            return

    
        if new_team == "spectator":
    
            self.teams = [player for player in self.teams if player['name'] != name]
        else:
          
            existing_player = next((player for player in self.teams if player['name'] == name), None)

            if existing_player:
                if existing_player['team'] != new_team:
                    existing_player['ready_for_next_match'] = False
                existing_player['team'] = new_team
            else:
     
                self.teams.append({
                    "name": name,
                    "team": new_team,
                    "automark": False,
                    "ready_for_next_match": False,
                })
        
        #set automark also broadcasts teams
        await self.set_automark(self.automark_names)

    async def set_automark(self, names):
        
        for player in self.teams:
            if player['name'] in names:
                player['automark'] = True
            else:
                player['automark'] = False
        await self.broadcast(json.dumps({
            "type": "user_list",
            "data": self.teams  
        }))

    async def set_next_match_ready(self, websocket, data):
        ready = data.get("ready")
        if not isinstance(ready, bool):
            await websocket.send(json.dumps({
                "type": "error",
                "data": {"message": "ready must be a boolean"},
            }))
            return

        username = self.connected_username(websocket)
        player = next((player for player in self.teams if player["name"] == username), None)
        if player is None:
            return

        player["ready_for_next_match"] = ready
        await self.broadcast(json.dumps({
            "type": "user_list",
            "data": self.teams,
        }))

    async def reset_next_match_ready(self):
        changed = False
        for player in self.teams:
            if player.get("ready_for_next_match", False):
                player["ready_for_next_match"] = False
                changed = True

        if changed:
            await self.broadcast(json.dumps({
                "type": "user_list",
                "data": self.teams,
            }))
    
    
    async def stop_game(self, reason="manual", winner=None):
        self.game_active = False
        self.timer_active = False
        self.pause_active = False

        task = self.game_task
        if task and task is not asyncio.current_task():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        await self.broadcast(json.dumps({
            "type": "result",
            "data": {
                "winner": winner,
                "reason": reason,
                "timestamp": time.time_ns(),
            },
        }))

    async def game_loop(self):
        self.timer_active = True
        try:
            for i in range(3, 0, -1):
                await self.handle_message({"username": "SERVER", "content": str(i)})
                await asyncio.sleep(1)

            self.game_active = True
            self.start_time = time.time_ns()

            await self.handle_message({"username": "SERVER", "content": "GO!"})
            await self.broadcast(json.dumps({"type" : "game_start", "data" : { "result": "true", "timestamp": self.start_time, "restart": "false"} }))
            await self.reset_next_match_ready()

            print("Game Prep Time Started")

            await asyncio.sleep(57.1)

            if self.timer_active:
                self.game_active = False
                await self.broadcast(json.dumps({
                        "type" : "result",
                        "data" : {
                            "winner": "countdown",
                            "timestamp": time.time_ns()
                        }
                    }
                ))

                for i in range(3, 0, -1):
                    await self.handle_message({"username": "SERVER", "content": str(i)})
                    await asyncio.sleep(1)

                self.game_active = True
                self.start_time = time.time_ns()

                await self.handle_message({"username": "SERVER", "content": "GO!"})

                await self.broadcast(json.dumps({"type" : "game_start", "data" : { "result": "true", "timestamp": self.start_time, "restart": "true"} }))
                await self.reset_next_match_ready()
        except asyncio.CancelledError:
            raise
        finally:
            self.timer_active = False
            if self.game_task is asyncio.current_task():
                self.game_task = None

    async def check_game_start(self):
        if self.game_active or self.timer_active or (self.game_task and not self.game_task.done()):
            return

        self.game_task = asyncio.create_task(self.game_loop())

    # broadcast a game start only seen by automarker
    # that way automarker does its "tp to garge" without revealing user boards
    # or doing any other client thingss
    async def test_autostart(self):
        await self.broadcast_to_automarker(json.dumps({
            "type": "game_start",
            "data": {
                "result": "true",
                "timestamp": time.time_ns(),
                "restart": "true"
            }
        }))

    async def automark_handler(self, data):
        #expected data structure player : string, unlock : string time:string
        data = data["data"]
        playername = data['playerName']
        unlock = soulFromID(data)
        time = data["time"]
        
        print(playername, unlock, time)
        player_team = None
        for player in self.teams:
            if player["name"] == playername:
                player_team = player["team"]
                break
        
        index = -1

        for i, entry in enumerate(self.board):
            if entry["name"] == unlock:
                index = i
        if index != -1 and player_team != None:
            message = {'data' : {'user' : playername, 'index' : index, 'color' : player_team, 'timern' : time}}
            await self.handle_board_update(self, message, True)
        return
    
    async def daft_board(self):
        board = daftgen()
        await self.handle_new_board(board)

    async def bgen_board(self, data):
        options = data if isinstance(data, dict) else {}
        try:
            result = self.bgen.generate(
                stacked_district=options.get("stackedDistrict"),
                freshness=options.get("freshness", 100),
                stale_duration=options.get("staleDuration", 10),
                graffiti_distribution=options.get("graffitiDistribution"),
                simple_bingos=options.get("simpleBingos", True),
                seed=options.get("seed"),
            )
            await self.handle_new_board(result["board"])
        except (TypeError, ValueError, RuntimeError) as error:
            print(f"Error generating bGen board: {error}")

    async def kick(self, data):
        kicklog = kicklog = f"{data['kicker']} kicked {data['user']} PUMA"
        for client in self.clients.items():
            websocket, userdata = client
            if json.loads(userdata)['username'] == data['user']:
                kickmsg = {'type' : "kick", 'data' : {"user" : data['kicker']}}
                await websocket.send(json.dumps(kickmsg))
                await self.handle_message({"username": "SERVER", "content": kicklog})
                return

    async def infohandler(self, websocket, data):
        senddata = ""
        match data.get("type"):
            case "Snipes":
                snips = await self.detect_snipes()
                senddata = json.dumps({"type" : "Snipes", "data" : snips}) #json.dumps(self.detect_snipes())
            case "Queue":
                senddata = json.dumps({"type" : "Queue", "data" : self.queue})
            case "Teams":
                senddata = json.dumps({"type" : "Teams", "data" : self.teams})
            case "Automark Names":
                senddata = json.dumps({"type" : "Automark Names", "data" : self.automark_names})
            case "Start Time":
                senddata = json.dumps({"type" : "Start Time", "data" : self.start_time})
            case "Game Active":
                senddata = json.dumps({"type" : "Game Active", "data" : self.game_active})
            case _:
                senddata = json.dumps({"type" : "unknown", "data" : "Unknown Message Type"})
        await websocket.send(json.dumps({"type" : "info", "data" : senddata}))
        return

    async def location_update(self, data):
        uname = data['name']
        ulocation = data['location']
        await self.broadcast(json.dumps({"type" : "location_update", 
        "data" : {
        "name" : uname, 
        "location" : ulocation}}))

    async def main_handler(self, websocket, path=None):
        
        username = None
        try:
            async for message in websocket:
                if username is None:
                    #first message should be the username
                    username = message
                    await self.register(websocket, username)
                else:
                    data = json.loads(message)
                    datatype = data.get("type") or "message"
                    match datatype:
                        case "message":
                            await self.handle_message(data["data"])
                        case "board_update":
                            await self.handle_board_update(websocket, data, False)
                        case "new_board":
                            await self.handle_new_board(data['data'])
                            self.game_active = False
                        case "team_update":
                            await self.team_handler(websocket, data['data'])
                        case "next_match_ready":
                            await self.set_next_match_ready(websocket, data['data'])
                        case "startreq":
                            await self.check_game_start()
                        case "test_autostart":
                            await self.test_autostart()
                        case "automark":
                            await self.automark_handler(data)
                        case "set_automark":
                            self.automark_names = data['data']['names']
                            await self.set_automark(self.automark_names)
                        case "daft_board":
                            await self.daft_board()
                        case "bgen_board":
                            await self.bgen_board(data.get("data", {}))
                        case "kick":
                            await self.kick(data['data'])
                        case "info":
                            await self.infohandler(websocket, data['data'])
                        case "location_update":
                            await self.location_update(data['data'])
                        case _:
                            print(f"Unknown message type: {datatype}")
        except websockets.exceptions.ConnectionClosed:
            print(f"Connection closed: {username}")
        except Exception as e:
            print(f"Error in connection: {e}")
        finally:
            await self.unregister(websocket)

    async def start(self):
        
        async with websockets.serve(self.main_handler, self.host, self.port):
            print(f"Server started on ws://{self.host}:{self.port}")
            await asyncio.Future()  
def signal_handler(signal, frame):
    print("Stopping the server...")
    asyncio.get_event_loop().stop()
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    env_variables = dotenv.dotenv_values(".env")
    if set(env_variables.keys()).issubset(["py_port", "py_host", "py_pocketbase_api_key"]):
        server = IRCChatServer(env_variables['py_host'], env_variables['py_port'])
        asyncio.run(server.start())
    else:
        print("No Valid ENV found. We need py_port, py_host, py_pocketbase_url and py_pocketbase_api_key")
        print("Only keys found are: ", ','.join(env_variables.keys()))
        exit()
