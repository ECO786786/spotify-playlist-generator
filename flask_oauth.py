import spotipy
from spotipy.oauth2 import SpotifyOAuth
from flask import Flask, request, redirect, session, url_for
import os
import pandas as pd 
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")
redirect_uri = os.getenv("REDIRECT_URI")
scope = os.getenv("SCOPE")

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['SESSION_COOKIE_NAME'] = 'Spotify OAuth Session'

sp_oauth = SpotifyOAuth(client_id, client_secret, redirect_uri, scope=scope)

@app.route('/')
def login():
    # Redirect user to Spotify's OAuth page
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@app.route('/callback')
def callback():
    # Get the access token from the callback URL
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)
    session['token_info'] = token_info
    return redirect(url_for('generate_playlists'))

@app.route('/generate_playlists')
def generate_playlists():
    token_info = session.get('token_info', None)
    if not token_info:
        return redirect('/')

    # Read the clustered songs from the CSV file
    df = pd.read_csv('clustered_songs_two.csv')
    sp = spotipy.Spotify(auth=token_info['access_token'])
    user = sp.current_user()
    username = user['id']

    # Number of clusters (40)
    n_clusters = df['cluster'].nunique()

    playlist_collection = {}

    for i in range(n_clusters):
        # Create a playlist for each cluster
        playlist_name = f'my_playlist_cluster_{i}'
        playlist_description = 'This playlist is generated from cluster analysis.'

        # Create the playlist on Spotify
        playlist = sp.user_playlist_create(user=username, name=playlist_name, public=True, description=playlist_description)
        playlist_id = playlist['id']

        # Select 10 random songs from the current cluster
        id_list = list(df.loc[df["cluster"] == i].sample(10).id)
        uris = [f'spotify:track:{track_id.strip()}' for track_id in id_list]

        # Add tracks to the playlist
        sp.user_playlist_add_tracks(user=username, playlist_id=playlist_id, tracks=uris)

        playlist_collection[playlist_name] = playlist_id

    return f"Playlists created successfully: {playlist_collection}"

if __name__ == '__main__':
    app.run(port=8888)
