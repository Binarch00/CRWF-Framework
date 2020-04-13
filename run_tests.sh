#!/bin/bash

echo 'flush cache'
redis-cli flushall
echo 'init models'
PYTHONPATH=./ python database/models.py
echo 'btc-address gen'
PYTHONPATH=./ python services/btc_address_generator.py
echo 'start tests'
PYTHONPATH=./ python -m unittest
