from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView

from users.models import User


class UserNameCountView(APIView):
    """
    用户名数量
    """

    def get(self, request, username):
        """
        检查用户名是否存在
        :param request: 请求对象
        :param username: 用户名
        :return: 用户名/用户数量
        """
        count = User.objects.filter(username=username).count()
        data = {
            'username': username,
            'count': count
        }

        return Response(data)


class MobileCountView(APIView):
    """
    手机数量
    """

    def get(self, request, mobile):
        """
        检查手机号是否存在
        :param request: 请求对象
        :param mobile: 手机号
        :return: 手机号/手机号数量
        """
        count = User.objects.filter(mobile=mobile).count()
        data = {
            'mobile': mobile,
            'count': count
        }

        return Response(data)
