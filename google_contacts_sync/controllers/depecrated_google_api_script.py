from __future__ import print_function

import json
import webbrowser

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow, Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/contacts.readonly']

# Not to be used now. The logic was shifted to controllers.
# Still kept in the dir to test in case of error in original.
def fetch_google_contacts(credentials, user_token):
    """Shows basic usage of the People API.
    Prints the name of the first 10 connections.
    """
    creds = None
    coords = []
    google_labels = []
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.

    if user_token:
        g_token_info = json.loads(user_token)
        creds = Credentials.from_authorized_user_info(g_token_info, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            g_cred_info = json.loads(credentials)
            flow = InstalledAppFlow.from_client_config(g_cred_info, SCOPES)
            creds = flow.run_local_server(open_browser=True)


    try:
        coords.append(creds)
        service = build('people', 'v1', credentials=creds)

        # Call the People API
        results = service.people().connections().list(
            resourceName='people/me',
            pageSize=1000,
            personFields='names,emailAddresses,addresses,photos,phoneNumbers,organizations,memberships').execute()
        connections = results.get('connections', [])
        while 'nextPageToken' in results:
            # Make the subsequent request with the nextPageToken
            results = service.people().connections().list(
                resourceName='people/me',
                pageSize=1000,  # Set the desired page size
                personFields='names,emailAddresses,addresses,photos,phoneNumbers,organizations,memberships',
                pageToken=results['nextPageToken']).execute()

            connections.extend(results.get('connections', []))
        for contact in connections:
            memberships = contact.get('memberships', [])
            label_names = []

            for membership in memberships:
                contact_group_id = membership['contactGroupMembership']['contactGroupId']

                # Fetch the contact group details using the contact_group_id
                group_details = service.contactGroups().get(
                    resourceName=f'contactGroups/{contact_group_id}'
                ).execute()
                label = group_details.get('name', '')

                # Get the label name and append it to label_names list
                label_names.append(label)

                # creating another list so can create separate label records avoiding duplication
                if label not in google_labels:
                    google_labels.append(label)

            # Add the label_names list to the contact dictionary
            contact['label_names'] = label_names
        coords.append(connections)
        coords.append(google_labels)
        return coords
    except HttpError as err:
        print(err)


if __name__ == '__main__':
    fetch_google_contacts(google_creds=None, token=None)
