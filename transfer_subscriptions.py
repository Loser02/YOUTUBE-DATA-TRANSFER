import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import json

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

def authenticate_account(scope):
    flow = InstalledAppFlow.from_client_secrets_file("client_secrets.json", scope)
    return flow.run_local_server(port=0, prompt='consent')

def get_subscriptions(youtube, channelId):
    subscriptions = []
    nextPageToken = None

    while True:
        request = youtube.subscriptions().list(
            part="snippet",
            channelId=channelId,
            maxResults=50,
            pageToken=nextPageToken
        )
        response = request.execute()

        for item in response["items"]:
            subscriptions.append(item["snippet"]["resourceId"]["channelId"])

        nextPageToken = response.get("nextPageToken")
        if nextPageToken is None:
            break

    return subscriptions

def read_ids(filename):
    try:
        with open(filename, "r") as file:
            ids = json.load(file)
    except FileNotFoundError:
        ids = []

    return ids

def write_ids(filename, ids):
    with open(filename, "w") as file:
        json.dump(ids, file)

def main_transfer_subscriptions():
    scope = [
        "https://www.googleapis.com/auth/youtube.force-ssl",
        "https://www.googleapis.com/auth/youtube"
    ]
    source_credentials = authenticate_account(scope)
    target_credentials = authenticate_account(scope)
    youtube_source = googleapiclient.discovery.build("youtube", "v3", credentials=source_credentials)
    youtube_target = googleapiclient.discovery.build("youtube", "v3", credentials=target_credentials)

    source_channel_request = youtube_source.channels().list(part="snippet", mine=True)
    source_channel_id = source_channel_request.execute()["items"][0]["id"]

    subscriptions = get_subscriptions(youtube_source, source_channel_id)
    transferred_filename = "transferred_subscriptions.json"
    skipped_filename = "skipped_subscriptions.json"
    transferred_ids = read_ids(transferred_filename)
    skipped_ids = read_ids(skipped_filename)

    # Transfer subscriptions
    for channel_id in subscriptions:
        if channel_id not in transferred_ids and channel_id not in skipped_ids:
            try:
                youtube_target.subscriptions().insert(part="snippet", body={
                    "snippet": {
                        "resourceId": {
                            "kind": "youtube#channel",
                            "channelId": channel_id
                        }
                    }
                }).execute()
                transferred_ids.append(channel_id)
            except googleapiclient.errors.HttpError as error:
                print(f"Error: {error}")
                print(f"Skipping subscription to channel ID {channel_id}")
                if channel_id not in skipped_ids:
                    skipped_ids.append(channel_id)
        else:
            print(f"Subscription to channel ID {channel_id} already transferred or skipped.")

    write_ids(transferred_filename, transferred_ids)
    write_ids(skipped_filename, skipped_ids)
    print("Subscriptions transferred successfully.")

if __name__ == "__main__":
    main_transfer_subscriptions()
