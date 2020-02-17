from huey import SqliteHuey
import os
import json

schedule = SqliteHuey('test.db', utc=False)


class Config:
    FLASK_DEBUG = os.environ.get('FLASK_DEBUG')

    # Database Settings
    MONGO_HOST = os.environ.get('MONGO_HOST')
    MONGO_PORT = os.environ.get('MONGO_PORT')

    # Relic APIs
    RELIC_API_BASE_URL = os.environ.get('RELIC_API_BASE_URL')
    LEADERBOARDS = os.environ.get('LEADERBOARDS')
    SPECIFIC_LEADERBOARD = os.environ.get('SPECIFIC_LEADERBOARD')
    PROFILES_STATS = os.environ.get('PROFILES_STATS')
    RECENT_MATCH_HISTORY = os.environ.get('RECENT_MATCH_HISTORY')

    # Endpoints for screenshots
    STATS_1V1_URL = os.environ.get('STATS_1v1_URL')
    STATS_TEAMS_URL = os.environ.get('STATS_TEAMS_URL')

    # Facebook Settings
    FB_GROUP_ID = os.environ.get('FB_TEST_GROUP_ID') if FLASK_DEBUG else os.environ.get('FB_GROUP_ID')
    FB_TOKEN = os.environ.get('FB_TOKEN')

    # Relic Headers
    HTTP_HEADERS = json.load(open('config.json'))

    # Email Settings
    EMAIL_PORT = os.environ.get('EMAIL_PORT')
    SMTP_SERVER = os.environ.get('SMTP_SERVER')
    SENDER_EMAIL = os.environ.get('SENDER_EMAIL')
    SENDER_PASSWORD = os.environ.get('SENDER_PASSWORD')
    RECEIVER_EMAIL = os.environ.get('RECEIVER_EMAIL')
