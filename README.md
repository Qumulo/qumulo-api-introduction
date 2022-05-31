# Introduction to the Qumulo API

Qumulo's software is enhanced, complimented and managed by a robust, RESTful API. The browser-based application is driven 100% by our API. Because of this user-driven design, end-users can also leverage the power and flexibility of this rich API.

All bindings and applications are built on top of the REST standardized endpoint found on each of the Qumulo cluster's nodes. Qumulo's engineering team provides Python library bindings for accessing the API. They've also conveniently packaged up their "qq" tool. **qq** is a command-line interface, used internally at Qumulo for managing the filesystem, testing, and configuration of a cluster, and you can use it too.

Below is a diagram of the Qumulo API ecosystem. The green elements highlight the core components that we'll dive into deeper below.

![Qumulo API Ecosystem][api-ecosytem]

## Installation

1. Install the necessary tools:
    - [**Python 3.8+**](https://www.python.org/downloads/)
    - [**pip** ](https://pip.pypa.io)
    - **curl** (`brew install curl` on a mac or `apt-get install curl` on Ubuntu)
2. Run `pip install qumulo-api`. To install a version of the Python SDK that matches a particular version of Qumulo Core, specify the Qumulo Core version in the command like so: `pip install qumulo-api==5.1.1`.

## Interacting with the Qumulo API

### qq - Qumulo's user-friendly and powerful command-line tool

The Python SDK includes the `qq` command line tool, which is installed into your system's `PATH` so that it can be run from anywhere. With `qq` you can use the power of the Qumulo API from a command line on MacOSX, Windows, or Linux.

```bash
export API_HOSTNAME={your-qumulo-cluster-host-name}
export API_USER={your-qumulo-api-user-name}
export API_PASSWORD={your-qumulo-api-password}

# 1. Login using the credentials above.
$ qq --host $API_HOSTNAME login -u $API_USER -p $API_PASSWORD

# 2. 
$ qq --host $API_HOSTNAME fs_get_stats

# It should return something that looks like this:
{
    "block_size_bytes": 4096,
    "free_size_bytes": "7364635484160",
    "raw_size_bytes": "102420130627584",
    "total_size_bytes": "47953309859840"
}

# 3. See all the commands available:
$ qq

#4. See help on a specific command (such as adding an NFS share):
$ qq nfs_add_share -h

```

```bash 
# For extra credit, install jq ("brew install jq" on a Mac)
# Run this command to see the aggregate capacity for all files and directories in the root path of the Qumulo cluster:
$ qq --host $API_HOSTNAME fs_read_dir_aggregates --path / | \
    jq -r '.files | to_entries[] | [ .value.capacity_usage, .value.name, .value.type] | @tsv' | sort -rn
```


### Python library - Python bindings for accessing the Qumulo API

```bash
# First, setup the basic credentials for your Qumulo cluster. (You might've already done this above.)
export API_HOSTNAME={your-qumulo-cluster-host-name}
export API_USER={your-qumulo-api-user-name}
export API_PASSWORD={your-qumulo-api-password}
```

Then, from the command line, start python `$ python3` and run the following code:
```
import os
from qumulo.rest_client import RestClient

# Create Qumulo python rest client and login
rc = RestClient(os.environ['API_HOSTNAME'], 8000)
rc.login(os.environ['API_USER'], os.environ['API_PASSWORD'])

# Get file system stats
rc.fs.read_fs_stats()
```
If you hit issues related to SSL when trying to run this, please follow these [directions on setting up the Qumulo API on Mac OSX](qumulo-api-on-mac-osx.md).

### **curl** - Raw HTTP requests with the curl command-line tool.

While we don't recommend using this technique for interacting with the Qumulo, API, it can be used to illustrate some of the technical foundations of REST.

```bash
# 1. Set some basic variables to be used by the scripts below.

export API_HOSTNAME={your-qumulo-cluster-host-name}
export API_USER={your-qumulo-api-user-name}
export API_PASSWORD={your-qumulo-api-password}

# 2. Login using the credentials above.
curl -X POST \
       -H "Content-Type: application/json" \
       -k https://$API_HOSTNAME:8000/v1/session/login \
       -d "{\"username\": \"$API_USER\", \"password\": \"$API_PASSWORD\"}"

# This will return a json object that looks something like this:
{"key_id": "eJzjePAoggEIVuQ8BtMGQPyFkQEMGJkgNDMSG8aHqWEHYjYgjklMyc3M8wOyAMmNCVg=", 
 "key": "hRG5EBRltK9Ie3Lf2Q/2l0387ic6gt7Ww29H1xCvNB8=", 
 "algorithm": "hmac-sha-256", 
 "bearer_token": "1:AUQAAABlSnk3K2ZCUkJBTVFWT1k5QnRNR1FQeUZrPNNNOTb9d9DNaPM6eCE1LOx6mQ=="}

# 3. Grab the "bearer_token" value and place it into the command below after the word "Bearer":
curl -X GET \
       -H "Authorization: Bearer 1:AUQAAABlSnk3K2ZCUkJBTVFWT1k5QnRNR1FQeUZrPNNNOTb9d9DNaPM6eCE1LOx6mQ==" \
       -k https://$API_HOSTNAME:8000/v1/file-system

# It should return something that looks like this:
{"raw_size_bytes": "102420130627584", 
 "block_size_bytes": 4096, 
 "total_size_bytes": "47953309859840", 
 "free_size_bytes": "7365139591168"}
```

Now that you've learned some basics regarding curl and the Qumulo API, here's an example of how to: [create, write, read, and delete](create-write-read-delete-with-curl.sh)


[api-ecosytem]: assets/qumulo-api-ecosystem-2017-03.png "Qumulo API Ecosystem"
