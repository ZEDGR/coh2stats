from datetime import datetime
from time import sleep
import facebook
import requests
import json
import imgkit
import os

STATS_1v1_URL = os.environ.get('STATS_1v1_URL')
STATS_TEAMS_URL = os.environ.get('STATS_TEAMS_URL')
FB_GROUP_ID = os.environ.get('FB_TEST_GROUP_ID') if os.environ.get('FLASK_DEBUG') else os.environ.get('FB_GROUP_ID')
FB_TOKEN = os.environ.get('FB_TOKEN')

imgkit_options = {
    'quiet': '',
    'crop-w': '950',
    'crop-x': '225',
    'format': 'jpg',
    'encoding': 'UTF-8',
}

if not os.environ.get('FLASK_DEBUG'):
    imgkit_options['xvfb'] = ''

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
    img_1v1 = imgkit.from_url(STATS_1v1_URL, False, options=imgkit_options)
    sleep(3)
    img_teams = imgkit.from_url(STATS_TEAMS_URL, False, options=imgkit_options)

    fb_cfg = {
        'page_id': FB_GROUP_ID,
        'access_token': FB_TOKEN
    }

    fb_api = get_fb_api(fb_cfg)
    id_1v1 = fb_api.put_photo(image=img_1v1, published=False).get('id')
    id_teams = fb_api.put_photo(image=img_teams, published=False).get('id')
    attached_media = json.dumps([{'media_fbid': str(id_1v1)}, {'media_fbid': str(id_teams)}])
    message = f'Στατιστικά Ελληνικής Κοινότητας {datetime.now():%d/%m/%Y}'
    fb_api.put_object(parent_object="me", connection_name="feed", attached_media=attached_media, message=message)

if __name__ == '__main__':
    main()
