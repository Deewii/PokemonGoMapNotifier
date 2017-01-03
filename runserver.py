from flask import Flask, request
from gevent import wsgi

from notifier import Notifier

import logging
import logging.handlers
import os
import json
import configargparse


def log_setup(log_console=True, log_file=True):
    formatter = logging.Formatter('%(asctime)s %(levelname)s [%(threadName)s] %(name)s - %(message)s')
    log = logging.getLogger()

    if log_file:
        if not os.path.exists("log"):
            os.mkdir("log")
        # rotate with 20mb size log files
        file_handler = logging.handlers.RotatingFileHandler('log/server.log', maxBytes=1024 * 1024 * 20, backupCount=10,
                                                            encoding="utf-8")
        file_handler.setFormatter(formatter)
        log.addHandler(file_handler)
    if log_console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        log.addHandler(console_handler)

    return log


app = Flask(__name__)


@app.route('/', methods=['POST'])
def webhook_receiver():
    data = json.loads(request.data)
    notifier.enqueue(data)
    return ""


if __name__ == '__main__':
    # Setup logging
    log = log_setup()
    log.setLevel(logging.INFO)

    # Removes logging of each received request to flask server
    logging.getLogger('pywsgi').setLevel(logging.WARNING)

    # Remove logging of each sent request to discord
    logging.getLogger('requests').setLevel(logging.WARNING)

    parser = configargparse.ArgParser()
    parser.add_argument('--host', help='Host', default='localhost')
    parser.add_argument('-p', '--port', help='Port', type=int, default=8000)
    parser.add_argument('--debug', help="Debug mode", action='store_true', default=False)
    parser.add_argument('-c', '--config', help="config.json file to use", default="config/config.json")
    args = parser.parse_args()

    if args.debug:
        logging.getLogger('notifier').setLevel(logging.DEBUG)

    notifier = Notifier()
    notifier.start()

    log.info("Webhook server started on http://{}:{}".format(args.host, args.port))
    server = wsgi.WSGIServer((args.host, args.port), app, log=logging.getLogger('pywsgi'))
    server.serve_forever()
