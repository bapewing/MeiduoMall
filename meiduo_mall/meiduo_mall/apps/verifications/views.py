from random import randint

from django.http import HttpResponse
from django.shortcuts import render
from django_redis import get_redis_connection
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

# TODO:了解 os.ptah
from meiduo_mall.libs.yuntongxun.sms import CCP
from meiduo_mall.utils import constants
from meiduo_mall.utils.captcha.captcha import captcha
from verifications.serializers import CheckImageCodeSerializer


class ImageCodeView(APIView):
    '''
    获取图片验证码
    '''

    def get(self, request, image_code_id):
        text, image = captcha.generate_captcha()
        redis_conn = get_redis_connection('verify_codes')
        redis_conn.setex('img_%s' % image_code_id, constants.IMAGE_CODE_REDIS_EXPIRES, text)
        return HttpResponse(content=image, content_type='image/jpg')


class SMSCodeView(GenericAPIView):
    serializer_class = CheckImageCodeSerializer

    def get(self, request, mobile):
        serializer = self.get_serializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        sms_code = str(randint(0, 999999))
        print('sms_code:%s' % sms_code)

        redis_conn = get_redis_connection('verify_codes')
        pl = redis_conn.pipeline()
        # TODO:这是做什么用的？
        pl.multi()
        # TODO:验证码不是发送成功才往redis存吗？
        pl.setex('sms_%s' % mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
        pl.setex('send_flag_%s' % mobile, constants.SMS_CODE_REDIS_INTERVAL, 1)
        pl.execute()

        # result = CCP().send_template_sms(mobile, [sms_code, int(constants.SMS_CODE_REDIS_EXPIRES / 60)],
        #
        #                                  constants.SMS_CODE_TEMPLATE_ID)
        # # TODO:发送失败的状态码？
        # if result != 0:
        #     return Response({'message': '发送失败'}, status=404)
        return Response({'message': '发送成功'})
