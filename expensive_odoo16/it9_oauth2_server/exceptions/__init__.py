import json


class AuthenticateException(Exception):
    def __init__(self, error, error_description, status):
        self.error = error
        self.error_description = error_description
        self.error_uri = 'See the full API docs at https://authorization-server.com/docs/access_token'
        self.status = status

    def __str__(self, *args, **kwargs):
        return json.dumps({
            'error': self.error,
            'error_description': self.error_description,
            'error_uri': self.error_uri
        })
