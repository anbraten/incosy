#! /bin/bash

pip install -r requirements.txt
flask --app app run --host=0.0.0.0 --debug
