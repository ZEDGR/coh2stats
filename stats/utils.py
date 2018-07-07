import datetime

def set_last_game(date_taken, last_match_date):
    last_match_date = datetime.datetime.fromtimestamp(last_match_date)
    delta = date_taken - last_match_date

    if delta.days > 1:
        return "{} days ago".format(delta.days)
    elif delta.days == 1:
        return "a day ago"
    elif delta.seconds >= 0 and delta.seconds < 60:
        return "less than a minute ago"
    elif delta.seconds < 3600:
        return "{} minutes ago".format(delta.seconds // 60)
    elif delta.seconds >= 3600 and delta.seconds < 7200:
        return "an hour ago"
    else:
        return "{} hours ago".format(delta.seconds // 3600)
