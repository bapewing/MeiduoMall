from django.shortcuts import render
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_jwt.settings import api_settings

from carts.utils import merge_cart_cookie_to_redis
from oauth.exceptions import QQAPIException
from oauth.models import OauthQQUser
from oauth.serializers import OauthUserSerializer
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


class OauthQQUserView(GenericAPIView):
    serializer_class = OauthUserSerializer

    def get(self, request):
        code = request.query_params.get('code')
        if not code:
            return Response({'message': '缺少code'}, status=status.HTTP_400_BAD_REQUEST)

        oauth = OauthQQ()

        try:
            access_token = oauth.get_access_token(code)
            open_id = oauth.get_openid(access_token)
        except QQAPIException:
            return Response({'message': '获取QQ用户数据异常'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        # 根据openid查询用户之前是否绑定
        try:
            oauth_user = OauthQQUser.objects.get(openid=open_id)
        except OauthQQUser.DoesNotExist:
            # 第一次使用QQ登录
            access_token = OauthQQUser.generate_save_user_token(open_id)
            return Response({'access_token': access_token})
        else:
            # 非第一次使用QQ登录
            user = oauth_user.user
            jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
            jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
            payload = jwt_payload_handler(user)
            token = jwt_encode_handler(payload)
            # 前端通过返回数据是否有user_id而判断是注册用户还是关联用户
            response = Response({
                'token': token,
                'username': user.username,
                'user_id': user.id
            })
            response = merge_cart_cookie_to_redis(request, user, response)

            return response

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # 生成已登录的token
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)

        response = Response({
            'token': token,
            'username': user.username,
            'user_id': user.id
        })
        response = merge_cart_cookie_to_redis(request, user, response)

        return response

