from __future__ import print_function

import os.path
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/contacts.readonly']


def fetch_google_contacts():
    """Shows basic usage of the People API.
    Prints the name of the first 10 connections.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.

    # Get the current directory where your script is located
    current_directory = Path(__file__).parent

    # Construct the path to the data folder within the module
    data_folder_path = current_directory / '../data'

    # Append the file name to the data folder path
    token_file_name = 'token.json'
    creds_file_name = 'credentials.json'
    token_file_path = data_folder_path / token_file_name
    creds_file_path = data_folder_path / creds_file_name

    # Get the absolute path as a string
    absolute_token_file_path = str(token_file_path)
    absolute_creds_file_path = str(creds_file_path)

    if os.path.exists(absolute_token_file_path):
        creds = Credentials.from_authorized_user_file(absolute_token_file_path, SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(absolute_creds_file_path, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(absolute_token_file_path, 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('people', 'v1', credentials=creds)

        # Call the People API
        results = service.people().connections().list(
            resourceName='people/me',
            pageSize=1000,
            personFields='names,emailAddresses,addresses,photos,phoneNumbers,organizations').execute()
        connections = results.get('connections', [])
        while 'nextPageToken' in results:
            # Make the subsequent request with the nextPageToken
            results = service.people().connections().list(
                resourceName='people/me',
                pageSize=1000,  # Set the desired page size
                personFields='names,emailAddresses,addresses,photos,phoneNumbers,organizations',
                pageToken=results['nextPageToken']).execute()

            connections.extend(results.get('connections', []))
        return connections
    except HttpError as err:
        print(err)


if __name__ == '__main__':
    fetch_google_contacts()
