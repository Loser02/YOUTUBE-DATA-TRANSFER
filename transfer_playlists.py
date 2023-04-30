import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import json

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.errors import HttpError

def authenticate_account(scope, client_secrets_files):
    for client_secrets_file in client_secrets_files:
        try:
            flow = InstalledAppFlow.from_client_secrets_file(client_secrets_file, scope)
            return flow.run_local_server(port=0, prompt='consent')
        except HttpError as error:
            print(f"API quota reached for {client_secrets_file}. Trying next file.")
            continue
    raise Exception("All client secrets files reached their API quota.")

def get_playlists(youtube, channelId):
    playlists = []
    nextPageToken = None

    while True:
        request = youtube.playlists().list(
            part="snippet",
            channelId=channelId,
            maxResults=50,
            pageToken=nextPageToken
        )
        response = request.execute()

        for item in response["items"]:
            playlists.append(item["id"])

        nextPageToken = response.get("nextPageToken")
        if nextPageToken is None:
            break

    return playlists

def get_videos_from_playlist(youtube, playlist_id):
    videos = []
    nextPageToken = None

    while True:
        request = youtube.playlistItems().list(
            part="snippet",
            playlistId=playlist_id,
            maxResults=50,
            pageToken=nextPageToken
        )
        response = request.execute()

        for item in response["items"]:
            videos.append(item["snippet"]["resourceId"]["videoId"])

        nextPageToken = response.get("nextPageToken")
        if nextPageToken is None:
            break

    return videos

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

def main_transfer_playlists():
    scope = [
        "https://www.googleapis.com/auth/youtube.force-ssl",
        "https://www.googleapis.com/auth/youtube"
    ]
    client_secrets_files = ["client_secrets.json"] + [f"client_secrets_{i}.json" for i in range(1, 11)]
    source_credentials = authenticate_account(scope, client_secrets_files)
    target_credentials = authenticate_account(scope, client_secrets_files)
    youtube_source = googleapiclient.discovery.build("youtube", "v3", credentials=source_credentials)
    youtube_target = googleapiclient.discovery.build("youtube", "v3", credentials=target_credentials)

    source_channel_request = youtube_source.channels().list(part="snippet", mine=True)
    source_channel_id = source_channel_request.execute()["items"][0]["id"]

    playlists = get_playlists(youtube_source, source_channel_id)
    transferred_filename = "transferred_playlists.json"
    skipped_filename = "skipped_playlists.json"
    transferred_ids = read_ids(transferred_filename)
    skipped_ids = read_ids(skipped_filename)

    # Transfer playlists
    for playlist_id in playlists:
        if playlist_id not in transferred_ids and playlist_id not in skipped_ids:
            try:
                playlist_request = youtube_source.playlists().list(part="snippet", id=playlist_id)
                playlist_response = playlist_request.execute()
                playlist_title = playlist_response["items"][0]["snippet"]["title"]

                # Create a new playlist in the target account
                new_playlist = youtube_target.playlists().insert(part="snippet,status", body={
                    "snippet": {
                        "title": playlist_title,
                        "description": "Transferred playlist"
                    },
                    "status": {
                        "privacyStatus": "private"
                    }
                }).execute()

                new_playlist_id = new_playlist["id"]

                # Get videos from the source playlist and add them to the new playlist
                videos = get_videos_from_playlist(youtube_source, playlist_id)
                for video_id in videos:
                    try:
                        youtube_target.playlistItems().insert(part="snippet", body={
                            "snippet": {
                                "playlistId": new_playlist_id,
                                "resourceId": {
                                    "kind": "youtube#video",
                                    "videoId": video_id
                                }
                            }
                        }).execute()
                    except googleapiclient.errors.HttpError as error:
                        print(f"Error adding video {video_id} to the playlist: {error}")

                transferred_ids.append(playlist_id)
            except googleapiclient.errors.HttpError as error:
                print(f"Error: {error}")
                print(f"Skipping playlist ID {playlist_id}")
                if playlist_id not in skipped_ids:
                    skipped_ids.append(playlist_id)
        else:
            print(f"Playlist ID {playlist_id} already transferred or skipped.")

    write_ids(transferred_filename, transferred_ids)
    write_ids(skipped_filename, skipped_ids)
    print("Playlists transferred successfully.")

if __name__ == "__main__":
    main_transfer_playlists()


