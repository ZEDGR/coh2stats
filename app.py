from flask import Flask

app = Flask(__name__, static_folder='assets')
from stats.routes import stats
app.register_blueprint(stats)

if __name__ == '__main__':
    app.run()
