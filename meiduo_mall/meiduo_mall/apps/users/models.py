from django.contrib.auth.models import AbstractUser
from django.db import models
from itsdangerous import TimedJSONWebSignatureSerializer as TJWSSerializer, BadData
from django.conf import settings

from meiduo_mall.utils import constants


class User(AbstractUser):
    """
    用户信息
    """

    mobile = models.CharField(max_length=11, unique=True, verbose_name='手机号')

    class Meta:
        db_table = "tb_users"
        verbose_name = "用户信息"
        verbose_name_plural = verbose_name

    def generate_send_sms_token(self):
        """
        生成发送短信验证码的access_token
        :return: access_token
        """
        serializer = TJWSSerializer(settings.SECRET_KEY, constants.SMS_CODE_REDIS_EXPIRES)
        access_token = serializer.dumps({
            'mobile': self.mobile
        }).decode()

        return access_token

    @staticmethod
    def check_send_sms_token(access_token):
        """
        检验access_token
        :param access_token: 验证第一步产生的access_token
        :return: mobile
        """
        serialier = TJWSSerializer(settings.SECRET_KEY, constants.SEND_SMS_CODE_TOKEN_EXIPIRES)
        try:
            data = serialier.loads(access_token)
        except BadData:
            return None
        else:
            mobile = data.get('mobile')
            return mobile

    def generate_set_password_token(self):
        """
        生成重置密码的access_token
        :return: access_token
        """
        serializer = TJWSSerializer(settings.SECRET_KEY, constants.SMS_CODE_REDIS_EXPIRES)
        access_token = serializer.dumps({
            'user_id': self.id
        }).decode()
        return access_token
