from random import randint

from django.http import HttpResponse
from django.shortcuts import render
from django_redis import get_redis_connection
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

# TODO:了解 os.ptah
from meiduo_mall.utils import constants
from meiduo_mall.utils.captcha.captcha import captcha
from users.models import User
from verifications.serializers import CheckImageCodeSerializer


class ImageCodeView(APIView):
    """
    图片验证码
    """

    def get(self, request, image_code_id):
        """
        获取图片验证码
        :param request: 请求对象
        :param image_code_id: uuid随机值
        :return: image图片
        """
        text, image = captcha.generate_captcha()
        redis_conn = get_redis_connection('verify_codes')
        redis_conn.setex('img_%s' % image_code_id, constants.IMAGE_CODE_REDIS_EXPIRES, text)
        return HttpResponse(content=image, content_type='image/jpg', status=status.HTTP_200_OK)


class SMSCodeView(GenericAPIView):
    """
    短信验证码
    """
    serializer_class = CheckImageCodeSerializer

    def get(self, request, mobile):
        """
        发送短信验证码
        :param request: 请求对象
        :param mobile:  手机号
        :return: message消息
        """
        serializer = self.get_serializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        sms_code = str('%06d' % randint(0, 999999))
        print('sms_code:%s' % sms_code)

        redis_conn = get_redis_connection('verify_codes')
        pl = redis_conn.pipeline()
        # TODO:这是做什么用的？
        pl.multi()
        # 解决:验证码不是发送成功才往redis存吗？==>同步耗时任务，用户体验差
        pl.setex('sms_%s' % mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
        pl.setex('send_flag_%s' % mobile, constants.SMS_CODE_REDIS_INTERVAL, 1)
        pl.execute()

        # send_sms_code.delay(mobile, sms_code)

        return Response({'message': '发送成功'})


class SMSCodeByTokenView(APIView):
    """
    根据access_token发送短信
    """

    def get(self, request):
        """
        获取access_token生成的短信验证码
        :param request: 请求对象
        :return: message
        """
        access_token = request.query_params.get('access_token')
        if not access_token:
            return Response({'message': '缺少access_token'}, status=status.HTTP_400_BAD_REQUEST)

        mobile = User.check_send_sms_token(access_token)
        if not mobile:
            return Response({'message': '无效的access_token'}, status=status.HTTP_400_BAD_REQUEST)

        redis_conn = get_redis_connection('verify_codes')
        send_flag = redis_conn.get('send_flag_%s' % mobile)
        if send_flag:
            raise Response({"message": "发送短信次数过于频"}, status=status.HTTP_429_TOO_MANY_REQUESTS)

        sms_code = str('%06d' % randint(0, 999999))
        print('sms_code:%s' % sms_code)

        redis_conn = get_redis_connection('verify_codes')
        pl = redis_conn.pipeline()
        # TODO:这是做什么用的？
        pl.multi()
        # 解决:验证码不是发送成功才往redis存吗？==>同步耗时任务，用户体验差
        pl.setex('sms_%s' % mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
        pl.setex('send_flag_%s' % mobile, constants.SMS_CODE_REDIS_INTERVAL, 1)
        pl.execute()

        # send_sms_code.delay(mobile, sms_code)

        return Response({'message': '发送成功'}, status=status.HTTP_200_OK)