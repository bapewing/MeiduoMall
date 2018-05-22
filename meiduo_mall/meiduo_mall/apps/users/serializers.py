import re

from django_redis import get_redis_connection
from rest_framework import serializers
from rest_framework_jwt.settings import api_settings

from celery_tasks.emails.tasks import send_verify_email
from goods.models import SKU
from meiduo_mall.utils import constants
from users.models import User, Address
from users.utils import get_user_by_account


class CreateUserSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(label='确认密码', write_only=True)
    sms_code = serializers.CharField(label='短信验证码', write_only=True)
    allow = serializers.CharField(label='同意协议', write_only=True)
    token = serializers.CharField(label='登录状态token', read_only=True)

    def validate_mobile(self, value):
        if not re.match(r'^1[35789]\d{9}$', value):
            raise serializers.ValidationError('手机格式错误')
        return value

    def validate_allow(self, value):
        if value != 'true':
            raise serializers.ValidationError('请同意用户协议')
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError('两次密码不一致')

        redis_conn = get_redis_connection('verify_codes')
        mobile = attrs['mobile']
        real_sms_code = redis_conn.get('sms_%s' % mobile)
        if not real_sms_code:
            raise serializers.ValidationError('无效的短信验证码')
        if real_sms_code.decode() != attrs['sms_code']:
            raise serializers.ValidationError('短信验证码错误')

        return attrs

    def create(self, validated_data):
        del validated_data['password2']
        del validated_data['sms_code']
        del validated_data['allow']
        user = super().create(validated_data)

        user.set_password(validated_data['password'])
        user.save()

        # 补充生成记录登录状态的token
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)
        user.token = token

        return user

    class Meta:
        model = User
        fields = ('id', 'username', 'password', 'password2', 'sms_code', 'mobile', 'allow', 'token')
        extra_kwargs = {
            'id': {'read_only': True},
            'username': {
                'min_length': 5,
                'max_length': 20,
                'error_messages': {
                    'min_length': '仅允许5-20个字符的用户名',
                    'max_length': '仅允许5-20个字符的用户名',
                }
            },
            'password': {
                'write_only': True,
                'min_length': 8,
                'max_length': 20,
                'error_messages': {
                    'min_length': '仅允许5-20个字符的密码',
                    'max_length': '仅允许5-20个字符的密码',
                }
            }
        }


class CheckSMSCodeSerializer(serializers.Serializer):
    sms_code = serializers.CharField(min_length=6, max_length=6)

    def validate_sms_code(self, value):
        # bug:get[] TypeError: 'builtin_function_or_method' object is not subscriptable
        account = self.context['view'].kwargs.get('account')
        user = get_user_by_account(account)
        if not user:
            raise serializers.ValidationError('用户不存在')

        # TODO: 用户保存到序列化器
        self.user = user

        redis_conn = get_redis_connection('verify_codes')
        real_sms_code = redis_conn.get('sms_%s' % user.mobile)
        if not real_sms_code:
            raise serializers.ValidationError('无效短信验证码')
        if value != real_sms_code.decode():
            raise serializers.ValidationError('短信验证码错误')
        return value


class ResetPasswordSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(label='确认密码', write_only=True)
    access_token = serializers.CharField(label='密码token', write_only=True)

    def validate(self, attrs):
        """
        校验数据
        """
        # 判断两次密码
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError('两次密码不一致')

        # 需要对比 access token中的userid 与请求用户的id是否一致
        allow = User.check_set_password_token(attrs['access_token'], self.context['view'].kwargs['pk'])
        if not allow:
            raise serializers.ValidationError('无效的access token')

        return attrs

    def update(self, instance, validated_data):
        """
        更新密码
        :param instance: User对象
        :param validated_data: 校验后的字典
        :return: User对象
        """
        instance.set_password(validated_data['password'])
        instance.save()
        return instance

    class Meta:
        model = User
        fields = ('id', 'password', 'password2', 'access_token')
        extra_kwargs = {
            'password': {
                'write_only': True,
                'min_length': 8,
                'max_length': 20,
                'error_messages': {
                    'min_length': '仅允许8-20个字符的密码',
                    'max_length': '仅允许8-20个字符的密码',
                }
            }
        }


class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'mobile', 'email', 'email_active')


class EmailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email')
        extra_kwargs = {
            'email': {
                'required': True
            }
        }

    def update(self, instance, validated_data):
        instance.email = validated_data.get('email')
        instance.save()

        verify_url = instance.generate_verify_url()
        send_verify_email.delay(instance.email, verify_url)

        return instance


class EmailVerificationSerializer(serializers.ModelSerializer):
    token = serializers.CharField(label='邮件token', read_only=True)

    def validate(self, attrs):
        # TODO: 为什么需要以这种方式获取token呢？？？
        access_token = self.context.get('request').query_params.get('token')
        if not access_token:
            return serializers.ValidationError('缺少access_token')

        # TODO： 如果check直接返回已经更新的model，那根本就不需要使用create方法了
        user = User.check_email_verification_token(access_token)
        if not user:
            return serializers.ValidationError('链接无效')
        attrs['user'] = user

        return attrs

    def create(self, validated_data):
        user = validated_data.get('user')
        user.email_active = True
        user.save()
        return user

    class Meta:
        model = User
        fields = ('id', 'token')
        extra_kwargs = {
            'token': {
                'required': True
            }
        }


class UserAddressSerializer(serializers.ModelSerializer):
    province = serializers.StringRelatedField(read_only=True)
    city = serializers.StringRelatedField(read_only=True)
    district = serializers.StringRelatedField(read_only=True)
    province_id = serializers.IntegerField(label='省id', required=True)
    city_id = serializers.IntegerField(label='市id', required=True)
    district_id = serializers.IntegerField(label='区id', required=True)
    mobile = serializers.RegexField(label='手机号', regex=r'^1[35789]\d{9}$')

    class Meta:
        model = Address
        exclude = ('user', 'is_deleted', 'create_time', 'update_time')

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class UserAddressTitleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ('title',)


class AddUserHistorySerializer(serializers.Serializer):
    sku_id = serializers.IntegerField(min_value=1)

    def validate_sku_id(self, value):
        try:
            SKU.objects.get(id=value)
        except SKU.DoesNotExist:
            raise serializers.ValidationError("sku id 不存在")
        return value

    def create(self, validated_data):
        """保存"""
        # user_id
        user_id = self.context['request'].user.id
        sku_id = validated_data['sku_id']

        # 保存记录到redis中
        redis_conn = get_redis_connection('history')

        pl = redis_conn.pipeline()

        # 清除sku_id在redis中的记录
        # lrem(name, count, value)
        pl.lrem('history_%s' % user_id, 0, sku_id)

        # 向redis追加数据
        # lpush  [1,2,3,4] 5   -> [5,1,2,3,4]
        pl.lpush('history_%s' % user_id, sku_id)

        # 如果超过数量，截断
        # ltrim(name, start, end)
        pl.ltrim('history_%s' % user_id, 0, constants.USER_BROWSING_HISTORY_COUNTS_LIMIT-1)

        pl.execute()

        return validated_data
