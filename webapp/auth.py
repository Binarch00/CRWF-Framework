import re
import hashlib
import time
from flask import flash, session, request, redirect, url_for, render_template, g, abort
from webapp import app
from database.models import User
from core.utils.cached_objects import UserCH
import cache
from settings import logger, GOOGLE_CAPTCHA, SECRET
import requests as req


def web_login(user_name, password):
    userid = User.login(user_name, password)
    if not userid:
        is_abuse_check(request.remote_addr, prefix="login", threshold=10, wait_time=60*60)
        return False
    if userid != -1:
        flash("Login success!")
        session["id"] = userid
    return userid


@app.before_request
def load_user():
    if is_abuse_check(request.remote_addr, prefix="requests", threshold=1000, wait_time=3600):
        abort(403, "IP abuse detected!")
    if is_abuse_check(request.remote_addr, prefix="login", threshold=10, wait_time=3600, increment=False):
        abort(403, "IP abuse detected!")
    user_id = session.get("id")
    if user_id:
        g.user = UserCH(user_id)
    else:
        g.user = None


@app.route("/activate/<vcode>", methods=["GET"], endpoint="auth.activate")
def activate(vcode):
    if User.verify_user(vcode):
        flash("Account activated!")
    return redirect(url_for("home"))


@app.route("/login", methods=["GET", "POST"], endpoint="auth.login")
def login():
    if request.method == "POST":
        user_name = request.form.get("username")
        password = request.form.get("password")
        next_page = request.form.get("next_page", url_for("home"))
        captcha_response = request.form.get("g-recaptcha-response")
        if not validate_captcha(captcha_response):
            return render_template("base.html", error_login="Recaptcha Fail")
        user = web_login(user_name, password)
        if user == -1:
            return render_template("base.html", error_login="Pending Account Activation!")
        if not user:
            return render_template("base.html", error_login="Invalid Credentials")

        return redirect(next_page)
    else:
        return render_template("base.html", error_login=None)


@app.route("/logout", methods=["GET"], endpoint="auth.logout")
def logout():
    del session["id"]
    g.user = None
    flash("Logout success!")
    return redirect(url_for("home"))


def gen_forgot(id, tm=None):
    if not tm:
        tm = int(time.time())
    tm = str(tm)
    data = "{}{}{}{}".format(id, SECRET, "salt-452341", tm)
    data = data.encode()
    return "{}/{}".format(hashlib.md5(data).hexdigest(), tm)


def valid_forgot_code(id, tm, code):
    now = int(time.time())
    tm_int = int(tm)
    # valid for only one hour
    if now - tm_int > 3600:
        flash("Expired password forgot code!")
        logger.warning("Expired password forgot code! id: %s" % id)
        return False
    if gen_forgot(id, tm) != code:
        flash("Invalid password forgot code!")
        return False
    return True


@app.route("/forgot", methods=["GET", "POST"], endpoint="auth.forgot")
def forgot():
    if request.method == "POST":
        user_name = request.form.get("username")
        if not re.match(r"[^@]+@[^@]+\.[^@]+", user_name):
            return render_template("forgot.html", error="Invalid email address!")
        next_page = request.form.get("next_page", url_for("home"))
        captcha_response = request.form.get("g-recaptcha-response")
        if not validate_captcha(captcha_response):
            return render_template("forgot.html", error="Recaptcha Fail")
        if is_abuse_check(request.remote_addr, prefix="forgot", threshold=10):
            return render_template("forgot.html", error="Abuse detected by your IP address.")
        try:
            User.forgot(email=user_name)
        except Exception as ex:
            logger.exception(ex)
            return render_template("forgot.html", error="Password Forgot Fail!")
        return redirect(next_page)
    else:
        return render_template("forgot.html", error=None)


@app.route("/reset-auth/<uid>/<hash>/<htime>", methods=["GET", "POST"], endpoint="auth.reset")
def reset(uid, hash, htime):
    if valid_forgot_code(uid, htime, "{}/{}".format(hash, htime)):
        if request.method == "POST":
            password = request.form.get("password")
            password2 = request.form.get("password2")
            if password != password2:
                return render_template("reset.html", error="Password Confirmation Error!")
            if not validate_password(password):
                return render_template("reset.html", error="Password length should be between 8 and 30 characters.")
            captcha_response = request.form.get("g-recaptcha-response")
            if not validate_captcha(captcha_response):
                return render_template("reset.html", error="Recaptcha Fail")
            if is_abuse_check(request.remote_addr, prefix="reset", threshold=5):
                return render_template("reset.html", error="Abuse detected by your IP address.")
            if User.reset_user_password(uid, password):
                flash("Password Reset Success!")
                return redirect(url_for("home"))
            else:
                return render_template("reset.html", error="Password Reset Fail!")
        else:
            return render_template("reset.html", error=None)
    else:
        return render_template("reset.html", error="Invalid Reset Code")


@app.route("/register", methods=["GET", "POST"], endpoint="auth.register")
def register():
    if request.method == "POST":
        user_name = request.form.get("username")
        if not re.match(r"[^@]+@[^@]+\.[^@]+", user_name):
            return render_template("register.html", error="Invalid email address!")
        password = request.form.get("password")
        password2 = request.form.get("password2")
        if password != password2:
            return render_template("register.html", error="Password Confirmation Error!")
        if not validate_password(password):
            return render_template("register.html", error="Password length should be between 8 and 30 characters.")
        next_page = request.form.get("next_page", url_for("home"))
        captcha_response = request.form.get("g-recaptcha-response")
        if not validate_captcha(captcha_response):
            return render_template("register.html", error="Recaptcha Fail")
        if is_abuse_check(request.remote_addr, prefix="register", threshold=10):
            return render_template("register.html", error="Abuse detected by your IP address.")
        try:
            User.add_user(email=user_name, password=password)
        except Exception as ex:
            logger.exception(ex)
            return render_template("register.html", error="Register Fail!")
        user = web_login(user_name, password)
        if not user:
            return render_template("register.html", error="Register Fail!")
        flash('Check your email to activate account.')
        return redirect(next_page)
    else:
        return render_template("register.html", error=None)


def validate_captcha(response):
    url = "https://www.google.com/recaptcha/api/siteverify"
    data = {
        "secret": GOOGLE_CAPTCHA["secret"],
        "response": response
    }
    resp = req.post(url=url, data=data).json()
    if resp.get("success") == True:
        return True
    return False


def validate_password(password):
    return 8 <= len(password) <= 30


def is_abuse_check(id, prefix="default", threshold=5, wait_time=12*60*60, increment=True):
    key = "abuse_check/{}/{}".format(prefix, id)
    result = 0
    if increment:
        result = cache.redis_con.incr(key)
        cache.redis_con.expire(key, wait_time)
    else:
        try:
            result = int(cache.redis_con.get(key))
        except TypeError:
            result = 0
    if result >= threshold:
        return True
    return False
