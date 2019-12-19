"""
emailverifier.models.Response
~~~~~~~~~~~~~~~~~~~~~~~
Response model which represents service response like an object
"""

from json import loads
from .audit import Audit


class Response:
    json_string = ''

    def __init__(self, json):
        """
        Initialise the Response object

        :param str json: The json string with service response
        """
        self.json_string = json

        parsed = loads(json)

        self.email_address = parsed['emailAddress'] \
            if 'emailAddress' in parsed else None
        self.format_check = Response.__convert_to_bool(parsed['formatCheck']) \
            if 'formatCheck' in parsed else None
        self.smtp_check = Response.__convert_to_bool(parsed['smtpCheck']) \
            if 'smtpCheck' in parsed else None
        self.dns_check = Response.__convert_to_bool(parsed['dnsCheck']) \
            if 'dnsCheck' in parsed else None
        self.free_check = Response.__convert_to_bool(parsed['freeCheck']) \
            if 'freeCheck' in parsed else None
        self.disposable_check = Response.__convert_to_bool(parsed['disposableCheck']) \
            if 'disposableCheck' in parsed else None
        self.catch_all_check = Response.__convert_to_bool(parsed['catchAllCheck']) \
            if 'catchAllCheck' in parsed else None
        self.mx_records = parsed['mxRecords'] if 'mxRecords' in parsed else None
        self.audit = Audit(parsed['audit']) if 'audit' in parsed else None

    @staticmethod
    def __convert_to_bool(value):
        _val = str(value).lower()

        if _val == 'true':
            return True
        if _val == '1':
            return True
        if _val == 'null':
            return None

        return False

    def __str__(self):
        return self.json_string
