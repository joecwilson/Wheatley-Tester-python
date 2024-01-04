#!/bin/bash

black src
isort src
ruff src
mypy src 
