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
from typing import Sequence

from qumulo.rest_client import RestClient


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


def main():
    args = parse_args(sys.argv)
    rc = RestClient(args.host, args.port)
    rc.login(args.user, args.passwd);

    last_line = None
    columns = ['iops.read.rate', 'iops.write.rate',
               'throughput.read.rate', 'throughput.write.rate',
               'reclaim.deferred.rate', 'reclaim.snapshot.rate']

    csv_file_name = 'qumulo-timeseries-data.csv'

    if os.path.exists(csv_file_name):
        # read to the last line in the file
        with open(csv_file_name, 'rb') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                last_line = row

    # at most we'll have 1 day of data
    begin_time = int(time.time()) - 60 * 60 * 24
    # otherwise, pull only the latest data, if we already have a file
    if last_line is not None:
        begin_time = int(last_line[0]) + 5
    results = rc.analytics.time_series_get(begin_time = begin_time)
    num_results = len(results[0]['values'])
    print(f'Appending {num_results} results to "{csv_file_name}".')
    data = {}
    for i in range(0,len(results[0]['times'])-1):
        ts = results[0]['times'][i]
        data[ts] = [None] * len(columns)

    for series in results:
        if series['id'] not in columns:
            continue
        for i in range(0,len(series['values'])):
            ts = series['times'][i]
            data[ts][columns.index(series['id'])] = series['values'][i]

    fw = open(csv_file_name, 'a')
    if last_line is None:
        fw.write('unix.timestamp,gmtime,' + ','.join(columns) + '\r\n')
    for ts in sorted(data):
        gmt = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(ts))
        fw.write(f'{ts},{gmt},' + ','.join([str(d) for d in data[ts]]) + '\r\n')
    fw.close()


# Main
if __name__ == '__main__':
    main()
