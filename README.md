# Cryto Ready Web Framework (CRWF)

## Core features
* Ready to accept crypto payments for users.
* Minimal maintenance.
* Easy scalable.
* User ready with login, register, account activation by email, password forgot and password reset.
* Recaptcha v2 protected forms.
* Basic app abuse control at IP level for register, password forgot and maximum requests.

The minimal maintenance is achieved by using as python core immutable features as possible.

---
##### Requirements
* Python3.7 or greater
* Crypto IPN service https://github.com/Binarch00/crypto_gateway

Abuse control by IP could end using proxy IP if proxies are used. 

---

##### Python libs setup
Python 3.7 or greater required
```shell script
python3.7 -m venv venv
. ./venv/bim/activate
pip install -r requirements.txt
```

##### For setup the initial database
`PYTHONPATH=./ python database/models.py`

##### For run unittests 
`./run_tests.sh`

##### Run the web app

`PYTHONPATH=./ python webapp/run.py`

---
Internal Services
---

#### Crypto Wallets Generator (Required Service)

For security reasons, the users wallets are generated outside the users register process.
This way the web app will never know how decode the wallets private keys.

##### Before the webapp consume all unused address, call the address generator by 
`PYTHONPATH=./ python services/btc_address_generator.py`

Security Details:
* Run the service outside the webapp server
* Setup secure remote database access to web app database
* Remove all decryption keys at web app deploy.

---

How To Deploy
---

#### TODO !

.