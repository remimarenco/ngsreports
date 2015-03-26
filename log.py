#!/usr/bin/env python
# encoding: utf-8
"""
log.py

Created by Anne Pajon on 2015-03-26.
"""

import logging
import logging.config

HOST = 'smtp.cruk.cam.ac.uk'
FROM = 'anne.pajon@cruk.cam.ac.uk'
TO = 'anne.pajon@cruk.cam.ac.uk'
SUBJECT = 'New Error From GLSREPORTS'

# logging definition
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'verbose': {
            'format': '%(asctime)s %(name)-24s %(levelname)-8s: %(message)s'
        },
        'simple': {
            'format': '%(name)-24s %(levelname)-8s: %(message)s'
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'info_file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'info.log',
            'maxBytes': '1024*1024*5',
            'backupCount': '10',
            'formatter': 'verbose',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'errors.log',
            'maxBytes': '1024*1024*5',
            'backupCount': '10',
            'formatter': 'verbose',
        },
        'email': {
            'level': 'ERROR',
            'class': 'logging.handlers.SMTPHandler',
            'mailhost': HOST,
            'fromaddr': FROM,
            'toaddrs': [TO],
            'subject': SUBJECT,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'glsreports': {
            'handlers': ['console', 'info_file', 'error_file'],
            'propagate': True,
            'level': 'DEBUG',
        },
    }
}


def get_custom_logger(logfile=None, noemail=False):
    if logfile:
        LOGGING['handlers']['info_file']['filename'] = logfile
        LOGGING['handlers']['error_file']['filename'] = logfile + ".errors"
    if not noemail:
        LOGGING['loggers']['glsreports']['handlers'].append('email')
    logging.config.dictConfig(LOGGING)
    return logging.getLogger('glsreports')