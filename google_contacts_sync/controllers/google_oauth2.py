import json
import webbrowser
import requests
import base64
import logging

from odoo import http, _
from odoo.http import request
from odoo.exceptions import ValidationError

from werkzeug.urls import url_join
from werkzeug.wrappers import Response
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ['https://www.googleapis.com/auth/contacts.readonly']

logger = logging.getLogger(__name__)


class GoogleOAuthController(http.Controller):

    @staticmethod
    def collect_data(google_token):
        data = []
        google_labels = []
        try:
            data.append(google_token)
            service = build('people', 'v1', credentials=google_token)
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

            resource_names = list()
            groups = service.contactGroups().list().execute()
            groups = groups.get('contactGroups')

            for group in groups:
                if group.get('name') in ['Vendor', 'Lead', 'Customer']:
                    resource_names.append(group.get('resourceName'))
                    google_labels.append(group)

            valid_contacts = list()
            for connection in connections:
                memberships = connection.get('memberships')
                if memberships:
                    labels = list()
                    for membership in memberships:
                        resource_name = membership.get('contactGroupMembership').get('contactGroupResourceName')
                        if not resource_name:
                            continue

                        for label in google_labels:
                            if resource_name == label.get("resourceName"):
                                labels.append(label.get("name"))
                    if labels:
                        connection["google_labels"] = labels
                        valid_contacts.append(connection)
            GoogleOAuthController.sync_google_data(valid_contacts)
        except Exception as e:
            raise e

    @staticmethod
    def sync_google_data(data):

        try:
            logger.info(".....Now about to Sync Google Data.....")
            google_contacts = request.env['res.partner'].search([('is_google_contact', '=', True)])

            for rec in data:
                # Avoiding replication of same contacts, filtering by their email and name
                if rec.get('emailAddresses'):
                    email = rec.get('emailAddresses', [])[0].get('value')
                else:
                    email = "None"
                if rec.get('names'):
                    name = rec.get('names', [])[0].get('displayName')
                else:
                    name = "None"

                if name not in google_contacts.mapped('name') or email not in google_contacts.mapped('email'):
                    # Every contact should be a person, given google contact flag and address set to private address
                    vals = {'company_type': 'person', 'is_google_contact': True, 'type': 'contact'}
                    names = rec.get('names', [])
                    if names:
                        vals['name'] = names[0].get('displayName')
                    emails = rec.get('emailAddresses', [])
                    if emails:
                        vals['email'] = emails[0].get('value')

                    # Dividing addresses based on 5 different fields of odoo for address, state is not provided by
                    # Google
                    addresses = rec.get('addresses', [])
                    if addresses:
                        vals['street'] = addresses[0].get('streetAddress')
                        vals['street2'] = addresses[0].get('extendedAddress')
                        vals['city'] = addresses[0].get('city')
                        vals['zip'] = addresses[0].get('postalCode')
                        vals['country_id'] = request.env['res.country'].search(
                            [('code', '=', addresses[0].get('country'))]).id

                    # taking image url converting it into bytes and then encoding it into base64
                    photos = rec.get('photos', [])
                    if photos:
                        photo = photos[0].get('url')
                        response = requests.get(photo, stream=True)
                        if response.status_code == 200:
                            base64encoded = base64.b64encode(response.content)
                            vals['image_1920'] = base64encoded
                        else:
                            raise ValidationError(_(f"Failed to download image from URL: {photo}"))
                else:
                    continue

                # getting unique phone number values for phone and mobile in odoo, if type isn't mentioned or anyone
                # of them is missing, first phonenumbers will be picked
                phone_numbers = rec.get('phoneNumbers', [])
                if phone_numbers and any(numbers.get('type') for numbers in phone_numbers):
                    for number in phone_numbers:
                        if number.get('type') == 'home':
                            vals['phone'] = number.get('canonicalForm')
                        elif number.get('type') == 'mobile':
                            vals['mobile'] = number.get('canonicalForm')
                    if 'phone' not in vals:
                        vals['phone'] = phone_numbers[0].get('canonicalForm')
                    if 'mobile' not in vals and len(phone_numbers) > 1:
                        vals['phone'] = phone_numbers[1].get('canonicalForm')
                elif phone_numbers:
                    vals['phone'] = phone_numbers[0].get('canonicalForm')
                    if len(phone_numbers) > 1:
                        vals['mobile'] = phone_numbers[1].get('canonicalForm')

                # organizations giving away both job position as title and company as its name, company id will be
                # searched if found, it will be set as parent by default
                organizations = rec.get('organizations', [])
                if organizations:
                    company = organizations[0].get('name')
                    vals['parent_id'] = request.env['res.partner'].search([('name', '!=', False)]).filtered(
                        lambda x: x.name.lower() == company.lower()).id or False
                    vals['function'] = organizations[0].get('title')

                # labels are actually groups which are termed as labels in google contacts to sort every contact
                # label wise
                labels = rec.get('google_labels', [])
                if labels:
                    all_matching_labels_ids = request.env['google.labels'].search([('name', 'in', labels)])
                    vals['google_label_ids'] = all_matching_labels_ids.ids
                request.env['res.partner'].create(vals)
                logger.info(".....End of the Entire Process.....")
        except Exception as e:
            raise e

    @http.route('/oauth/contacts', type='http', auth='public', website=True)
    def oauth_contacts_sync(self, **kwargs):
        Config = request.env['ir.config_parameter'].sudo()
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        redirect_uri = url_join(base_url, '/oauth/contacts')
        credentials = Config.get_param('google_contacts_credentials')
        google_loaded = json.loads(credentials)
        flow = Flow.from_client_config(google_loaded, SCOPES, redirect_uri=redirect_uri)

        response = request.httprequest.url
        flow.fetch_token(authorization_response=response)

        GoogleOAuthController.collect_data(flow.credentials)
        response_data = {'status': 'Success'}
        http_response = Response(json.dumps(response_data), content_type='application/json')
        return http_response

