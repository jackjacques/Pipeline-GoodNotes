#!/bin/bash
# Wrapper script for Miniconda Python execution
unset PYTHONHOME
unset PYTHONPATH
export PATH="/Users/jacques/miniconda3/bin:/usr/local/bin:/usr/bin:/bin"

exec /Users/jacques/miniconda3/bin/python3 -u "$@"
