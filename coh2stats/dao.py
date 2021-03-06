import pymongo
import os
from coh2stats.config import Config

config = Config()


class DAO:
    def __init__(self):
        mongo_host = config.MONGO_HOST
        mongo_port = config.MONGO_PORT

        if mongo_port:
            mongo_port = int(mongo_port)

        self.mc = pymongo.MongoClient(host=mongo_host, port=mongo_port)
        self.db = self.mc.coh2stats

    def insert_playerstats(self, data):
        try:
            return self.db.playerstats.insert_many(data, ordered=False)
        except pymongo.errors.BulkWriteError:
            # this is INSERT INGORE INTO for MongoDB using this exception and ordered=False
            pass

    def insert_weeklystats(self, data):
        return self.db.weeklystats.insert_one(data)

    def get_latest_weeklystats(self):
        collection = self.db.weeklystats
        return list(collection.find().sort('createdAt', -1).limit(1))

    def get_weeklystats_1v1(self):
        collection = self.db.weeklystats
        return list(collection.find({}, {'createdAt': 1, 'stats.1v1': 1, '_id': 0}).sort('createdAt', -1).limit(2))

    def get_weeklystats_teams(self):
        collection = self.db.weeklystats

        projection = {
            'createdAt': 1,
            'stats.team-of-2': 1,
            'stats.team-of-3': 1,
            'stats.team-of-4': 1,
            '_id': 0
        }
        return list(collection.find({}, projection).sort('createdAt', -1).limit(2))

    def get_players_to_track(self):
        return list(self.db.trackplayers.find())

    def set_publish(self, document_id, published):
        self.db.weeklystats.find_one_and_update(
            {'_id': document_id},
            {'$set': {'published': published}}
        )

    def close(self):
        return self.mc.close()
