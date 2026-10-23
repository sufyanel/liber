# -*- coding: utf-8 -*-

from odoo.exceptions import AccessDenied, ValidationError
from odoo.tests.common import HttpCase, tagged


@tagged('post_install', '-at_install')
class TestLoginAliases(HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.dale = cls.env['res.users'].create({'name': 'Dale', 'login': 'dale@liberholdings.com', 'password': 'Str0ng-pass-123'})
        cls.liz = cls.env['res.users'].create({'name': 'Liz', 'login': 'liz@liberholdings.com', 'password': 'An0ther-pass-456'})
        cls.env['res.users.login.alias'].create([
            {'name': 'Dale@Mail.GlobElectric.com', 'user_id': cls.dale.id},
            {'name': 'dale@mail.rbcindustrial.com', 'user_id': cls.dale.id},
        ])

    def _auth(self, login, password):
        # a real sign-in through the web session, as on the website login page
        session = self.authenticate(login, password)
        return session.uid

    def test_01_main_login_still_works(self):
        self.assertEqual(self._auth('dale@liberholdings.com', 'Str0ng-pass-123'), self.dale.id)

    def test_02_alias_signs_in_as_same_user_any_case(self):
        self.assertEqual(self._auth('dale@mail.globelectric.com', 'Str0ng-pass-123'), self.dale.id)
        self.assertEqual(self._auth('DALE@MAIL.RBCINDUSTRIAL.COM', 'Str0ng-pass-123'), self.dale.id)

    def test_03_wrong_password_refused(self):
        with self.assertRaises(AccessDenied):
            self._auth('dale@mail.globelectric.com', 'wrong')

    def test_04_alias_cannot_be_another_users_login(self):
        with self.assertRaises(ValidationError):
            self.env['res.users.login.alias'].create({'name': 'liz@liberholdings.com', 'user_id': self.dale.id})

    def test_05_new_login_cannot_reuse_an_alias(self):
        with self.assertRaises(ValidationError):
            self.env['res.users'].create({'name': 'Intruder', 'login': 'dale@mail.globelectric.com', 'password': 'x' * 12})

    def test_06_unknown_address_refused(self):
        with self.assertRaises(AccessDenied):
            self._auth('nobody@mail.globelectric.com', 'Str0ng-pass-123')
