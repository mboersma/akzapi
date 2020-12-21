#!/usr/bin/env bash
#-------------------------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See https://go.microsoft.com/fwlink/?linkid=2090316 for license information.
#-------------------------------------------------------------------------------------------------------------
#
# Syntax: ./azdev-setup.sh

set -euo pipefail

python3 -m venv env
. ./env/bin/activate
pip3 install --disable-pip-version-check --no-cache-dir --verbose azdev
azdev setup --repo . --ext capi
