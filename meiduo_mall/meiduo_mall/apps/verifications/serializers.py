from django_redis import get_redis_connection
from redis import RedisError
from rest_framework import serializers
import logging

logger = logging.getLogger('django')


class CheckImageCodeSerializer(serializers.Serializer):
    image_code_id = serializers.UUIDField()
    image_code = serializers.CharField(max_length=4, min_length=4)

    def validate(self, attrs):
        image_code_id = attrs['image_code_id']
        image_code = attrs['image_code']

        redis_conn = get_redis_connection('verify_codes')
        real_image_code = redis_conn.get('img_%s' % image_code_id)

        if not real_image_code:
            raise serializers.ValidationError('图片验证码无效')

        try:
            redis_conn.delete('img_%s' % image_code_id)
        except RedisError as e:
            logger.error(e)

        if real_image_code.decode().lower() != image_code.lower():
            raise serializers.ValidationError('图片验证码错误')

        # bug: 使用[]字典取值时，key不存在会报错，使用get取值时，key不存在会返回None
        mobile = self.context['view'].kwargs.get('mobile')
        if mobile:
            send_flag = redis_conn.get('send_flag_%s' % mobile)
            if send_flag:
                raise serializers.ValidationError('请求过于频繁')

        return attrs
