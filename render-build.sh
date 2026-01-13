#!/bin/bash

# Install Node.js dependencies
npm install

pip3 install -r src/python/requirements.txt

echo "Build completed successfully!"