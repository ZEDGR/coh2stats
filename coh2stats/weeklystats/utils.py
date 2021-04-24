import datetime


def get_players_stats(current_results, previous_results):
    # add last_game to the current results
    current_1v1_results = {}
    for faction, players in current_results["stats"]["1v1"].items():
        current_1v1_results[faction] = players
        for player in current_1v1_results[faction]:
            player["last_game"] = _get_time_since_last_game(
                current_results["createdAt"], player["lastmatchdate"]
            )

    # take previous week's players profile ids
    previous_players_ids = {}
    for faction, players in previous_results["stats"]["1v1"].items():
        previous_players_ids[faction] = [player["player"]["profile_id"] for player in players]

    # find each player's dynamic
    for faction, current_players in current_1v1_results.items():
        for player_current_index, player in enumerate(current_players):
            if player["player"]["profile_id"] not in previous_players_ids[faction]:
                player["player"]["dynamic"] = "N"
            else:
                player_previous_index = previous_players_ids[faction].index(
                    player["player"]["profile_id"]
                )
                if player_previous_index > player_current_index:
                    player["player"]["dynamic"] = "U"
                    player["player"]["pos_shift"] = player_previous_index - player_current_index
                elif player_previous_index < player_current_index:
                    player["player"]["dynamic"] = "D"
                    player["player"]["pos_shift"] = player_current_index - player_previous_index
                else:
                    player["player"]["dynamic"] = "S"

    return current_1v1_results


def get_teams_stats(current_results, previous_results):
    # add last_game to the current results
    current_team_results = {}
    for gametype, data in current_results["stats"].items():
        for team in data["Allies"]:
            team["last_game"] = _get_time_since_last_game(
                current_results["createdAt"], team["lastmatchdate"]
            )

        for team in data["Axis"]:
            team["last_game"] = _get_time_since_last_game(
                current_results["createdAt"], team["lastmatchdate"]
            )

        current_team_results[gametype] = {
            "allies": data["Allies"],
            "axis": data["Axis"],
        }

    # take previous week's teams players ids
    previous_teams_results = {}
    for gametype, data in previous_results["stats"].items():
        previous_teams_results[gametype] = {
            "allies": [
                tuple(player["profile_id"] for player in team["players"]) for team in data["Allies"]
            ],
            "axis": [
                tuple(player["profile_id"] for player in team["players"]) for team in data["Axis"]
            ],
        }

    # find each team's dynamic
    for gametype, data in current_team_results.items():
        current_allies_teams_players_ids = [
            tuple(player["profile_id"] for player in team["players"]) for team in data["allies"]
        ]
        current_axis_teams_players_ids = [
            tuple(player["profile_id"] for player in team["players"]) for team in data["axis"]
        ]

        for current_team_index, team in enumerate(current_allies_teams_players_ids):
            _set_team_dynamic(
                current_team_index,
                team,
                previous_teams_results[gametype]["allies"],
                current_team_results[gametype]["allies"],
            )

        for current_team_index, team in enumerate(current_axis_teams_players_ids):
            _set_team_dynamic(
                current_team_index,
                team,
                previous_teams_results[gametype]["axis"],
                current_team_results[gametype]["axis"],
            )

    return current_team_results


def _set_team_dynamic(current_team_index, team, previous_teams_results, current_team_results):
    if team not in previous_teams_results:
        current_team_results[current_team_index]["dynamic"] = "N"
    else:
        previous_team_index = previous_teams_results.index(team)
        if previous_team_index > current_team_index:
            current_team_results[current_team_index]["dynamic"] = "U"
            current_team_results[current_team_index]["pos_shift"] = (
                previous_team_index - current_team_index
            )
        elif previous_team_index < current_team_index:
            current_team_results[current_team_index]["dynamic"] = "D"
            current_team_results[current_team_index]["pos_shift"] = (
                current_team_index - previous_team_index
            )
        else:
            current_team_results[current_team_index]["dynamic"] = "S"


def _get_time_since_last_game(date_taken, last_match_date):
    last_match_date = datetime.datetime.utcfromtimestamp(last_match_date)
    delta = date_taken - last_match_date

    if delta.days > 1:
        return "{} days ago".format(delta.days)
    elif delta.days == 1:
        return "a day ago"
    elif delta.seconds >= 0 and delta.seconds < 60:
        return "less than a minute ago"
    elif delta.seconds < 3600:
        return "{} minutes ago".format(delta.seconds // 60)
    elif delta.seconds >= 3600 and delta.seconds < 7200:
        return "an hour ago"
    else:
        return "{} hours ago".format(delta.seconds // 3600)
