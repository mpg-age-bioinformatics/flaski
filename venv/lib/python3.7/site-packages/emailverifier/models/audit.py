"""
emailverifier.models.Audit
~~~~~~~~~~~~~~~~~~~~~~~
This model represents an audit object in service response
"""

from dateutil.parser import parse


class Audit:

    def __init__(self, data):
        """
        Initialise the Response object

        :param dict data: Dictionary with 2 keys - 'auditCreatedDate' and
            'auditUpdatedDate'
        """

        self.audit_created_date = parse(data['auditCreatedDate']) \
            if 'auditCreatedDate' in data and len(data['auditCreatedDate']) > 1 else None
        self.audit_updated_date = parse(data['auditUpdatedDate']) \
            if 'auditUpdatedDate' in data and len(data['auditUpdatedDate']) > 1 else None
