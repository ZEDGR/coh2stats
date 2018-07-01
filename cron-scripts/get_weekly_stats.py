import asyncio
import aiohttp
import json
import urllib.request
import urllib.parse
import datetime
import pymongo

CONFIG = json.load(open("config.json"))

# For GUI-less OS uncomment the line below
# dryscrape.start_xvfb()

# Countries selection
COUNTRIES = ("gr", "cy")

# number of top players/teams
TOP_PLAYERS = 5
TOP_TEAMS = 3


def request(url, params, headers):
    params = urllib.parse.urlencode(params)
    url = "{}?{}".format(url, params)
    request = urllib.request.Request(url, headers=headers)

    response = urllib.request.urlopen(request)
    return json.loads(response.read().decode('utf-8'))


def get_leaderboards():
    matchtypes = {}

    params = {'title': "coh2"}

    response = request(CONFIG['leaderboards'], params, CONFIG['headers'])

    id1v1 = None
    # get 1v1 matchtype id
    for mt in response['matchTypes']:
        if mt['name'] == '1V1':
            id1v1 = mt['id']
            break

    # get leaderboard ids
    for leaderboard in response['leaderboards']:
        for m in leaderboard['leaderboardmap']:
            if m['matchtype_id'] == id1v1:
                matchtypes.update(
                    {leaderboard['name']: leaderboard['id']})
            elif m['statgroup_type'] in (2, 3, 4):
                matchtypes.update(
                    {leaderboard['name']: leaderboard['id']})

    return matchtypes


async def get_results(matchtype, matchtype_id, aio_session, positions, sortBy=1, step=40, count=40):

    params = {
        'leaderboard_id': matchtype_id,
        'title': "coh2",
        'platform': "PC_STEAM",
        'sortBy': sortBy,
        'start': 1,
        'count': count
    }
    current_position = 1
    category_results = []

    while True:
        async with aio_session.get(CONFIG['specific_leaderboard'], params=params, headers=CONFIG['headers']) as response:
            response = await response.json()

            # if the leaderboardStats array is empty
            # we have exhausted this category
            if not response['leaderboardStats'] or current_position > positions:
                return (matchtype, category_results)

            params['start'] += step

            # for stats in response['leaderboardStats']:
            for group in response['statGroups']:
                found = all(member['country'] in COUNTRIES for member in group['members'])
                if found:
                    print("found for matchtype:", matchtype)

                    stats = next(stats for stats in response['leaderboardStats'] if stats['statGroup_id'] == group['id'])
                    results = dict(stats)
                    results['total'] = results['wins'] + results['losses']
                    results['ratio'] = "{:.0%}".format(results['wins'] / results['total'])
                    results['players'] = [
                        {'profile_id': member['profile_id'], 'name': member['alias'], 'country': member['country']}
                        for member in group['members']
                    ]
                    results['last_game'] = get_last_game_datetime(results['lastMatchDate'])

                    category_results.append(results)
                    current_position += 1
                    if current_position > positions:
                        break


def get_last_game_datetime(date):
    last_match_date = datetime.datetime.fromtimestamp(date)
    now = datetime.datetime.now()
    delta = now - last_match_date

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


def normalize(data):
    normalized = {
        "1v1": {},
        "team-of-2": {},
        "team-of-3": {},
        "team-of-4": {}
    }

    for matchtype, result in data:
        if matchtype.startswith("1v1"):
            normalized['1v1'].update({matchtype[3:]: result})
        else:
            num = matchtype[6]
            key = "team-of-{}".format(num)
            normalized[key].update({matchtype[7:]: result})
    return normalized


async def main():
    matchtypes = get_leaderboards()

    async with aiohttp.ClientSession() as aio_session:
        results = [
            get_results(matchtype, matchtype_id, aio_session, TOP_PLAYERS) if matchtype.startswith('1v1')
            else get_results(matchtype, matchtype_id, aio_session, TOP_TEAMS)
            for matchtype, matchtype_id in matchtypes.items()
        ]

        completed_tasks = await asyncio.gather(*results)

        results = normalize([task for task in completed_tasks])

    with open("data.json", 'w') as json_file:
        json.dump(results, json_file, indent=4)

    # Connect to a local MongoDB and store the results
    mongo_client = pymongo.MongoClient()
    grstats = mongo_client.coh2stats.newstats
    results = {'test': True, 'created_at': datetime.datetime.utcnow(), 'stats': results}
    grstats.insert(results)


if __name__ == '__main__':
    eloop = asyncio.get_event_loop()
    try:
        eloop.run_until_complete(main())
    finally:
        eloop.close()
