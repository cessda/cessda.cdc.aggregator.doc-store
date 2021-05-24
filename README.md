# CESSDA CDC Aggregator - Document Store #

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


### Install CDCAgg ###

```sh
python3 -m venv cdcagg-env
source cdcagg-env/bin/activate
cd cessda.cdc.aggregator.doc-store
pip install -r requirements.txt
pip install .
```


### Run application database setup ###

Change <ip> to mongodb vm ip.

```sh
python -m cdcagg_docstore.db_admin --replica "<ip>:27017"  --replica "<ip>:27018" --replica "<ip>:27019" initiate_replicaset setup_database setup_collections setup_users
```
