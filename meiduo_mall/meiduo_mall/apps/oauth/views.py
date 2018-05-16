from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView

from oauth.utils import OauthQQ


class OauthQQUrlView(APIView):
    """
    生成登录QQ的URL
    """
    def get(self, request):
        """
        拼接QQ登录需要的url路径
        :param request: 请求对象
        :return: url
        """
        # 登录成功跳转页面需要使用state=next
        state = request.query_params.get('state', '/')
        oauth = OauthQQ(state=state)
        oauth_url = oauth.get_auth_url()
        return Response({'oauth_url': oauth_url})
