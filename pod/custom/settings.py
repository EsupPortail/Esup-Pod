import os
##
# Project folder
#
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(PROJECT_DIR, 'static')
