# Using the Qumulo API Python bindings on Mac OSX

While the Mac comes with Python installed by default, there are a few challenges when attempting to use the Qumulo API. This readme walks you through the setup for using the Qumulo API on Mac OSX and addresses two issues:

1. Dealing with OpenSSL version issues
2. Keeping your environment clean

## Setup and installation

1. Install latest OpenSSL and python
    ```bash
    $ brew update
    $ brew install openssl
    $ brew link /usr/local/opt/openssl/bin/openssl --force  # this isn't guaranteed to work, but "it worked on my machine", even with an error
    $ brew install python --with-brewed-openssl
    # This will install python and python tools to /usr/local/bin rather than the default /usr/bin
    ```
    ```bash
    # confirm everything is working
    $ python3 --version  
    Python 3.<something>
    $ python3 -c "import ssl; print ssl.OPENSSL_VERSION"
    OpenSSL 1.<something> ...
    # If this says 0.something, things haven't installed correctly.
    ```

2. Install virtualenv
    ```bash
    $ pip install virtualenv
    ```

3. Set up and activate Qumulo API virtual environment
    ```bash
    # This will create a new directory called Qumulo API.
    $ virtualenv qumulo_api
    $ source qumulo_api/bin/activate
    ```

4. Install the Qumulo API
    ```bash
    $ pip install qumulo_api
    ... Successfully installed ...
    # verify it's installed, and see path where it's installed
    python3 -c "import qumulo; print qumulo.__file__"
    ```
