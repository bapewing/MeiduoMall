import re

from django.shortcuts import render
from django_redis import get_redis_connection
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.generics import CreateAPIView, GenericAPIView, UpdateAPIView, RetrieveAPIView
from rest_framework.mixins import UpdateModelMixin, CreateModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet
from rest_framework_jwt.views import ObtainJSONWebToken

from carts.utils import merge_cart_cookie_to_redis
from goods.models import SKU
from goods.serializers import SKUSerializer
from meiduo_mall.utils import constants
from users.models import User
from users.serializers import CreateUserSerializer, CheckSMSCodeSerializer, ResetPasswordSerializer, \
    UserDetailSerializer, EmailSerializer, EmailVerificationSerializer, UserAddressSerializer, \
    UserAddressTitleSerializer, AddUserHistorySerializer
from users.utils import get_user_by_account
from verifications.serializers import CheckImageCodeSerializer


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


class RegisterUserView(CreateAPIView):
    """
    用户注册
    """
    serializer_class = CreateUserSerializer


class SMSCodeTokenView(GenericAPIView):
    """
    找回密码第一步验证
    """
    serializer_class = CheckImageCodeSerializer

    def get(self, request, account):
        """
        获取用户账号发送短信token
        :param request: 请求对象
        :param account: 用户名或手机号
        :return: 格式化手机号/access_token
        """
        serializer = self.get_serializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        user = get_user_by_account(account)
        if not user:
            return Response({'message': '用户不存在'}, status=status.HTTP_404_NOT_FOUND)

        access_token = user.generate_send_sms_token()
        # 正则sub分组替换 https://blog.csdn.net/hzliyaya/article/details/52495150
        mobile = re.sub(r'(\d{3})\d{4}(\d{4})', r'\1****\2', user.mobile)

        return Response({
            'mobile': mobile,
            'access_token': access_token
        })


class PasswordTokenView(GenericAPIView):
    """
    找回密码第二步验证
    """
    serializer_class = CheckSMSCodeSerializer

    def get(self, request, account):
        """
        获取用户账号修改密码的token
        :param request: 请求对象
        :param account: 用户名或是密码
        :return: user_id/access_token
        """
        serializer = self.get_serializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        user = serializer.user
        access_token = user.generate_set_password_token()

        return Response({'user_id': user.id, 'access_token': access_token})


# 不能继承UpdateAPIView吗？
# 可以继承自UpdateAPIView 只需要修改js中请求方法为put就行
class PasswordView(UpdateModelMixin, GenericAPIView):
    """
    重置用户密码
    """
    queryset = User.objects.all()
    serializer_class = ResetPasswordSerializer

    def post(self, request, pk):
        return self.update(request, pk)


class UserDetailView(RetrieveAPIView):
    """
    用户详细信息
    """
    serializer_class = UserDetailSerializer
    # TODO: django认证系统文档
    permission_classes = [IsAuthenticated]

    # RetrieveAPIView只能自动处理url中包含pk的请求 /user/pk/
    # 现在的请求路由是 /user/ 所以需要重写get_object方法获取当前用户
    # 基于django的认证系统，request请求中存储有当前登录的用户
    # 前端请求时需要在headers中加入jwt token
    def get_object(self):
        return self.request.user


class EmailView(UpdateAPIView):
    # queryset = User.objects.all()
    serializer_class = EmailSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    # TODO:使用下面这种方法时，必须定义query_set ?
    # 使用下面这种方法时，必须定义query_set? 如果继承自CreateAPIView就不需要query_set
    # 因为update操作最后会调用get_object方法，get_object方法内部需要在数据库中查询要更新的对象
    # 所以如果不用重写get_object的方式，必须要定义查询集，确保视图能够查询到要更新的对象
    # def get_serializer(self, *args, **kwargs):
    #     return EmailSerializer(self.request.user, data=self.request.data)


# 可以使用UpdateAPIView吗？PK怎么办？能够从request.user中获取用户吗？是不是需要前端传送jwt token？应该没有jwt token
# 不可以使用UpdateAPIView，因为获取不到pk。不能从request.user中获取用户，此时也没有jwt token可以传送给后端。
class EmailVerificationView(CreateModelMixin, GenericAPIView):
    serializer_class = EmailVerificationSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        return self.create(request)


class AddressViewSet(CreateModelMixin, UpdateModelMixin, GenericViewSet):
    """
    用户地址新增与修改
    """
    serializer_class = UserAddressSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.request.user.addresses.filter(is_deleted=False)

    def create(self, request, *args, **kwargs):
        count = request.user.addresses.count()
        if count > constants.USER_ADDRESS_COUNT_LIMIT:
            return Response({'message': '保存地址数据已经达到上限'}, status=status.HTTP_400_BAD_REQUEST)

        return super().create(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = UserAddressSerializer(queryset, many=True)
        user = self.request.user
        return Response({
            'user_id': user.id,
            'default_address_id': user.default_address_id,
            'limit': constants.USER_ADDRESS_COUNT_LIMIT,
            'addresses': serializer.data,
        })

    def destroy(self, request, *args, **kwargs):
        address = self.get_object()
        address.is_deleted = True
        address.save()

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['PUT'], detail=True)
    def status(self, request, pk=None, address_id=None):
        address = self.get_object()
        request.user.default_address = address
        request.user.save()

        return Response({'message': 'OK'}, status=status.HTTP_200_OK)

    @action(methods=['PUT'], detail=True)
    def title(self, request, pk=None, address_id=None):
        address = self.get_object()
        serializer = UserAddressTitleSerializer(address, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)


class UserHistoryView(CreateModelMixin, GenericAPIView):
    """用户历史记录"""
    # jwt_token 过期时会有401错误，不能添加用户历史浏览记录，不能算是bug
    permission_classes = [IsAuthenticated]
    serializer_class = AddUserHistorySerializer

    def post(self, request):
        """保存"""
        return self.create(request)

    def get(self, request):
        user_id = request.user.id
        # 查询redis数据库
        redis_conn = get_redis_connection('history')
        sku_id_list = redis_conn.lrange('history_%s' % user_id, 0, constants.USER_BROWSING_HISTORY_COUNTS_LIMIT)

        # 根据redis返回的sku id 查询数据
        # SKU.objects.filter(id__in=sku_id_list)
        sku_list = []
        for sku_id in sku_id_list:
            sku = SKU.objects.get(id=sku_id)
            sku_list.append(sku)

        # 使用序列化器序列化
        # 如果要被序列化的是包含多条数据的查询集QuerySet，可以通过添加many=True参数补充说明
        serializer = SKUSerializer(sku_list, many=True)
        return Response(serializer.data)


class UserAuthorizeView(ObtainJSONWebToken):
    """
    用户认证
    """

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data.get('user')
            response = merge_cart_cookie_to_redis(request, user, response)

        return response
