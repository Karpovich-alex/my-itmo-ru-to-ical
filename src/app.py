import logging
from pathlib import Path

import sentry_sdk
from flask import Flask, Response
from sentry_sdk.integrations.flask import FlaskIntegration

from auth import get_access_token
from calendar_processing import get_raw_events, raw_events_to_calendar
from src.utils import get_hash

logging.basicConfig(level=logging.INFO)
logging.getLogger("werkzeug").handlers = []  # to prevent duplicated logging output
app = Flask(__name__)
application = app  # for wsgi compliance

app.config.from_pyfile(Path("../config/config.py"))

user_mapper = {}
for num in range(1, int(app.config["ISU_USER_NUM"]) + 1):
    try:
        username = app.config[f"ISU_USERNAME_{num}"]
    except KeyError:
        app.logger.warning(f"Cant find username for user {num}")
        break
    if app.config.get(f"ISU_USER_HASH_{num}", None):
        _creds_hash = app.config[f"ISU_USER_HASH_{num}"]
    else:
        _creds_hash = get_hash(16)
    user_mapper[_creds_hash] = num
    app.logger.info(f"URL path for u:{username} calendar #{num}: /calendar/{_creds_hash}")

if app.config["SENTRY_DSN"]:
    sentry_sdk.init(
        dsn=app.config["SENTRY_DSN"],
        integrations=[FlaskIntegration()],
        traces_sample_rate=1.0,
    )


def get_user_num(_creds_hash: str) -> int:
    return user_mapper[_creds_hash]


@app.route("/ping")
def ping():
    return "pong"


@app.route("/calendar/<_creds_hash>", methods=["GET"])
def get_calendar(_creds_hash: str):
    try:
        user_num = get_user_num(_creds_hash)
    except KeyError:
        return Response(status=500)
    token = get_access_token(app.config[f"ISU_USERNAME_{user_num}"], app.config[f"ISU_PASSWORD_{user_num}"])
    events = get_raw_events(token)
    calendar = raw_events_to_calendar(events)
    return Response("\n".join(map(str.strip, calendar)), content_type="text/calendar")


if app.config["SENTRY_DSN"]:
    sentry_sdk.capture_message(f"my-itmo-ru-to-ical started for {app.config['ISU_USERNAME']}, hash {_creds_hash}")

if __name__ == '__main__':
    app.run()
