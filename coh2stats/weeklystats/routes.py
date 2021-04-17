from flask import render_template, Blueprint
from coh2stats.weeklystats.utils import get_players_stats
from coh2stats.weeklystats.utils import get_teams_stats
from coh2stats import dao
import os

stats = Blueprint("stats", __name__)


@stats.route("/weeklystats/1v1/latest")
def weeklystats_1v1():
    current_results, previous_results = dao.get_weeklystats_1v1()
    stats = get_players_stats(current_results, previous_results)

    return render_template("results_1v1.html", stats=stats)


@stats.route("/weeklystats/teams/latest")
def weeklystats_teams():
    current_results, previous_results = dao.get_weeklystats_teams()
    stats = get_teams_stats(current_results, previous_results)

    return render_template("results_teams.html", stats=stats)
