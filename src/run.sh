#! /bin/bash

pip install -r requirements.txt
pip list -v
flask --app app run --host=0.0.0.0
