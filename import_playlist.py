import re
from ytmusicapi import YTMusic

def extract_playlist_id(url: str) -> str:
    match = re.search(r"list=([a-zA-Z0-9_-]+)", url)
    return match.group(1) if match else url

def get_playlist_title_and_song_names(playlist_url):
    playlist_id = extract_playlist_id(playlist_url)

    ytmusic = YTMusic()
    playlist_data = ytmusic.get_playlist(playlist_id)

    title = playlist_data["title"]
    song_names = []

    for song in playlist_data["tracks"]:
        # artists = [ artist["name"] for artist in song["artists"] ]
        song_names.append(song["title"])

    return title, song_names