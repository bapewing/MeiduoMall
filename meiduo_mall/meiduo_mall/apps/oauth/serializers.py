from django_redis import get_redis_connection
from rest_framework import serializers

from oauth.models import OauthQQUser
from users.models import User


class OauthUserSerializer(serializers.Serializer):
    access_token = serializers.CharField(label='操作凭证')
    mobile = serializers.RegexField(label='用户手机号', regex=r'^1[35789]\d{9}$')
    password = serializers.CharField(label='用户密码', min_length=8, max_length=20)
    sms_code = serializers.CharField(label='短信验证码', min_length=6, max_length=6)

    def validate(self, attrs):
        access_token = attrs.get('access_token')
        openid = OauthQQUser.check_save_user_token(access_token)
        if not openid:
            raise serializers.ValidationError('无效的access_token')
        # 方便在validated_data中使用
        attrs['openid'] = openid

        mobile = attrs['mobile']
        sms_code = attrs['sms_code']
        redis_conn = get_redis_connection('verify_codes')
        real_sms_code = redis_conn.get('sms_%s' % mobile)
        if real_sms_code.decode() != sms_code:
            raise serializers.ValidationError('验证码错误')

        try:
            user = User.objects.get(mobile=mobile)
        except User.DoesNotExist:
            pass
        else:
            password = attrs.get('password')
            if not user.check_password(password):
                raise serializers.ValidationError('密码错误')
            attrs['user'] = user

        return attrs

    def create(self, validated_data):
        user = validated_data.get('user')
        if not user:
            # 用户不存在需要注册
            # bug: 用户密码明文， 不能使用create创建
            user = User.objects.create_user(
                username=validated_data['mobile'],
                mobile=validated_data['mobile'],
                password=validated_data['password']
            )

        OauthQQUser.objects.create(
            openid=validated_data['openid'],
            user=user
        )

        return user
