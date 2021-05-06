#!/usr/bin/env python3

import time
import os
import unittest

from parameterized import parameterized
from typing import Mapping, Sequence
from unittest.mock import patch

from qumulo.rest_client import RestClient
from timeseries_to_csv import *


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


def assert_expected_output_file_contents(
    testcase: unittest.TestCase,
    filename: str,
    expected_data: Mapping[int, Sequence[str]]
) -> None:
    testcase.assertTrue(os.path.exists(filename))
    remaining_lines = None
    with open(filename, 'r') as csv_file:
        # First line should contain the header
        testcase.assertIn('unix.timestamp', csv_file.readline())
        remaining_lines = csv_file.readlines()

    testcase.assertIsNotNone(remaining_lines)
    testcase.assertEqual(len(expected_data), len(remaining_lines))
    for data_points, line in zip(expected_data.values(), remaining_lines):
        for word in data_points:
            testcase.assertIn(word, line)


class HelperTest(unittest.TestCase):
    def setUp(self):
        self.filename = 'test-file.csv'

    def tearDown(self):
        if os.path.exists(self.filename):
            os.remove(self.filename)

    def test_calculate_begin_time_no_existing_file_uses_last_day(self):
        begin_time = calculate_begin_time(self.filename)

        current_time_minus_one_day = int(time.time()) - (60 * 60 * 24)
        self.assertLessEqual(begin_time, current_time_minus_one_day)

    def test_calculate_begin_time_uses_latest_time_from_existing_file(self):
        with open(self.filename, 'w') as csv_file:
            csv_file.writelines([ '12,\n', '17,\n', '22,\n' ])

        begin_time = calculate_begin_time(self.filename)
        self.assertEqual(begin_time, 27)

    def test_convert_timeseries_into_dict_empty(self):
        timeseries = []
        output = convert_timeseries_into_dict(timeseries)

        # Empty dictionaries evaluate to false
        self.assertFalse(output)

    def test_convert_timeseries_into_dict_with_no_relevant_data(self):
        times = [ 0, 5, 10 ]
        timeseries = [
            {
                'times': times,
                'id': 'foo'
            },
            {
                'times': times,
                'id': 'bar'
            },
            {
                'times': times,
                'id': 'baz'
            }
        ]

        output = convert_timeseries_into_dict(timeseries)

        # Three timestamps, so should be three rows
        self.assertEqual(len(output), 3)
        self.assertEqual(list(output.keys()), times)

        # No relevant data to process, all entries should be empty
        for row in output.values():
            self.assertEqual(len(row), len(COLUMNS_TO_PROCESS))
            for entry in row:
                self.assertIsNone(entry)

    def test_convert_timeseries_into_dict_with_listed_columns(self):
        # N.B. times correspond to the value below
        times = [ 0, 5, 10 ]
        values = [ 'foo', 'bar', 'baz' ]

        timeseries = []
        for column_id in COLUMNS_TO_PROCESS:
            timeseries.append({
                'times': times,
                'id': column_id,
                'values': values
            })

        output = convert_timeseries_into_dict(timeseries)

        for time, row in output.items():
            expected_value = values[times.index(time)]
            for entry in row:
                self.assertEqual(entry, expected_value)

    def test_write_csv_to_file_creates_headers_if_no_file(self):
        data = {}
        write_csv_to_file(data, self.filename)

        self.assertTrue(os.path.exists(self.filename))
        with open(self.filename, 'r') as csv_file:
            # First line should contain the header
            self.assertIn('unix.timestamp', csv_file.readline())

    def test_write_csv_to_file_creates_headers_if_empty_file(self):
        data = {}

        # Touch the file, so it exists but is empty
        with open(self.filename, 'w'):
            pass

        write_csv_to_file(data, self.filename)

        self.assertTrue(os.path.exists(self.filename))
        with open(self.filename, 'r') as csv_file:
            # First line should contain the header
            self.assertIn('unix.timestamp', csv_file.readline())

    def test_write_csv_to_file_dumps_data_in_csv_format(self):
        data = {
            0: ['foo', 'bar', 'baz'],
            5: ['fiz', 'bang', 'zap'],
            10: ['zot', 'buh', 'gul'],
        }

        write_csv_to_file(data, self.filename)
        assert_expected_output_file_contents(self, self.filename, data)

    def test_write_csv_to_file_appends_to_existing_file(self):
        primary_data = { 0: ['foo', 'bar', 'baz'] }
        secondary_data = { 5: ['fiz', 'bang', 'zap'] }

        write_csv_to_file(primary_data, self.filename)
        write_csv_to_file(secondary_data, self.filename)

        combined_data = primary_data
        combined_data.update(secondary_data)
        assert_expected_output_file_contents(self, self.filename, combined_data)


# N.B. We mock out read_time_series_from_cluster instead of the RestClient
# since the RestClient has dynamic attributes that are difficult to mock. (i.e.
# we can't easily mock the call to rest_client.analytics.time_series_get())
@patch('timeseries_to_csv.read_time_series_from_cluster')
class IntegrationTest(unittest.TestCase):
    def setUp(self):
        self.times = [ 0, 5, 10 ]
        self.values = [ 'foo', 'bar', 'baz' ]

        self.timeseries_from_rest_client = []
        for column_id in COLUMNS_TO_PROCESS:
            self.timeseries_from_rest_client.append({
                'times': self.times,
                'id': column_id,
                'values': self.values
            })

        self.expected_data = {
            0: ['foo'] * len(COLUMNS_TO_PROCESS),
            5: ['bar'] * len(COLUMNS_TO_PROCESS),
            10: ['baz'] * len(COLUMNS_TO_PROCESS)
        }

    def tearDown(self):
        if os.path.exists(CSV_FILENAME):
            os.remove(CSV_FILENAME)

    def test_default_arguments(self, mock_getter):
        mock_getter.return_value = self.timeseries_from_rest_client
        main(['localhost'])

        mock_getter.assert_called_with('localhost', 8000)

        assert_expected_output_file_contents(
                self, CSV_FILENAME, self.expected_data)

    def test_default_arguments(self, mock_getter):
        mock_getter.return_value = self.timeseries_from_rest_client
        main(['localhost'])

        mock_getter.assert_called_with('localhost', 'admin', 'admin', 8000)
        assert_expected_output_file_contents(
                self, CSV_FILENAME, self.expected_data)

    def test_passes_argument_to_rest_client(self, mock_getter):
        mock_getter.return_value = self.timeseries_from_rest_client
        main(['localhost', '-u', 'my_user', '-p', 'my_password', '-P', '8001'])

        mock_getter.assert_called_with(
                'localhost', 'my_user', 'my_password', 8001)
        assert_expected_output_file_contents(
                self, CSV_FILENAME, self.expected_data)

    def test_creates_header_only_file_if_no_data_from_server(self, mock_getter):
        mock_getter.return_value = {}
        main(['localhost'])

        mock_getter.assert_called_with('localhost', 'admin', 'admin', 8000)
        assert_expected_output_file_contents(self, CSV_FILENAME, {})


if __name__ == '__main__':
    unittest.main()
