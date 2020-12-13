from math import floor
from pathlib import Path
from time import time as timestamp

import jwt
import requests

BASE_URL = 'https://api.github.com'
APP_ID = 92513
INSTALLATION_ID = 13498280

session = requests.Session()
session.headers.update({
    'Accept': 'application/vnd.github.v3+json'
})


def get_private_key() -> bytes:
    directory = Path(__file__).resolve().parent.parent / 'keys'
    for path in directory.iterdir():
        if path.name.endswith('.pem'):
            with path.open('rb') as handler:
                return handler.read()
    raise FileNotFoundError('Private key file not found. Please place your private key in the `keys` directory.')


def get_jwt_token() -> str:
    """
    Generate a JWT token with the app's private key.

    Reference: https://docs.github.com/developers/apps/authenticating-with-github-apps#authenticating-as-a-github-app

    :return: A JWT token representing the app it self.
    """
    key = get_private_key()
    time = floor(timestamp())
    return jwt.encode({
        'iat': time,  # Issued at time
        'exp': time + 10 * 60,  # Expiry (10 minutes)
        'iss': APP_ID  # GitHub App's identifier
    }, key, 'RS256').decode('utf-8')


def get_access_token() -> str:
    """
    Creates an installation access token for the app's installation on an account.

    Reference: https://docs.github.com/rest/reference/apps#create-an-installation-access-token-for-an-app

    :return: An installation access token.
    """
    token = get_jwt_token()
    response = session.post(f'{BASE_URL}/app/installations/{INSTALLATION_ID}/access_tokens', headers={
        'Authorization': f'Bearer {token}'
    })
    response.raise_for_status()
    return response.json()['token']
