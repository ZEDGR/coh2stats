import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from coh2stats import config
from datetime import datetime
from time import sleep
import json
import os
import facebook
import imgkit

imgkit_options = {
    'quiet': '',
    'crop-w': '950',
    'crop-x': '225',
    'format': 'jpg',
    'encoding': 'UTF-8',
}

if not config.FLASK_DEBUG:
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
    img_1v1 = imgkit.from_url(config.STATS_1v1_URL, False, options=imgkit_options)
    sleep(3)
    img_teams = imgkit.from_url(config.STATS_TEAMS_URL, False, options=imgkit_options)

    fb_cfg = {
        'page_id': config.FB_GROUP_ID,
        'access_token': config.FB_TOKEN
    }

    fb_api = get_fb_api(fb_cfg)
    id_1v1 = fb_api.put_photo(image=img_1v1, published=False).get('id')
    id_teams = fb_api.put_photo(image=img_teams, published=False).get('id')
    attached_media = json.dumps([{'media_fbid': str(id_1v1)}, {'media_fbid': str(id_teams)}])
    message = f'Στατιστικά Ελληνικής Κοινότητας {datetime.now():%d/%m/%Y}'
    fb_api.put_object(parent_object="me", connection_name="feed", attached_media=attached_media, message=message)


if __name__ == '__main__':
    main()
