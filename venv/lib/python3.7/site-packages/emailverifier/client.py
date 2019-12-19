"""
emailverifier.Client
~~~~~~~~~~~~~~~~~~~~~
Implementation of Email Verification API client in Python
"""

from emailverifier.version import __version__
import requests
import requests.exceptions
from emailverifier import exceptions
from emailverifier import models


class Client:
    __url = 'https://emailverification.whoisxmlapi.com/api/v1'
    __ua = 'Python library/' + __version__

    def __init__(self, api_key=None, url=None):
        """
        Initialise the Client object

        :param str api_key: User's API key
        :param url: Endpoint URL
        """
        self.api_key = api_key,
        self.url = self.__url if url is None else url

    def get(self, email, options=None):
        """
        Verify an email address

        :param str email: email address
        :param dict options: Input parameters are described here
            https://emailverification.whoisxmlapi.com/docs
        :return: returns object of emailverifier.models.Response
        """
        if self.api_key is None:
            raise exceptions.UndefinedVariableException('The API key is not set')

        args = {'emailAddress': email, 'apiKey': self.api_key,
                'outputFormat': 'json'}

        if options is not None:
            if not isinstance(options, dict):
                raise exceptions.InvalidArgumentException('Options should be a dict')

            if 'outputFormat' in options:
                options['outputFormat'] = 'json'

            args = Client.merge_two_dicts(args, options)

        return models.Response(self.__verify(args))

    def get_raw(self, email, output_format='json', options=None):
        """
        Verify an email address

        :param str email: email address
        :param str output_format: response format (json, xml)
        :param dict options: Input parameters are described here
            https://emailverification.whoisxmlapi.com/docs
        :return: server response as a string
        """
        if self.api_key is None:
            raise exceptions.UndefinedVariableException('API key is not set')

        args = {'emailAddress': email, 'apiKey': self.api_key,
                'outputFormat': output_format}

        if options is not None:
            if not isinstance(options, dict):
                raise exceptions.InvalidArgumentException('Options should be a dict')

            if 'outputFormat' in options:
                options['outputFormat'] = output_format

            args = Client.merge_two_dicts(args, options)

        return self.__verify(args)

    def __verify(self, params):
        try:
            response = requests.get(self.url, params=params,
                                    headers={'User-Agent': self.__ua})
        except requests.exceptions.RequestException as err:
            raise exceptions.GeneralException(err.__str__())

        code = response.status_code

        if code < 200 or code >= 300:
            raise exceptions.HttpException(code, 'Error: ' + response.text)

        return response.text

    def set_api_key(self, api_key):
        """
        Setter for the API key

        :param str api_key:
        """

        if not isinstance(api_key, str):
            raise exceptions.InvalidArgumentException('The API key should be a string')

        self.api_key = api_key

    def set_url(self, url):
        """
        Setter for the endpoint URL

        :param str url:
        """
        if not isinstance(url, str):
            raise exceptions.InvalidArgumentException('Url should be a string')

        self.url = url

    @staticmethod
    def merge_two_dicts(x, y):
        z = x.copy()
        z.update(y)
        return z
