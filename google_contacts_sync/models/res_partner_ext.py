from odoo import fields, models, api, _
from ..controllers.google_api_script import fetch_google_contacts
import requests
from odoo.exceptions import ValidationError
import base64


class ResPartnerExt(models.Model):
    _inherit = 'res.partner'

    is_google_contact = fields.Boolean()

    def sync_contacts(self):
        res = fetch_google_contacts()
        google_contacts = self.search([('is_google_contact', '=', True)])
        for rec in res:

            # avoiding replication of same contacts, filtering by their email and name
            if not rec.get('names', [])[0].get('displayName') in google_contacts.mapped('name') or not \
                    rec.get('emailAddresses', [])[0].get('value') in google_contacts.mapped('email'):

                # every contact should be a person, given google contact flag and address set to private address
                vals = {'company_type': 'person', 'is_google_contact': True, 'type': 'private'}
                names = rec.get('names', [])
                if names:
                    vals['name'] = names[0].get('displayName')
                emails = rec.get('emailAddresses', [])
                if emails:
                    vals['email'] = emails[0].get('value')

                # dividing addresses based on 5 different fields of odoo for address, state is not provided by google
                addresses = rec.get('addresses', [])
                if addresses:
                    vals['street'] = addresses[0].get('streetAddress')
                    vals['street2'] = addresses[0].get('extendedAddress')
                    vals['city'] = addresses[0].get('city')
                    vals['zip'] = addresses[0].get('postalCode')
                    vals['country_id'] = self.env['res.country'].search([('code', '=', addresses[0].get('country'))]).id

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

                # getting unique phone number values for phone and mobile in odoo, if type isn't mentioned or anyone of
                # them is missing, first phonenumbers will be picked
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
                    vals['parent_id'] = self.search([('name', '!=', False)]).filtered(
                        lambda x: x.name.lower() == company.lower()).id or False
                    vals['function'] = organizations[0].get('title')
                self.create(vals)
