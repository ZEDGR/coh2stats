import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from coh2stats import dao
from coh2stats import config
import asyncio
import aiohttp


async def get_players_profiles(players_profiles_ids, session):
    url = config.PROFILES_STATS.format(players_profiles_ids)

    async with session.get(url) as response:
        response = await response.json()

        players_profiles = {}
        for stat_group in response['statGroups']:
            for player in stat_group['members']:
                if player['profile_id'] in players_profiles_ids:
                    players_profiles[player['profile_id']] = {
                        'steam_id': player['name'],
                        'name': player['alias'],
                        'country': player['country'],
                        'level': player['level']
                    }
                    break
    return players_profiles


async def get_match_stats(steam_ids, session):
    url = config.RECENT_MATCH_HISTORY.format(steam_ids)

    async with session.get(url) as response:
        response = await response.json()
        players_profiles_ids = [
            report_result['profile_id']
            for stats in response['matchHistoryStats']
            for report_result in stats['matchhistoryreportresults']
        ]

        players_profiles = await get_players_profiles(players_profiles_ids, session)

        final_stats = []
        for stats in response['matchHistoryStats']:
            stats['_id'] = stats['id']
            del stats['id']

            for report_result in stats['matchhistoryreportresults']:
                report_result['profile'] = players_profiles.get(report_result['profile_id'])

            final_stats.append(stats)

    return final_stats


async def get_data():
    steam_ids = [player['steam_id'] for player in dao.get_players_to_track()]

    results = []
    async with aiohttp.ClientSession() as session:
        for chunk in chunks(steam_ids, 5):
            stats = await get_match_stats(chunk, session)
            results.extend(stats)

    dao.insert_playerstats(results)


def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]


def main():
    eloop = asyncio.get_event_loop()
    try:
        eloop.run_until_complete(get_data())
    finally:
        eloop.close()


if __name__ == '__main__':
    main()
