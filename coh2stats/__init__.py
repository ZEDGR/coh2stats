from flask import Flask
from coh2stats.dao import DAO
from coh2stats.config import Config
from coh2stats.config import schedule
from coh2stats.weeklystats.tasks import *
from coh2stats.personalstats.tasks import *


dao = DAO()


def create_app():
    app = Flask(__name__, static_folder='assets')
    from coh2stats.weeklystats.routes import stats
    app.register_blueprint(stats)

    return app
