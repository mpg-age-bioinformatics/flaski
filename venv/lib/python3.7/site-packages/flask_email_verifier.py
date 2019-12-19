from os import environ
from emailverifier import Client
from emailverifier.exceptions import ApiBaseException

from flask import current_app, _app_ctx_stack

CONFIG_KEY = "EMAIL_VERIFIER_KEY"


class EmailVerifier(object):
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        api_key = app.config.get(CONFIG_KEY) or environ.get(CONFIG_KEY)
        if not api_key:
            raise Exception("""No API key was supplied for performing email verification. 
            Please set a value for EMAIL_VERIFIER_KEY.""")

        self.client = Client(api_key)

    def verify(self, email, options=None):
        try:
            data = self.client.get(email, options)
        except ApiBaseException:
            data = None

        return data
