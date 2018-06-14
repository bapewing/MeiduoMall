import json
import logging
from urllib.parse import urlencode, parse_qs
from urllib.request import urlopen

from django.conf import settings

from oauth.exceptions import QQAPIException

logger = logging.getLogger('django')


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
        """
        生成访问qq的拼接路径
        :return:
        """
        parameters = {
            'response_type': 'code',
            'client_id': self.app_id,
            'redirect_uri': self.redirect_uri,
            'state': self.state,
            'scope': 'get_user_info',
        }

        return 'https://graph.qq.com/oauth2.0/authorize?' + urlencode(parameters)

    def get_access_token(self, code):
        """
        获取QQ的access_token
        :param code: 重定向域路径中code
        :return: access_token
        """
        parameters = {
            'grant_type': 'authorization_code',
            'client_id': self.app_id,
            'client_secret': self.app_key,
            'code': code,
            'redirect_uri': self.redirect_uri
        }

        url = 'https://graph.qq.com/oauth2.0/token?' + urlencode(parameters)
        # access_token=FE04************************CCE2&expires_in=7776000&refresh_token=88E4************************BE14
        try:
            response = urlopen(url).read().decode()
            response_dict = parse_qs(response)
            access_token = response_dict.get("access_token")[0]
        except Exception as e:
            logger.error(e)
            raise QQAPIException('获取access_token异常')

        return access_token

    def get_openid(self, access_token):
        """
        获取QQ用户的openid
        :param access_token: 服务器获取的access_token
        :return: openid
        """
        url = 'https://graph.qq.com/oauth2.0/me?access_token=' + access_token
        # callback( {"client_id":"YOUR_APPID","openid":"YOUR_OPENID"} );
        try:
            response = urlopen(url).read().decode()
            # 切片是最便捷的获取openid的形式
            response_dict = json.loads(response[10:-4])
        except Exception as e:
            logger.error(e)
            raise QQAPIException('获取openid异常')

        return response_dict.get('openid')
