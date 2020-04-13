from flask import Flask, render_template
from settings import SERVER_NAME, GOOGLE_CAPTCHA, SERVICE_NAME

app = Flask(__name__, static_url_path='')
app.secret_key = "iUHDAIYE(*W#ed0o9u013jsioajiohIUS+A9HDiu+7sag2diuw45489"
app.config['SERVER_NAME'] = SERVER_NAME

import webapp.auth
import webapp.ipn
import webapp.json_api


@app.context_processor
def inject_template_globals():
    return dict(sitekey=GOOGLE_CAPTCHA["sitekey"], service_name=SERVICE_NAME, main_url=SERVER_NAME)


@app.route('/', endpoint="home")
def index():
    return render_template("base.html")
