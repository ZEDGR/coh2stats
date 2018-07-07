from flask import render_template, Blueprint
from stats.utils import set_last_game
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

    results = collection.find({}, {'created_at': 1, 'stats.1v1': 1, '_id': 0}).sort('created_at', -1).limit(1).next()

    sorted_results = {}

    for faction, players in results['stats']['1v1'].items():
        faction = faction.lower()
        sorted_results[faction] = sorted(players, key=lambda k: k['rank'])
        for player in sorted_results[faction]:
            player['last_game'] = set_last_game(results['created_at'], player['last_match_date'])

    return render_template('results_1v1.html', stats=sorted_results)


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
    results = collection.find({}, projection).sort('created_at', -1).limit(1).next()

    sorted_results = {}

    for gametype, data in results['stats'].items():

        for team in data['Allies']:
            team['last_game'] = set_last_game(results['created_at'], team['last_match_date'])

        for team in data['Axis']:
            team['last_game'] = set_last_game(results['created_at'], team['last_match_date'])

        sorted_results[gametype.lower()] = {
            'allies': sorted(data['Allies'], key=lambda k: k['rank']),
            'axis': sorted(data['Axis'], key=lambda k: k['rank'])
        }

    return render_template('results_teams.html', stats=sorted_results)
