#!/usr/bin/env python3

import unittest

from parameterized import parameterized

from timeseries_to_csv import parse_args


class ArgparseTest(unittest.TestCase):
    def test_default_arguments(self):
        args = parse_args(['my_host'])
        self.assertEqual(args.host, 'my_host')
        self.assertEqual(args.user, 'admin')
        self.assertEqual(args.password, 'admin')
        self.assertEqual(args.port, 8000)

    @parameterized.expand([['-u'], ['--user']])
    def test_user(self, user_arg: str):
        args = parse_args(['my_host', user_arg, 'my_user'])
        self.assertEqual(args.user, 'my_user')

    @parameterized.expand([['-p'], ['--password']])
    def test_password(self, password_arg: str):
        args = parse_args(['my_host', password_arg, 'my_user'])
        self.assertEqual(args.password, 'my_user')

    @parameterized.expand([['-P'], ['--port']])
    def test_port(self, port_arg: str):
        args = parse_args(['my_host', port_arg, '8001'])
        self.assertEqual(args.port, 8001)

