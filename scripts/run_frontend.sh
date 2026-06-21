#!/bin/bash
cd "$(dirname "$0")/.."
python -m http.server 3000 --directory frontend
