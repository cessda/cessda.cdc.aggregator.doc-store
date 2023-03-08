# CESSDA Metadata Aggregator - Document Store #

[![Build Status](https://jenkins.cessda.eu/buildStatus/icon?job=cessda.cdc.aggregator.doc-store%2Fmaster)](https://jenkins.cessda.eu/job/cessda.cdc.aggregator.doc-store/job/master/)
[![Bugs](https://sonarqube.cessda.eu/api/project_badges/measure?project=cessda.cdc.aggregator.doc-store&metric=bugs)](https://sonarqube.cessda.eu/dashboard?id=cessda.cdc.aggregator.doc-store)
[![Code Smells](https://sonarqube.cessda.eu/api/project_badges/measure?project=cessda.cdc.aggregator.doc-store&metric=code_smells)](https://sonarqube.cessda.eu/dashboard?id=cessda.cdc.aggregator.doc-store)
[![Coverage](https://sonarqube.cessda.eu/api/project_badges/measure?project=cessda.cdc.aggregator.doc-store&metric=coverage)](https://sonarqube.cessda.eu/dashboard?id=cessda.cdc.aggregator.doc-store)
[![Duplicated Lines (%)](https://sonarqube.cessda.eu/api/project_badges/measure?project=cessda.cdc.aggregator.doc-store&metric=duplicated_lines_density)](https://sonarqube.cessda.eu/dashboard?id=cessda.cdc.aggregator.doc-store)
[![Lines of Code](https://sonarqube.cessda.eu/api/project_badges/measure?project=cessda.cdc.aggregator.doc-store&metric=ncloc)](https://sonarqube.cessda.eu/dashboard?id=cessda.cdc.aggregator.doc-store)
[![Maintainability Rating](https://sonarqube.cessda.eu/api/project_badges/measure?project=cessda.cdc.aggregator.doc-store&metric=sqale_rating)](https://sonarqube.cessda.eu/dashboard?id=cessda.cdc.aggregator.doc-store)
[![Quality Gate Status](https://sonarqube.cessda.eu/api/project_badges/measure?project=cessda.cdc.aggregator.doc-store&metric=alert_status)](https://sonarqube.cessda.eu/dashboard?id=cessda.cdc.aggregator.doc-store)
[![Reliability Rating](https://sonarqube.cessda.eu/api/project_badges/measure?project=cessda.cdc.aggregator.doc-store&metric=reliability_rating)](https://sonarqube.cessda.eu/dashboard?id=cessda.cdc.aggregator.doc-store)
[![Security Rating](https://sonarqube.cessda.eu/api/project_badges/measure?project=cessda.cdc.aggregator.doc-store&metric=security_rating)](https://sonarqube.cessda.eu/dashboard?id=cessda.cdc.aggregator.doc-store)
[![Technical Debt](https://sonarqube.cessda.eu/api/project_badges/measure?project=cessda.cdc.aggregator.doc-store&metric=sqale_index)](https://sonarqube.cessda.eu/dashboard?id=cessda.cdc.aggregator.doc-store)
[![Vulnerabilities](https://sonarqube.cessda.eu/api/project_badges/measure?project=cessda.cdc.aggregator.doc-store&metric=vulnerabilities)](https://sonarqube.cessda.eu/dashboard?id=cessda.cdc.aggregator.doc-store)

HTTP server providing an API in front of a MongoDB cluster. This
program is part of CESSDA Metadata Aggregator.

Source code is hosted at Bitbucket <https://github.com/cessda/cessda.cdc.aggregator.doc-store>

## Features ##

DocStore provides CRUD access to the records via REST API. It also
features a flexible Query API for filtering records.

DocStore feature list:

  - REST API for full control of records.
  - Query API for flexible filtering of records.
  - Logical deletions.
  - Streaming responses.
  - Support for MongoDB replicas.
  - Helper script to ease initial database setup.

## Requirements ##

  - Python 3.8 or newer.
  - MongoDB 3.6 or newer.

## Installation ##

On Ubuntu 20.04

### Database setup ###

This is an example setup with a single virtual machine containing
three mongodb replicas.


1. Install MongoDB

    ```sh
    sudo apt install mongodb
    ```

2. Create directories for replica data

    ```sh
    sudo mkdir /var/lib/mongodb/{r1,r2,r3}
    sudo chown mongodb:mongodb /var/lib/mongodb/{r1,r2,r3}
    sudo chmod 0755 /var/lib/mongodb/{r1,r2,r3}
    ```


3. Configure single mongodb instance to use r1 replica data directory.

    ```sh
    sudo sed -i 's#dbpath=/var/lib/mongodb#dbpath=/var/lib/mongodb/r1#' /etc/mongodb.conf
    ```


4. Restart mongodb.service

    ```sh
    sudo systemctl restart mongodb.service
    ```


5. Create rootadmin user using the mongo shell

    ```sh
    mongo
    use admin
    db.createUser({user: 'rootadmin', pwd: 'password', roles: [{role: 'root', db: 'admin'}]})
    exit
    ```


6. Stop & disable mongodb.service

    ```sh
    sudo systemctl stop mongodb.service
    sudo systemctl disable mongodb.service
    ```


7. Create directory for mongodb replica configuration

    ```sh
    sudo mkdir /etc/mongodb
    sudo chmod 0755 /etc/mongodb
    ```


8. Generate keyfile for replica authentication

    ```sh
    sudo openssl rand -base64 756 | sudo tee /var/lib/mongodb/auth_key
    sudo chown mongodb:mongodb /var/lib/mongodb/auth_key
    sudo chmod 0600 /var/lib/mongodb/auth_key
    ```

9. Configure replicas. Example for /etc/mongodb/r1.conf.

    ```sh
    storage:
      dbPath: /var/lib/mongodb/r1
      journal:
        enabled: true

    systemLog:
      destination: file
      logAppend: true
      path: /var/lib/mongodb/r1.log

    net:
      port: 27017
      bindIp: 0.0.0.0

    processManagement:
      timeZoneInfo: /usr/share/zoneinfo

    security:
      authorization: enabled
      keyFile: /var/lib/mongodb/auth_key

    replication:
      replSetName: rs_cdcagg
    ```


10. Ensure permissions

    ```sh
    sudo chmod 0644 /etc/mongodb/{r1,r2,r3}.conf
    ```


11. Create systemd units for replicas. Example for /etc/systemd/system/mongod_r1.service.

    ```sh
    [Unit]
    Description=MongoDB Database Server
    Documentation=https://docs.mongodb.org/manual
    After=network.target

    [Service]
    Type=simple
    User=mongodb
    Group=mongodb
    ExecStart=/usr/bin/mongod --config /etc/mongodb/r1.conf
    Restart=always
    PIDFile=/var/run/mongodb/mongod_r1.pid
    # file size
    LimitFSIZE=infinity
    # cpu time
    LimitCPU=infinity
    # virtual memory size
    LimitAS=infinity
    # open files
    LimitNOFILE=64000
    # processes/threads
    LimitNPROC=64000
    # locked memory
    LimitMEMLOCK=infinity
    # total threads (user+kernel)
    TasksMax=infinity
    TasksAccounting=false
    # Recommended limits for mongod as specified in
    # http://docs.mongodb.org/manual/reference/ulimit/#recommended-settings

    [Install]
    WantedBy=multi-user.target
    ```


12. Ensure permissions

    ```sh
    sudo chmod 0644 /etc/systemd/system/mongod_r{1,2,3}.service
    ```


13. Enable replica services

    ```sh
    sudo systemctl enable mongod_r1.service
    sudo systemctl enable mongod_r2.service
    sudo systemctl enable mongod_r3.service
    ```


14. Reload systemd manager configuration

    ```sh
    sudo systemctl daemon-reload
    ```


15. Start services

    ```sh
    sudo systemctl start mongod_r1.service
    sudo systemctl start mongod_r2.service
    sudo systemctl start mongod_r3.service
    ```

### Get Package ###

Clone the repository using Git.

```sh
git clone https://github.com/cessda/cessda.cdc.aggregator.doc-store.git
```

Or fetch a specific release using a tag. For example to get 0.2.0 release.

```sh
git clone --branch 0.2.0 https://github.com/cessda/cessda.cdc.aggregator.doc-store.git
```


### Install DocStore ###

It is recommended to install packages inside Python virtual
environment to isolate the install. This package also provides a
Dockerfile to help setup a containerized environment.

Create the Python virtual environment and activate it.

```sh
python3 -m venv cdcagg-env
source cdcagg-env/bin/activate
```

Install Python packages.

```sh
cd cessda.cdc.aggregator.doc-store
pip install -r requirements.txt
pip install .
```

To upgrade existing install, use ``--upgrade`` flag in pip commands. Pip
uses ``only-if-needed`` upgrade strategy by default since version
10.0.0, but for backwards compatibility the option is also included in
the example.

```sh
pip install --upgrade -r requirements.txt --upgrade-strategy=only-if-needed
pip install . --upgrade --upgrade-strategy=only-if-needed
```


### Run application database setup ###

Change ``<ip>`` to mongodb vm ip.

```sh
python -m cdcagg_docstore.db_admin --replica "<ip>:27017"  --replica "<ip>:27018" --replica "<ip>:27019" initiate_replicaset setup_database setup_collections setup_users
```


### Database setup configuration reference ###

```sh
python -m cdcagg_docstore.db_admin --help
```


## Running the server ##

Change ``<ip>`` to mongodb ip.

```sh
python -m cdcagg_docstore --replica "<ip>:27017"  --replica "<ip>:27018" --replica "<ip>:27019"
```

### Server configuration reference ###

```sh
python -m cdcagg_docstore --help
```


## License ##

See the [LICENSE](LICENSE.txt) file.
