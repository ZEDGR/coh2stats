import dryscrape
import facebook
import json
import os
from time import sleep
from PIL import Image
from concurrent.futures import ThreadPoolExecutor

# Selectors for country. ex. .gr for Greece, .cy for Cyprus
# you can select one country or many but remember this will
# get the best players between the selected countries.
COUNTRY = ".gr,.cy"


BASE_URL = "http://www.companyofheroes.com"

SIDES = ("allies", "axis")

FACTIONS = ("soviet", "german", "aef", "wgerman", "british")

MODES = ("1v1", "team-of-2", "team-of-3", "team-of-4")

COOKIE = "agegate[passed]=yes; expires=Sat, 17-Nov-2018 18:00:00 GMT; domain=www.companyofheroes.com; path=/leaderboards"

# For CLI-only Linux OS install xvfb and uncomment the following line.
# dryscrape.start_xvfb()


def css_country_selectors():
    css = COUNTRY.split(sep=",")

    not_template = ":not({})"
    css_not = not_template * len(css)
    css_not = css_not.format(*css)
    css_not = "a" + css_not

    css = ["a" + c for c in css]
    css = ",".join(css)
    return css, css_not


def search_leaderboards(prefs):

    session = dryscrape.Session(base_url=BASE_URL)
    session.set_attribute('auto_load_images', True)
    session.set_cookie(COOKIE)

    headers = [
        'rank',
        'level',
        'players',
        'streak',
        'wins',
        'losses',
        'ratio',
        'total',
        'last_game']

    page = 1
    url = "leaderboards#global/{0}/{1}/by-rank?page=".format(*prefs)
    results = []
    selectors = css_country_selectors()

    while True:
        session.visit(url + str(page))
        sleep(3)
        current_page = int(session.css('a.current')[0].text())

        # if the current_page is the same with the previous then
        # we have exhausted this ranking category and no one is found by this criteria.
        if page > current_page:
            return results

        print("{0}, {1}, page{2}".format(prefs[0], prefs[1], page))
        matched = session.css(selectors[0])
        for players in matched:
            if players.parent().css(selectors[1]):
                continue
            data = players.parent().parent().children()
            for d in data:
                results.append(d.text().strip())
            if "\n" in results[2]:
                results[2] = results[2].split(sep="\n")
            results = cast_to_int(results)
            return dict(zip(headers, results))
        page += 1


def get_fb_api(cfg):
        graph = facebook.GraphAPI(cfg['access_token'])
        resp = graph.get_object('me/accounts')
        page_access_token = None
        for page in resp['data']:
                if page['id'] == cfg['page_id']:
                        page_access_token = page['access_token']
        graph = facebook.GraphAPI(page_access_token)
        return graph


def cast_to_int(lst):
    converted = []
    for i in lst:
        try:
            converted.append(int(i))
        except (ValueError, TypeError):
            converted.append(i)
    return converted


def export(results, matches):

    num_factions = len(FACTIONS)
    onevone = results[:num_factions]
    twovtwo = results[num_factions:num_factions + 2]
    threevthree = results[num_factions + 2:num_factions + 4]
    fourvfour = results[num_factions + 4:num_factions + 6]

    json_data = {
        MODES[0]: dict(zip(FACTIONS, onevone)),
        MODES[1]: dict(zip(SIDES, twovtwo)),
        MODES[2]: dict(zip(SIDES, threevthree)),
        MODES[3]: dict(zip(SIDES, fourvfour))
    }
    with open("data.json", 'w') as json_file:
        json.dump(json_data, json_file, indent=4)


def main():

    matches = []
    matches.extend((MODES[0], faction) for faction in FACTIONS)
    for i in range(1, len(MODES)):
        matches.extend((MODES[i], side) for side in SIDES)

    with ThreadPoolExecutor(max_workers=4) as executor:
        results = executor.map(search_leaderboards, matches)
        export(list(results), matches)

    path = os.path.dirname(os.path.abspath(__file__))
    session = dryscrape.Session()
    session.set_attribute('auto_load_images', True)
    session.visit("file://{0}/{1}".format(path, "result.html"))
    sleep(3)
    session.render("results.png")

    stats_image = Image.open('results.png')
    stats_image = stats_image.crop((0, 0, 960, 1530)).save("results.png")

    config = json.load(open("config.json"))
    fb_cfg = {
        'page_id': config['FB_GROUP_ID'],
        'access_token': config['FB_TOKEN']
    }

    fb_api = get_fb_api(fb_cfg)
    msg = open("message.txt", 'r').read()
    fb_api.put_photo(image=open("results.png", 'rb'), message=msg)


if __name__ == '__main__':
    main()
