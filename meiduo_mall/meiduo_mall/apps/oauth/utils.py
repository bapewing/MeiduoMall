from urllib.parse import urlencode

from django.conf import settings


class OauthQQ(object):
    """
    QQ认证工具类
    """
    def __init__(self, app_id=None, app_key=None, redirect_uri=None, state=None):
        self.app_id = app_id or settings.QQ_APP_ID
        self.app_key = app_key or settings.QQ_APP_KEY
        self.redirect_uri = redirect_uri or settings.QQ_REDIRECT_URI
        self.state = state or settings.QQ_STATE

    def get_auth_url(self):

        parameters = {
            'response_type': 'code',
            'client_id': self.app_id,
            'redirect_uri': self.redirect_uri,
            'state': self.state,
            'scope': 'get_user_info',
        }

        return 'https://graph.qq.com/oauth2.0/authorize?' + urlencode(parameters)