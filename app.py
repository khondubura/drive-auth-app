from flask import Flask, redirect, request, session, url_for, jsonify
import os
import google.auth.transport.requests
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

app = Flask(__name__)
app.secret_key = "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"

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

CLIENT_SECRETS_FILE = "client_secret.json"
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

# Temporary in-memory token store (use a DB in production)
user_tokens = {}

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
    user_id = request.args.get('userId')
    user_email = request.args.get('email')

    session['user_id'] = user_id
    session['user_email'] = user_email

    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri="https://drive-auth-app.onrender.com/oauth2callback"
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
        redirect_uri="https://drive-auth-app.onrender.com/oauth2callback"
    )
    flow.fetch_token(authorization_response=request.url)

    credentials = flow.credentials
    user_id = session.get('user_id')

    user_tokens[user_id] = {
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
    user_id = session.get('user_id')
    creds_data = user_tokens.get(user_id)

    if not creds_data:
        return redirect(url_for('login'))

    creds = Credentials(**creds_data)

    if creds.expired and creds.refresh_token:
        request_ = google.auth.transport.requests.Request()
        creds.refresh(request_)
        user_tokens[user_id]['token'] = creds.token

    return f"✅ Google Drive connected for user {user_id}"

@app.route('/files')
def list_drive_files():
    user_id = session.get('user_id')
    creds_data = user_tokens.get(user_id)

    if not creds_data:
        return '<h3 style="color: #DDD8CB; font-family: Montserrat;">Please log in first.</h3>'

    creds = Credentials(**creds_data)

    if creds.expired and creds.refresh_token:
        request_ = google.auth.transport.requests.Request()
        creds.refresh(request_)
        user_tokens[user_id]['token'] = creds.token

    service = build('drive', 'v3', credentials=creds)
    results = service.files().list(
        pageSize=10,
        fields="files(id, name, mimeType, modifiedTime)"
    ).execute()
    items = results.get('files', [])

    html = f"""
    <html>
    <head>
        <style>
            body {{
                background-color: #5E5747;
                font-family: 'Montserrat', sans-serif;
                color: #DDD8CB;
                padding: 40px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                background-color: #EEEEE9;
                color: #5E5747;
                border-radius: 12px;
                overflow: hidden;
                font-size: 16px;
            }}
            th, td {{
                padding: 14px 20px;
                border-bottom: 1px solid #ccc;
                text-align: left;
            }}
            th {{
                background-color: #DDD8CB;
                color: #5E5747;
            }}
            tr:hover {{
                background-color: #DDD8CB;
                color: #5E5747;
            }}
        </style>
    </head>
    <body>
        <h2>Your Google Drive Files</h2>
        <table>
            <thead>
                <tr>
                    <th>Name</th>
                    <th>Type</th>
                    <th>Modified</th>
                </tr>
            </thead>
            <tbody>
    """

    for file in items:
        html += f"""
            <tr>
                <td>{file['name']}</td>
                <td>{file['mimeType']}</td>
                <td>{file.get('modifiedTime', '—')}</td>
            </tr>
        """

    html += """
            </tbody>
        </table>
    </body>
    </html>
    """

    return html

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
