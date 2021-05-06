#!/usr/bin/env python3
# Copyright (c) 2017 Qumulo, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy of
# the License at http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.

import os
import csv
import time
import calendar
import datetime
import argparse

from collections import OrderedDict
from typing import Any, Mapping, List, Sequence

from qumulo.rest_client import RestClient


CSV_FILENAME = 'qumulo-timeseries-data.csv'
COLUMNS_TO_PROCESS = [
    'iops.read.rate',
    'iops.write.rate',
    'throughput.read.rate',
    'throughput.write.rate',
    'reclaim.deferred.rate',
    'reclaim.snapshot.rate'
]


def parse_args(args: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Sample program to convert time series to CSVs on a Qumulo cluster.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        'host',
        help='Qumulo Cluster to communicate with'
    )
    parser.add_argument(
        '-u',
        '--user',
        default='admin',
        help='Username for authentication'
    )
    parser.add_argument(
        '-p',
        '--password',
        default='admin',
        help='Password for authentication'
    )
    parser.add_argument(
        '-P',
        '--port',
        type=int,
        default=8000,
        help='REST Port for communicating with the cluster'
    )
    return parser.parse_args(args)


def calculate_begin_time(csv_file_name: str) -> int:
    """
    At most, we'll grab 1 day of data, but if we already have some data
    present, we can just request data since then.
    """
    last_line = None
    if os.path.exists(csv_file_name):
        # read to the last line in the file
        with open(csv_file_name, 'r') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                last_line = row

    if last_line is not None:
        return int(last_line[0]) + 5
    return int(time.time()) - 60 * 60 * 24


def read_time_series_from_cluster(
    host: str,
    user: str,
    password: str,
    port: int
) -> List[Mapping[str, Any]]:
    """Communicates with the cluster to grab the analytics in time series format"""
    rest_client = RestClient(host, port)
    rest_client.login(user, password)
    return rest_client.analytics.time_series_get(begin_time=calculate_begin_time(CSV_FILENAME))


def convert_timeseries_into_dict(
    results: Sequence[Mapping[str, Any]]
) -> Mapping[int, Sequence[str]]:
    """Extracts important values from the timeseries results into a dictionary"""

    if not results:
        return {}

    # Setup empty lists for each timestamp
    data = {}
    for timestamp in results[0]['times']:
        data[int(timestamp)] = [None] * len(COLUMNS_TO_PROCESS)

    # Extract each data point
    for series in results:
        name = series['id']
        if name not in COLUMNS_TO_PROCESS:
            continue

        for timestamp, value in zip(series['times'], series['values']):
            column_idx = COLUMNS_TO_PROCESS.index(name)
            data[int(timestamp)][column_idx] = value

    return data


def write_csv_to_file(data: Mapping[int, Sequence[str]], filename: str) -> None:
    """Write the provided data to the file, creating headers if needed"""
    should_add_headers = not os.path.exists(filename) or os.path.getsize(filename) == 0

    with open(filename, 'a') as output_file:
        if should_add_headers:
            output_file.write('unix.timestamp,gmtime,' + ','.join(COLUMNS_TO_PROCESS) + '\r\n')

        for ts in sorted(data):
            gmt = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(ts))
            output_file.write(f'{ts},{gmt},' + ','.join([str(d) for d in data[ts]]) + '\r\n')


def main(sys_args: Sequence[str]):
    args = parse_args(sys_args)
    results = read_time_series_from_cluster(
            args.host, args.user, args.password, args.port)
    data = convert_timeseries_into_dict(results)
    write_csv_to_file(data, CSV_FILENAME)


if __name__ == '__main__':
    main(sys.argv[1:])
