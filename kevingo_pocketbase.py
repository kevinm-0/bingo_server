import pocketbase
import dotenv

from datetime import datetime, timezone

env_variables = dotenv.dotenv_values(".env")

pb = pocketbase.PocketBase(env_variables["py_pocketbase_url"])
pb.auth_store.save(env_variables['py_pocketbase_api_key'], None)

def _pb_filter_escape(value):
    #fuck those pocketbase filter strings
    return str(value).replace("\\", "\\\\").replace('"', '\\"')


def _get_user(username):
    username = _pb_filter_escape(username)

    try:
        return pb.collection("users").get_first_list_item(
            f'username = "{username}"'
        )
    except Exception as e:
        if getattr(e, "status", None) == 404:
            return None
        raise


def _create_user(username):
    return pb.collection("users").create({
        "username": username,
        "wins": 0,
        "time_played": 0,
    })

def committodb(init_board_db, queue, winnerUsers,
               duration, start_time, teams):
    try:
        user_records = {}

        for winner in set(winnerUsers):
            print("setting winner for", winner)
            user = _get_user(winner)

            if user is not None:
                pb.collection("users").update(
                    user.id,
                    {"wins": (getattr(user, "wins", 0) or 0) + 1}
                )

        for player in teams:
            username = player["name"]

            if player["team"] == "#D3D3D3":
                continue

            user = _get_user(username)

            if user is None:
                user = _create_user(username)

            user_records[username] = user

            current_time_played = (
                getattr(user, "time_played", 0) or 0
            )

            pb.collection("users").update(
                user.id,
                {
                    "time_played":
                        current_time_played + duration
                }
            )

        pocketbase_datetime = datetime.fromtimestamp(
            start_time / 1_000_000_000,
            tz=timezone.utc
        ).isoformat(timespec="milliseconds").replace("+00:00", "Z")


        game = pb.collection("games").create({
            "duration": int(duration),
            "start_time": pocketbase_datetime,
            "init_board": init_board_db,
            "board_changes": queue,
        })

        game_id = game.id

        for player in teams:
            if player["team"] == "#D3D3D3":
                continue

            user = user_records[player["name"]]

            pb.collection("user_games").create({
                "user_id": user.id,
                "game_id": game_id,
            })

        print(f"Game committed successfully: {game_id}")
        return game_id

    except Exception as e:
        print(f"Error updating PocketBase: {e}")
        raise