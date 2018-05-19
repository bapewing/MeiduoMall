from django.contrib.auth.models import AbstractUser
from django.db import models
from itsdangerous import TimedJSONWebSignatureSerializer as TJWSSerializer, BadData
from django.conf import settings

from meiduo_mall.utils import constants
from meiduo_mall.utils.basemodels import BaseModel


class User(AbstractUser):
    """
    用户信息
    """

    mobile = models.CharField(max_length=11, unique=True, verbose_name='手机号')
    email_active = models.BooleanField(default=False, verbose_name='邮箱验证状态')
    default_address = models.ForeignKey('Address', related_name='users', null=True, blank=True,
                                        on_delete=models.SET_NULL, verbose_name='默认地址')

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

    @staticmethod
    def check_set_password_token(access_token, user_id):
        """
        检验设置密码的token
        """
        serializer = TJWSSerializer(settings.SECRET_KEY, expires_in=constants.SET_PASSWORD_TOKEN_EXPIRES)
        try:
            data = serializer.loads(access_token)
        except BadData:
            return False
        else:
            if user_id != str(data.get('user_id')):
                return False
            else:
                return True

    def generate_verify_url(self):

        serializer = TJWSSerializer(settings.SECRET_KEY, expires_in=constants.EMAIL_VERIFY_TOKEN_EXPIRES)
        data = {
            'user_id': self.id,
            'email': self.email
        }

        access_token = serializer.dumps(data).decode()
        verify_url = 'http://www.meiduo.site:8080/success_verify_email.html?token=' + access_token

        return verify_url

    @staticmethod
    def check_email_verification_token(access_token):
        serializer = TJWSSerializer(settings.SECRET_KEY, expires_in=constants.EMAIL_VERIFY_TOKEN_EXPIRES)
        try:
            data = serializer.loads(access_token)
        except BadData:
            return False
        else:
            email = data.get('email')
            user_id = data.get('user_id')
            try:
                user = User.objects.filter(id=user_id, email=email).first()
            except User.DoesNotExist:
                return None
            else:
                return user


class Address(BaseModel):
    """
    用户地址
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses', verbose_name='用户')
    title = models.CharField(max_length=20, verbose_name='地址名称')
    receiver = models.CharField(max_length=20, verbose_name='收货人')
    province = models.ForeignKey('areas.Area', on_delete=models.PROTECT, related_name='province_addresses',
                                 verbose_name='省')
    city = models.ForeignKey('areas.Area', on_delete=models.PROTECT, related_name='city_addresses', verbose_name='市')
    district = models.ForeignKey('areas.Area', on_delete=models.PROTECT, related_name='district_addresses',
                                 verbose_name='区')
    place = models.CharField(max_length=50, verbose_name='地址')
    mobile = models.CharField(max_length=11, verbose_name='手机')
    tel = models.CharField(max_length=20, null=True, blank=True, default='', verbose_name='固定电话')
    email = models.CharField(max_length=30, null=True, blank=True, default='', verbose_name='电子邮箱')
    is_deleted = models.BooleanField(default=False, verbose_name='逻辑删除')

    class Meta:
        db_table = 'tb_address'
        verbose_name = '用户地址'
        verbose_name_plural = verbose_name
        ordering = ['-update_time']
