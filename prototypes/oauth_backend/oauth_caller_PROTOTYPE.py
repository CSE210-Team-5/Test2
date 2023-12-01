from mastodon import Mastodon  # pip install Mastodon.py
import configparser


if __name__ == "__main__":
    parser = configparser.ConfigParser()
    parser.read("client.ini")
    client_dict = parser["APP_TOKENS"]

    # The following are generated from a previous API call, when we create our app/bot.
    # These are thus OUR client id, secret token

    CLIENT_ID = client_dict["CLIENT_ID"]
    CLIENT_SECRET = client_dict["CLIENT_SECRET"]
    ACCESS_TOKEN = client_dict["ACCESS_TOKEN"]

    # Should get user to input this. If your acc is on tomorrow.io, this domain needs to be tomorrow.io etc.
    USERS_DOMAIN = "https://mastodon.social"

    # This is our bot/app's api client
    bot_m = Mastodon(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, access_token=ACCESS_TOKEN,
                     api_base_url=USERS_DOMAIN)

    # This will generate a url that we should show to the user.
    # The user will need to go to this url and perform the auth
    url = bot_m.auth_request_url(redirect_uris="urn:ietf:wg:oauth:2.0:oob", scopes=["read", "write", "push"])
    print("User should be redirected to:" + url)
    """
    # User will be redirected. They can then copy an authorization code and paste it into the application.
    auth_code = "THIS IS THE USER'S AUTH CODE THAT THEY CAN COPY IN"

    users_access_token = bot_m.log_in(code=auth_code,
                                      redirect_uri='urn:ietf:wg:oauth:2.0:oob', scopes=["read", "write",
                                                                                "push"])

    # Using the user's access token, log in on their behalf
    user_client = Mastodon(access_token=users_access_token, api_base_url=USERS_DOMAIN)

    # With that client, you can now do stuff like read the timeline
    timeline = user_client.timeline(timeline="home", limit=20)

    # Base url is different for every different mastodon server
    # form = show_auth_form(CLIENT_ID, CLIENT_SECRET, ACCESS_TOKEN)
    with open("sample_data.json", 'w') as f:
        json.dump(timeline, f, default=str)
    """
