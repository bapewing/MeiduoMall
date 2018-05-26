import base64
import pickle
from django.shortcuts import render
from django_redis import get_redis_connection
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from carts.serializers import CartSerializer, CartSKUSerializer
from goods.models import SKU


class CartView(APIView):

    # TODO:了解下重写方法。
    # 允许用户未登陆情况下访问此接口，通过判断user的值来确定是否登陆
    def perform_authentication(self, request):
        pass

    def post(self, request):

        serializer = CartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        sku_id = serializer.validated_data.get('sku_id')
        count = serializer.validated_data.get('count')
        selected = serializer.validated_data.get('selected')

        try:
            user = request.user
        except Exception:
            # 前端携带错误的token
            user = None

        if user and user.is_authenticated:
            redis_conn = get_redis_connection('cart')
            pl = redis_conn.pipeline()

            pl.hincrby('cart_%s' % user.id, sku_id, count)
            if selected:
                pl.sadd('cart_selected_%s' % user.id, sku_id)
            pl.execute()

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            # 用户未登陆 购物车数据保存在cookie中
            cart_str = request.COOKIES.get('cart')

            if cart_str:
                # 存入cookie的格式是：字典转bytes，bytes再base64转成字符串
                cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))
            else:
                # 未登录下第一次添加物品到购物车
                cart_dict = {}

            # cookie中存储的格式
            # {
            #     sku_id: {
            #     "count": xxx, // 数量
            #     "selected": True // 是否勾选
            # }

            if sku_id in cart_dict:
                origin_count = cart_dict[sku_id]['count']
                count += origin_count

            cart_dict[sku_id] = {
                'count': count,
                'selected': selected
            }
            cookie_cart = base64.b64encode(pickle.dumps(cart_dict)).decode()

            response = Response(serializer.data, status=status.HTTP_201_CREATED)
            response.set_cookie('cart', cookie_cart)
            return response

    def get(self, request):

        try:
            user = request.user
        except Exception:
            user = None

        if user and user.is_authenticated:
            redis_conn = get_redis_connection('cart')
            redis_cart = redis_conn.hgetall('cart_%s' % user.id)
            cart_selected = redis_conn.smembers('cart_selected_%s' % user.id)

            # 将redis和cookie整合成一致的字典，方便数据库查询
            cart_dict = {}
            for sku_id, count in redis_cart.items():
                # redis中键值都是字符串
                cart_dict[int(sku_id)] = {
                    'count': int(count),
                    'selected': sku_id in cart_selected
                }
        else:
            cart_str = request.COOKIES.get('cart')
            if cart_str:
                cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))
            else:
                cart_dict = {}

        sku_id_list = cart_dict.keys()
        # 查询购物车中sku对象
        sku_obj_list = SKU.objects.filter(id__in=sku_id_list)
        for sku in sku_obj_list:
            sku.count = cart_dict[sku.id]['count']
            sku.selected = cart_dict[sku.id]['selected']

        # TODO: 多的一方序列化
        serializer = CartSKUSerializer(sku_obj_list, many=True)
        return Response(serializer.data)

    def put(self, request):

        serializer = CartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        sku_id = serializer.validated_data.get('sku_id')
        count = serializer.validated_data.get('count')
        selected = serializer.validated_data.get('selected')

        try:
            user = request.user
        except Exception:
            user = None

        if user is not None and user.is_authenticated:

            redis_conn = get_redis_connection('cart')
            pl = redis_conn.pipeline()
            pl.hset('cart_%s' % user.id, sku_id, count)
            if selected:
                # 勾选增加记录
                pl.sadd('cart_selected_%s' % user.id, sku_id)
            else:
                # 未勾选 删除记录
                pl.srem('cart_selected_%s' % user.id, sku_id)
            pl.execute()

            return Response(serializer.data)
        else:
            cart_str = request.COOKIES.get('cart')

            if cart_str:
                cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))
            else:
                cart_dict = {}

            if sku_id in cart_dict:
                cart_dict[sku_id] = {
                    'count': count,
                    'selected': selected
                }

            cookie_cart = base64.b64encode(pickle.dumps(cart_dict)).decode()

            response = Response(serializer.data)
            response.set_cookie('cart', cookie_cart)

            return response
