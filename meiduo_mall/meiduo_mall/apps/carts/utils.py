import base64
import pickle

from django_redis import get_redis_connection


def merge_cart_cookie_to_redis(request, user, response):
    """
    登陆时将cookie中数据合并到redis中
    :param request: 用户请求对象
    :param user: 当前请求的用户
    :param response: 响应对象清除cookie中的购物车数据
    :return: response
    """
    # 从cookie中读取购物车数据
    cart_str = request.COOKIES.get('cart')
    # bug: cookie中没有数据时，返回正常的response
    if not cart_str:
        return response
    cookie_cart = pickle.loads(base64.b64decode(cart_str.encode()))

    redis_conn = get_redis_connection('cart')
    cart_redis = redis_conn.hgetall('cart_%s' % user.id)

    cart = {}
    for sku_id, count in cart_redis.items():
        # redis中存储的都是字符串，取出都是二进制，整型字符串直接强转成整型
        cart[int(sku_id)] = int(count)

    selected_sku_id_list = []
    for sku_id, selected_count_dict in cookie_cart.items():
        # cookie数据直接覆盖redis数据
        cart[sku_id] = selected_count_dict.get('count')
        if selected_count_dict.get('selected'):
            selected_sku_id_list.append(sku_id)

    pl = redis_conn.pipeline()
    pl.hmset('cart_%s' % user.id, cart)
    # 列表拆包
    pl.sadd('cart_selected_%s' % user.id, *selected_sku_id_list)
    pl.execute()

    response.delete_cookie('cart')
    return response
