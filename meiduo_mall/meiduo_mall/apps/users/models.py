from django.contrib.auth.models import AbstractUser
from django.db import models
from itsdangerous import TimedJSONWebSignatureSerializer as TJWSSerializer
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
        access_token = serializer.dumps(
            {
                'mobile': self.mobile
            }
        ).decode()

        return access_token
