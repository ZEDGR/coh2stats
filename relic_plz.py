# import asyncio
# import aiohttp
import json
import urllib.request
import urllib.parse
import datetime
import os
import facebook
import dryscrape
from time import sleep
from PIL import Image

CONFIG = json.load(open("config.json"))

COUNTRIES = ("gr", "cy")


def request(url, params, headers):

    params = urllib.parse.urlencode(params)
    url = "{}?{}".format(url, params)
    request = urllib.request.Request(url, headers=headers)

    response = urllib.request.urlopen(request)
    return json.load(response)


def get_leaderboards():

    matchtypes = {}

    params = {'title': "coh2"}

    response = request(CONFIG['leaderboards'], params, CONFIG['headers'])
    # response = json.load(open("export.json"))

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


def get_results(matchtype_id, sortBy=1, step=40, count=40):
    # response = json.load(open("first.json"))

    params = {
        'leaderboard_id': matchtype_id,
        'title': "coh2",
        'platform': "PC_STEAM",
        'sortBy': sortBy,
        'start': 1,
        'count': count
    }

    while True:

        response = request(CONFIG['specific_leaderboard'], params, CONFIG['headers'])

        # if the leaderboardStats array is empty
        # we have exhausted this category
        if not response['leaderboardStats']:
            return None

        params['start'] += step

        for stats in response['leaderboardStats']:
            for group in response['statGroups']:
                if stats['statGroup_id'] == group['id']:
                    found = all(member['country'] in COUNTRIES for member in group['members'])
                    if found:
                        print("found for matchtype:", matchtype_id)
                        results = dict(stats)
                        results['total'] = results['wins'] + results['losses']
                        results['ratio'] = "{:.0%}".format(results['wins'] / results['total'])
                        results['players'] = [{'name': member['alias'], 'country': member['country']} for member in group['members']]
                        results['last_game'] = get_last_game_datetime(results['lastMatchDate'])
                        return results


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


def get_fb_api(cfg):
        graph = facebook.GraphAPI(cfg['access_token'])
        resp = graph.get_object('me/accounts')
        page_access_token = None
        for page in resp['data']:
                if page['id'] == cfg['page_id']:
                        page_access_token = page['access_token']
        graph = facebook.GraphAPI(page_access_token)
        return graph


def main():

    matchtypes = get_leaderboards()
    results = [(matchtype, get_results(matchtype_id)) for matchtype, matchtype_id in matchtypes.items()]
    results = normalize(results)
    with open("newdata.json", 'w') as json_file:
        json.dump(results, json_file, indent=4)

    path = os.path.dirname(os.path.abspath(__file__))
    session = dryscrape.Session()
    session.visit("file://{0}/{1}".format(path, "result.html"))
    sleep(3)
    session.render("results.png")

    stats_image = Image.open('results.png')
    stats_image = stats_image.crop((0, 0, 960, 1530)).save("results.png")

    fb_cfg = {
        'page_id': CONFIG['fb_group_id'],
        'access_token': CONFIG['fb_token']
    }

    fb_api = get_fb_api(fb_cfg)
    msg = open("message.txt", 'r').read()
    fb_api.put_photo(image=open("results.png", 'rb'), message=msg)


if __name__ == '__main__':
    main()
