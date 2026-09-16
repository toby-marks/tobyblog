#!/usr/bin/env python3
"""Fetch the full track list for a Spotify playlist into data/jukebox.json.

Uses the Spotify Web API client-credentials flow (no user login required for
public playlists). Standard library only.

Usage:
    export SPOTIFY_CLIENT_ID=...
    export SPOTIFY_CLIENT_SECRET=...
    python3 fetch_spotify_playlist.py                    # default jukebox playlist
    python3 fetch_spotify_playlist.py --playlist-id XYZ  # any playlist

The playlist ID comes from the playlist URL:
    https://open.spotify.com/playlist/<ID>?si=...

If credentials are missing the script exits 0 without touching the existing
data file, so committed data keeps CI builds working when secrets are absent.
"""
import argparse
import base64
import json
import os
import sys
import urllib.parse
import urllib.request

DEFAULT_PLAYLIST_ID = "2Sm7xsMO0FooUoxbNnYzpg"  # Lost Halloween Music
TOKEN_URL = "https://accounts.spotify.com/api/token"
API_URL = "https://api.spotify.com/v1/playlists/{id}"
OUT_PATH = os.path.join("data", "jukebox.json")

# Only request the fields we actually use; keeps the payload small.
FIELDS = (
    "name,description,images,external_urls,tracks(total,next),"
    "tracks.items(track(id,name,artists(name),album(name,images),"
    "duration_ms,external_urls))"
)


def get_token(client_id, client_secret):
    auth = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    req = urllib.request.Request(
        TOKEN_URL,
        data=b"grant_type=client_credentials",
        headers={
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)["access_token"]


def get_json(url, token):
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def get_playlist(token, playlist_id):
    query = urllib.parse.urlencode({"fields": FIELDS, "limit": 100})
    pl = get_json(f"{API_URL.format(id=playlist_id)}?{query}", token)
    items = pl["tracks"]["items"]
    next_url = pl["tracks"].get("next")
    while next_url:  # paginate if the playlist has more than 100 tracks
        page = get_json(next_url, token)
        items.extend(page.get("items", []))
        next_url = page.get("next")
    pl["tracks"]["items"] = items
    return pl


def medium(images):
    """Middle album art variant (~300px); Spotify returns sizes descending."""
    if not images:
        return ""
    return images[min(1, len(images) - 1)]["url"]


def transform(pl):
    tracks = []
    for i, item in enumerate(pl["tracks"]["items"], 1):
        t = item.get("track") or {}
        if not t.get("id"):
            continue  # local files / removed episodes have no id
        tracks.append({
            "number": i,
            "id": t["id"],
            "name": t.get("name", ""),
            "artists": [a["name"] for a in t.get("artists", [])],
            "album": t.get("album", {}).get("name", ""),
            "art": medium(t.get("album", {}).get("images", [])),
            "duration_ms": t.get("duration_ms", 0),
            "url": t.get("external_urls", {}).get("spotify", ""),
        })
    return {
        "id": pl.get("id") or "",
        "name": pl.get("name", ""),
        "description": pl.get("description", ""),
        "image": pl["images"][0]["url"] if pl.get("images") else "",
        "url": pl.get("external_urls", {}).get("spotify", ""),
        "track_count": len(tracks),
        "tracks": tracks,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--playlist-id",
                    default=os.environ.get("SPOTIFY_PLAYLIST_ID", DEFAULT_PLAYLIST_ID))
    ap.add_argument("--out", default=OUT_PATH)
    args = ap.parse_args()

    client_id = os.environ.get("SPOTIFY_CLIENT_ID")
    client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET")
    if not client_id or not client_secret:
        print("SPOTIFY_CLIENT_ID/SPOTIFY_CLIENT_SECRET not set; "
              "keeping existing jukebox data.")
        return

    pl = get_playlist(get_token(client_id, client_secret), args.playlist_id)
    data = transform(pl)
    data["id"] = args.playlist_id  # fields filter omits it; record the request

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"Wrote {len(data['tracks'])} tracks from \"{data['name']}\" to {args.out}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit("\nInterrupted.")
