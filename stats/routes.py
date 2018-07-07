from flask import render_template, Blueprint
from stats.utils import get_players_stats
from stats.utils import get_teams_stats
import pymongo
import os


db_client = pymongo.MongoClient(
    host=os.environ.get('MONGO_HOST'),
    port=int(os.environ.get('MONGO_PORT'))
)

stats = Blueprint('stats', __name__)


@stats.route('/weeklystats/1v1/static')
def weeklystats_1v1():
    collection = db_client.coh2stats.weeklystats

    current_results, previous_results = list(collection.find({}, {'created_at': 1, 'stats.1v1': 1, '_id': 0}).sort('created_at', -1).limit(2))
    stats = get_players_stats(current_results, previous_results)

    return render_template('results_1v1.html', stats=stats)


@stats.route('/weeklystats/teams/static')
def weeklystats_teams():
    collection = db_client.coh2stats.weeklystats

    projection = {
        'created_at': 1,
        'stats.team-of-2': 1,
        'stats.team-of-3': 1,
        'stats.team-of-4': 1,
        '_id': 0
    }
    current_results, previous_results = list(collection.find({}, projection).sort('created_at', -1).limit(2))
    stats = get_teams_stats(current_results, previous_results)

    return render_template('results_teams.html', stats=stats)
