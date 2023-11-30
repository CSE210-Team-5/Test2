"""Code for handling the main, feed page via flask"""
import configparser
import logging
from pathlib import Path

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from mastodon import Mastodon
from sqlalchemy import exc

from feed_amalgamator.helpers.constants import USER_DOMAIN_FIELD, LOGIN_TOKEN_FIELD, USER_ID_FIELD
from feed_amalgamator.helpers.custom_exceptions import InvalidApiInputError, MastodonConnError
from feed_amalgamator.db import get_db
from feed_amalgamator.helpers.logging_helper import LoggingHelper
from feed_amalgamator.helpers.mastodon_data_interface import MastodonDataInterface
from feed_amalgamator.helpers.mastodon_oauth_interface import MastodonOAuthInterface
from feed_amalgamator.helpers.db_interface import dbi, UserServer

"""
Notes from discussion with Professor:
# No abstraction, security, happy path (code only thinks about things that right, not robust code)
# magic values/strings, sql injection, robustness, Swagger file/OpenAPI format for documentation
"""

bp = Blueprint("feed", __name__, url_prefix="/feed")

# Setting up the loggers and interface layers
CONFIG_FILE_LOC = Path("configuration/app_settings.ini")
parser = configparser.ConfigParser()
parser.read(CONFIG_FILE_LOC)
log_file_loc = Path(parser['LOG_SETTINGS']['feed_log_loc'])
logger = LoggingHelper.generate_logger(logging.INFO, log_file_loc, "feed_page")
auth_api = MastodonOAuthInterface(CONFIG_FILE_LOC, logger)
data_api = MastodonDataInterface(logger)

# TODO - Add Swagger/OpenAPI documentation

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
                users_access_token = user_server["token"]

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
    """Endpoint for the user to add a server to their existing list"""
    if request.method == "POST":
        if USER_DOMAIN_FIELD in request.form:
            return render_redirect_url_page()
        elif LOGIN_TOKEN_FIELD in request.form:
            return render_input_auth_code_page()


def render_redirect_url_page():
    """Helper function to handle the logic for redirecting users to the Mastodon OAuth flow
    Should inherit the request and session of add_server"""

    domain = request.form[USER_DOMAIN_FIELD]
    logger.info("Rendering redirect url for user inputted domain {d}".format(d=domain))
    session[USER_DOMAIN_FIELD] = domain  # CWJ: What does this do

    valid_domain, parsed_domain = auth_api.verify_user_provided_domain(domain)
    if not valid_domain:
        logger.error("User inputted domain {d} was not a valid mastodon domain. "
                     "Failed to render redirect url page".format(d=domain))
        raise Exception  # TODO: We will need to standardize how to handle exceptions in the flask context.

    auth_api.start_app_api_client(parsed_domain)
    url = auth_api.generate_redirect_url()
    logger.info("Generated redirect url: {u}".format(u=url))
    return render_template("feed/add_server.html", url=url, is_domain_set=True)


def render_input_auth_code_page():
    """Helper function to handle the logic for allowing users to input the
    Should inherit the request and session of add_server"""
    auth_token = request.form[LOGIN_TOKEN_FIELD]
    user_id = session[USER_ID_FIELD]
    domain = session[USER_DOMAIN_FIELD]

    error = generate_auth_code_error_message(auth_token, user_id, domain)
    if error is None:
        try:
            # The auth_token input by the user is a one-time token used to generate the actual login token
            # Once the auth_token is used, it cannot be reused. We need to save the actual login token
            access_token = auth_api.generate_user_access_token(auth_token)

            user_server_obj = UserServer(user_id=user_id, server=domain, token=access_token)
            dbi.session.add(user_server_obj)
            dbi.session.commit()
        except exc.IntegrityError:
            error = "Record already exists."  # Hardcore error messages, or abstract further?
        except MastodonConnError:
            error = "Error: Could not generate valid login token"
        else:
            # Executes if there is no exception
            return redirect(url_for("feed.add_server", is_domain_set=False))
    flash(error)
    return render_template("feed/add_server.html", is_domain_set=False)


def generate_auth_code_error_message(authentication_token: str | None, user_id: str | None,
                                     user_domain: str | None) -> str | None:
    """
    Helper function to generate different error messages that will be shown to the user depending
    on what went wrong
    @param authentication_token: auth_token field in the request form
    @param user_id: user_id field in the session
    @param user_domain: user_domain field in the session
    @return: Either the error message, or None
    """
    error = None
    # Hardcode error messages, or abstract further? For localization. If shown to user, will have to localize further
    if not authentication_token:
        error = "Authorization Token in Required"
    elif not user_id:
        error = "Password is required."
    elif not user_domain:
        error = "Domain is required"
    return error


"""
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
"""