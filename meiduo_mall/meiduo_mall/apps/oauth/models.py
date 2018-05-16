from django.conf import settings
from django.db import models
from itsdangerous import TimedJSONWebSignatureSerializer as TJWSSerializer

from meiduo_mall.utils import constants
from meiduo_mall.utils.basemodels import BaseModel


class OauthQQUser(BaseModel):
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, verbose_name='用户')
    openid = models.CharField(max_length=64, db_index=True, verbose_name='qq_openid')

    class Meta:
        db_table = "tb_oauth_qq"
        verbose_name = "QQ登录用户信息"
        verbose_name_plural = verbose_name

    @staticmethod
    def generate_save_user_token(openid):
        """
        生成保存用户数据的token
        :param openid: 用户的openid
        :return: token
        """
        serializer = TJWSSerializer(settings.SECRET_KEY, expires_in=constants.SAVE_QQ_USER_TOKEN_EXPIRES)
        data = {'openid': openid}
        token = serializer.dumps(data)
        return token.decode()

    @staticmethod
    def check_save_user_token(token):
        """
        检验保存用户数据的token
        :param token: token
        :return: openid or None
        """
        serializer = TJWSSerializer(settings.SECRET_KEY, expires_in=constants.SAVE_QQ_USER_TOKEN_EXPIRES)
        try:
            data = serializer.loads(token)
        except BadData:
            return None
        else:
            return data.get('openid')
