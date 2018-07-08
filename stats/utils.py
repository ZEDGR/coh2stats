import datetime

def get_players_stats(current_results, previous_results):
    # sort current results and add last_game
    current_sorted_results = {}
    for faction, players in current_results['stats']['1v1'].items():
        faction = faction.lower()
        current_sorted_results[faction] = sorted(players, key=lambda k: k['rank'])
        for player in current_sorted_results[faction]:
            player['last_game'] = get_time_since_last_game(current_results['created'], player['last_match_date'])

    # take and sort previous players profile ids
    previous_sorted_players_ids = {}
    for faction, players in previous_results['stats']['1v1'].items():
        players_profiles_ids = [player['players'][0]['profile_id'] for player in sorted(players, key=lambda k: k['rank'])]
        previous_sorted_players_ids[faction.lower()] = players_profiles_ids

    # find each player's dynamic
    for faction, current_players in current_sorted_results.items():
        for player_current_index, player in enumerate(current_players):
            if player['players'][0]['profile_id'] not in previous_sorted_players_ids[faction]:
                player['players'][0]['dynamic'] = 'N'
            else:
                player_previous_index = previous_sorted_players_ids[faction].index(player['players'][0]['profile_id'])
                if player_previous_index > player_current_index:
                    player['players'][0]['dynamic'] = 'U'
                elif player_previous_index < player_current_index:
                    player['players'][0]['dynamic'] = 'D'
                else:
                    player['players'][0]['dynamic'] = 'S'

    return current_sorted_results

def get_teams_stats(current_results, previous_results):
    # sort current results and add last_game
    current_sorted_results = {}
    for gametype, data in current_results['stats'].items():
        for team in data['Allies']:
            team['last_game'] = get_time_since_last_game(current_results['created'], team['last_match_date'])

        for team in data['Axis']:
            team['last_game'] = get_time_since_last_game(current_results['created'], team['last_match_date'])

        current_sorted_results[gametype.lower()] = {
            'allies': sorted(data['Allies'], key=lambda k: k['rank']),
            'axis': sorted(data['Axis'], key=lambda k: k['rank'])
        }

    # take and sort previous teams players ids
    previous_sorted_teams_players_ids= {}
    for gametype, data in previous_results['stats'].items():
        previous_sorted_teams_players_ids[gametype.lower()] = {
            'allies': [tuple(player['profile_id'] for player in team['players']) for team in sorted(data['Allies'], key=lambda k: k['rank'])],
            'axis': [tuple(player['profile_id'] for player in team['players']) for team in sorted(data['Axis'], key=lambda k: k['rank'])]
        }

    # find each team's dynamic
    for gametype, data in current_sorted_results.items():
        current_allies_teams_players_ids = [tuple(player['profile_id'] for player in team['players']) for team in data['allies']]
        current_axis_teams_players_ids = [tuple(player['profile_id'] for player in team['players']) for team in data['axis']]

        for current_team_index, team in enumerate(current_allies_teams_players_ids):
            if team not in previous_sorted_teams_players_ids[gametype]['allies']:
                current_sorted_results[gametype]['allies'][current_team_index]['dynamic'] = 'N'
            else:
                previous_team_index = previous_sorted_teams_players_ids[gametype]['allies'].index(team)
                if previous_team_index > current_team_index:
                    current_sorted_results[gametype]['allies'][current_team_index]['dynamic'] = 'U'
                elif previous_team_index < current_team_index:
                    current_sorted_results[gametype]['allies'][current_team_index]['dynamic'] = 'D'
                else:
                    current_sorted_results[gametype]['allies'][current_team_index]['dynamic'] = 'S'

        for current_team_index, team in enumerate(current_axis_teams_players_ids):
            if team not in previous_sorted_teams_players_ids[gametype]['axis']:
                current_sorted_results[gametype]['axis'][current_team_index]['dynamic'] = 'N'
            else:
                previous_team_index = previous_sorted_teams_players_ids[gametype]['axis'].index(team)
                if previous_team_index > current_team_index:
                    current_sorted_results[gametype]['axis'][current_team_index]['dynamic'] = 'U'
                elif previous_team_index < current_team_index:
                    current_sorted_results[gametype]['axis'][current_team_index]['dynamic'] = 'D'
                else:
                    current_sorted_results[gametype]['axis'][current_team_index]['dynamic'] = 'S'

    return current_sorted_results

def get_time_since_last_game(date_taken, last_match_date):
    last_match_date = datetime.datetime.fromtimestamp(last_match_date)
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
