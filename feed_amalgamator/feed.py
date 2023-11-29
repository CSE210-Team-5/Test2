import configparser

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from mastodon import Mastodon

from feed_amalgamator.db import get_db

bp = Blueprint("feed", __name__, url_prefix="/feed")


@bp.route("/home", methods=["GET"])
def feed_home():
    if request.method == "GET":
        user_id = session["user_id"]
        db = get_db()
        error = None
        user_servers = db.execute(
            "SELECT * FROM user_server WHERE user_id = ?", (user_id,)
        ).fetchall()

        if user_servers is None:
            error = "Invalid User"
        timelines = []
        if error is None:
            parser = configparser.ConfigParser()
            parser.read("instance/client.ini")
            client_dict = parser["APP_TOKENS"]
            CLIENT_ID = client_dict["CLIENT_ID"]
            CLIENT_SECRET = client_dict["CLIENT_SECRET"]
            ACCESS_TOKEN = client_dict["ACCESS_TOKEN"]
            for user_server in user_servers:
                domain = user_server["server"]
                token = user_server["token"]
                bot_m = Mastodon(
                    client_id=CLIENT_ID,
                    client_secret=CLIENT_SECRET,
                    access_token=ACCESS_TOKEN,
                    api_base_url=domain,
                )
                print(domain, token)
                users_access_token = bot_m.log_in(
                    code=token,
                    redirect_uri="urn:ietf:wg:oauth:2.0:oob",
                    scopes=["read", "write", "push"],
                )
                user_client = Mastodon(
                    access_token=users_access_token, api_base_url=domain
                )
                timeline = user_client.timeline(timeline="home", limit=20)
                timelines.append(timeline)
            return render_template("feed/home.html", timelines=timelines)

        flash(error)

    return render_template("feed/home.html", timelines=None)


@bp.route("/add_server", methods=["GET", "POST"])
def add_server():
    if request.method == "POST":
        if "domain" in request.form:
            domain = request.form["domain"]
            session["domain"] = domain
            parser = configparser.ConfigParser()
            parser.read("instance/client.ini")
            client_dict = parser["APP_TOKENS"]
            CLIENT_ID = client_dict["CLIENT_ID"]
            CLIENT_SECRET = client_dict["CLIENT_SECRET"]
            ACCESS_TOKEN = client_dict["ACCESS_TOKEN"]
            USERS_DOMAIN = "https://mastodon.social"
            bot_m = Mastodon(
                client_id=CLIENT_ID,
                client_secret=CLIENT_SECRET,
                access_token=ACCESS_TOKEN,
                api_base_url=USERS_DOMAIN,
            )
            url = bot_m.auth_request_url(
                redirect_uris="urn:ietf:wg:oauth:2.0:oob",
                scopes=["read", "write", "push"],
            )
            return render_template("feed/add_server.html", url=url, is_domain_set=True)

        elif "token" in request.form:
            auth_token = request.form["token"]
            user_id = session["user_id"]
            domain = session["domain"]
            db = get_db()
            error = None
            if not auth_token:
                error = "Authorization Token in Required"
            elif not user_id:
                error = "Password is required."
            elif not domain:
                error = "domain is required"

            if error is None:
                try:
                    db.execute(
                        "INSERT INTO user_server (user_id, server, token) VALUES (?, ?, ?)",
                        (user_id, domain, auth_token),
                    )
                    db.commit()
                except db.IntegrityError:
                    error = "Record already exists."
                else:
                    return redirect(url_for("feed.add_server", is_domain_set=False))

            flash(error)

    return render_template("feed/add_server.html", is_domain_set=False)
