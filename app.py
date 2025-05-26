from flask import Flask, redirect, request, session, url_for
import os
import google.auth.transport.requests
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
import pathlib

app = Flask(__name__)
app.secret_key = "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"  # Change this to a secure secret key

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"  # For local dev only (HTTP)

# Path to your downloaded client_secret.json
CLIENT_SECRETS_FILE = "client_secret.json"

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

@app.route('/')
def index():
    return '''
    <h2>Welcome to the Google Drive Connector</h2>
    <a href="/login">
        <button style="padding: 10px 20px; font-size: 16px;">Connect Google Drive</button>
    </a>
    '''

@app.route('/login')
def login():
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=url_for('callback', _external=True)
    )
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true'
    )
    session['state'] = state
    return redirect(authorization_url)

@app.route('/oauth2callback')
def callback():
    state = session['state']
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        state=state,
        redirect_uri=url_for('callback', _external=True)
    )
    flow.fetch_token(authorization_response=request.url)

    credentials = flow.credentials
    session['credentials'] = {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }

    return redirect(url_for('drive'))

@app.route('/drive')
def drive():
    if 'credentials' not in session:
        return redirect('login')

    creds = Credentials(**session['credentials'])

    # Optional: update session with refreshed token
    if creds.expired and creds.refresh_token:
        request_ = google.auth.transport.requests.Request()
        creds.refresh(request_)
        session['credentials']['token'] = creds.token

    return '✅ Google Drive is connected! You can now use their data.'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
