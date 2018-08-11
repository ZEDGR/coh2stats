from coh2stats.dao import DAO
from huey import crontab
from coh2stats.config import schedule
from coh2stats.config import Config
import asyncio
import aiohttp
import json
import urllib.request
import urllib.parse
import datetime

config = Config()
dao = DAO()

# Countries selection
COUNTRIES = ("gr", "cy")

# number of top players/teams
TOP_PLAYERS = 5
TOP_TEAMS = 3


def request_leaderboards(params):
    params = urllib.parse.urlencode(params)
    url = "{}?{}".format(config.LEADERBOARDS, params)
    request = urllib.request.Request(url, headers=config.HTTP_HEADERS)

    response = urllib.request.urlopen(request)
    return json.loads(response.read().decode('utf-8'))


def get_leaderboards():
    matchtypes = {}

    params = {'title': "coh2"}

    response = request_leaderboards(params)

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
        async with aio_session.get(config.SPECIFIC_LEADERBOARD, params=params, headers=config.HTTP_HEADERS) as response:
            response = await response.json()

            # if the leaderboardStats array is empty
            # we have exhausted this category
            if not response['leaderboardStats'] or current_position > positions:
                return (matchtype, category_results)

            params['start'] += step

            for group in response['statGroups']:
                found = all(member['country'] in COUNTRIES for member in group['members'])
                if found:
                    print("found for matchtype:", matchtype)

                    stats = next(stats for stats in response['leaderboardStats']
                                 if stats['statGroup_id'] == group['id'])
                    results = dict(stats)
                    results['total'] = results['wins'] + results['losses']
                    results['ratio'] = f"{results['wins'] / results['total']:.0%}"
                    if matchtype.startswith('1v1'):
                        results['player'] = {
                            'profile_id': group['members'][0]['profile_id'],
                            'steam_id': group['members'][0]['name'],
                            'name': group['members'][0]['alias'],
                            'country': group['members'][0]['country']
                        }
                    else:
                        results['players'] = [
                            {
                                'profile_id': member['profile_id'],
                                'steam_id': member['name'],
                                'name': member['alias'],
                                'country': member['country']
                            }
                            for member in group['members']
                        ]
                    category_results.append(results)
                    current_position += 1
                    if current_position > positions:
                        break


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


async def gather():
    matchtypes = get_leaderboards()

    async with aiohttp.ClientSession() as aio_session:
        results = [
            get_results(matchtype, matchtype_id, aio_session, TOP_PLAYERS) if matchtype.startswith('1v1')
            else get_results(matchtype, matchtype_id, aio_session, TOP_TEAMS)
            for matchtype, matchtype_id in matchtypes.items()
        ]

        completed_tasks = await asyncio.gather(*results)

        results = normalize([task for task in completed_tasks])

    results = {'created': datetime.datetime.utcnow(), 'stats': results}
    dao.insert_weeklystats(results)
    dao.close()


@schedule.periodic_task(crontab(hour='14', minute='30', day_of_week='6'))
def get_weeklystats_main():
    eloop = asyncio.get_event_loop()
    eloop.run_until_complete(gather())
