from huey import crontab
from coh2stats.dao import DAO
from coh2stats.config import schedule
from coh2stats.config import Config
from coh2stats.mail import send_error_mail
from pyppeteer import launch
from datetime import datetime
import asyncio
import json
import facebook

config = Config()
dao = DAO()
IMG_1V1_PATH = config.STATS_1V1_URL.split('/')[-2] + '.png'
IMG_TEAMS_PATH = config.STATS_TEAMS_URL.split('/')[-2] + '.png'


async def take_screenshot_from_url(url, img_path):
    browser = await launch(args=['--no-sandbox'])
    page = await browser.newPage()
    await page.goto(url, waitUntil='networkidle0')
    await page.screenshot(path=img_path, fullPage=True)
    await browser.close()


async def take_screenshots():
    await take_screenshot_from_url(config.STATS_1v1_URL, IMG_1V1_PATH)
    await take_screenshot_from_url(config.STATS_TEAMS_URL, IMG_TEAMS_PATH)


def get_fb_api(cfg):
    graph = facebook.GraphAPI(cfg['access_token'])
    resp = graph.get_object('me/accounts')
    page_access_token = None
    for page in resp['data']:
        if page['id'] == cfg['page_id']:
            page_access_token = page['access_token']
    graph = facebook.GraphAPI(page_access_token)
    return graph


@schedule.periodic_task(crontab(hour='18', minute='12', day_of_week='6'))
def publish_weeklystats_main():
    stats = dao.get_latest_weeklystats()
    stats_id = stats[0]['_id']
    if not stats or stats[0]['createdAt'].date() != datetime.now().date():
        subject = "CoH2 Stats"
        message = "Failed to get data from the API Server"
        send_error_mail(subject, message)
        return

    eloop = asyncio.get_event_loop()
    eloop.run_until_complete(take_screenshots())

    fb_cfg = {
        'page_id': config.FB_GROUP_ID,
        'access_token': config.FB_TOKEN
    }

    fb_api = get_fb_api(fb_cfg)
    id_1v1 = fb_api.put_photo(image=open(IMG_1V1_PATH, 'rb'), published=False).get('id')
    id_teams = fb_api.put_photo(image=open(IMG_TEAMS_PATH, 'rb'), published=False).get('id')
    attached_media = json.dumps([{'media_fbid': str(id_1v1)}, {'media_fbid': str(id_teams)}])
    message = f'Στατιστικά Ελληνικής Κοινότητας {datetime.now():%d/%m/%Y}'
    fb_api.put_object(parent_object="me", connection_name="feed", attached_media=attached_media, message=message)
    dao.set_publish(stats_id, True)
