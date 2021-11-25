#!/bin/sh

curl -X POST "https://validator.swagger.io/validator/debug" -H  "accept: application/yaml" -H  "Content-Type: application/json" -d @openapi.json
