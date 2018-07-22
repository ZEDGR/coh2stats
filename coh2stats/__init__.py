from flask import Flask


def create_app():
    app = Flask(__name__, static_folder='assets')
    from coh2stats.stats.routes import stats
    app.register_blueprint(stats)

    return app
