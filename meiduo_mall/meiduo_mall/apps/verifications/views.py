from django.http import HttpResponse
from django.shortcuts import render
from django_redis import get_redis_connection
from rest_framework.views import APIView

# from meiduo_mall.meiduo_mall.utils import constants
# from meiduo_mall.meiduo_mall.utils.captcha.captcha import captcha
# TODO:了解 os.ptah
from meiduo_mall.utils import constants
from meiduo_mall.utils.captcha.captcha import captcha


class ImageCodeView(APIView):
    '''
    获取图片验证码
    '''

    def get(self, request, image_code_id):
        text, image = captcha.generate_captcha()
        redis_conn = get_redis_connection('verify_codes')
        redis_conn.setex('img_%s' % image_code_id, constants.IMAGE_CODE_REDIS_EXPIRES, text)
        return HttpResponse(content=image, content_type='image/jpg')
