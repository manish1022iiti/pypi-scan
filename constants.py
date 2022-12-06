"""
Constants

This file consolidates all constants into one module.
"""

# Total Number of top packages as per our popularity definition
NUM_POPULAR_PACKAGES = 5000

# Number of top packages on pypi to scan
TOP_N = 50

# Edit distance threshold to determine typosquatting status; if 0, code uses dynamic
# distance based on the length of the package name under consideration
MAX_DISTANCE = 0

# Minimum length of package name to be included for analysis
MIN_LEN_PACKAGE_NAME = 5
