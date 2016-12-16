import dryscrape
import facebook
import json
import os
from time import sleep
from PIL import Image


# Selectors for country. ex. .gr for Greece, .cy for Cyprus
# you can select one country or many but remember this will
# get the best players between the selected countries.
COUNTRY = ".gr,.cy"


BASE_URL = "http://www.companyofheroes.com"

SIDES = ("allies", "axis")

FACTIONS = ("soviet", "german", "aef", "wgerman", "british")

TYPES = ("1v1", "team-of-2", "team-of-3", "team-of-4")

COOKIE = "agegate[passed]=yes; expires=Sat, 17-Nov-2018 18:00:00 GMT; domain=www.companyofheroes.com; path=/leaderboards"

# For CLI-only Linux OS install xvfb and uncomment the following line.
# dryscrape.start_xvfb()

session = dryscrape.Session(base_url=BASE_URL)
session.set_attribute('auto_load_images', False)
session.set_cookie(COOKIE)


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
            return results
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


def arrange(results):

    data = [
        'rank',
        'level',
        'player',
        'streak',
        'wins',
        'losses',
        'ratio',
        'total',
        'last_game']

    arranged = {}
    for index, result in enumerate(results):
        if index == 0:
            results_1v1 = {}
            for i, player_results in enumerate(result):
                if not player_results:
                    results_1v1[FACTIONS[i]] = None
                    continue
                results_1v1[FACTIONS[i]] = dict(zip(data, player_results))
            arranged[TYPES[index]] = results_1v1
        else:
            data[2] = "players"
            result = tuple(result)
            arranged[TYPES[index]] = {
                SIDES[0]: dict(zip(data, result[0])),
                SIDES[1]: dict(zip(data, result[1]))
            }
    return arranged


def main():

    matches = []
    matches.append([(TYPES[0], faction) for faction in FACTIONS])
    for i in range(1, len(TYPES)):
        matches.append([(TYPES[i], side) for side in SIDES])

    results = [map(search_leaderboards, match) for match in matches]
    results = arrange(results)
    with open("data.json", "w") as export_file:
        json.dump(results, export_file)

    path = os.path.dirname(os.path.abspath(__file__))
    session.set_attribute('auto_load_images', True)
    session.visit("file://{0}/{1}".format(path, "result.html"))
    sleep(3)
    session.render("original.png")
    stats_image = Image.open("original.png")
    stats_image = stats_image.crop((0, 0, 960, 1530)).save("final.png", "png")

    fb_cfg = {
        "page_id": os.environ.get("FB_GROUP_ID"),
        "access_token": os.environ.get("FB_TOKEN")
    }

    fb_api = get_fb_api(fb_cfg)
    msg = open('message.txt', 'r').read()
    fb_api.put_photo(image=open('final.png', 'rb'), message=msg)


if __name__ == '__main__':
    main()
