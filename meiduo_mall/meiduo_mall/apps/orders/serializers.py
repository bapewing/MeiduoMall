from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from django_redis import get_redis_connection
from rest_framework import serializers

from carts.serializers import CartSKUSerializer
from goods.models import SKU
from orders.models import OrderInfo, OrderGoods


class OrderSettlementSerializer(serializers.Serializer):
    freight = serializers.DecimalField(max_digits=10, decimal_places=2)
    skus = CartSKUSerializer(many=True, read_only=True)


# TODO: 保存订单需要再理思路
class SaveOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderInfo
        fields = ('order_id', 'address', 'pay_method')
        # 'write_only':   向后端写数据  向后端传数据
        # 'read_only':  前端要从后端读取数据，后端返回数据使用
        read_only_fields = ('order_id',)
        extra_kwargs = {
            'address': {
                'write_only': True,
                'required': True
            },
            'pay_method': {
                'write_only': True,
                'required': True
            }
        }

    def create(self, validated_data):
        """
        保存订单
        :param validated_data:
        :return:
        """
        user = self.context['request'].user
        order_id = timezone.now().strftime('%Y%m%d%H%M%S') + ('%09d' % user.id)
        address = validated_data['address']
        pay_method = validated_data['pay_method']

        # 开启事务
        with transaction.atomic():
            # 创建保存点，记录当前数据状态
            save_id = transaction.savepoint()

            try:
                order = OrderInfo.objects.create(
                    order_id=order_id,
                    user=user,
                    address=address,
                    total_count=0,
                    total_amount=Decimal('0'),
                    freight=Decimal('10.0'),
                    pay_method=pay_method,
                    status=OrderInfo.ORDER_STATUS_ENUM['UNSEND'] if pay_method == OrderInfo.PAY_METHODS_ENUM[
                        'CASH'] else OrderInfo.ORDER_STATUS_ENUM['UNPAID']
                )
                # 从redis中获取购物车数据
                redis_conn = get_redis_connection('cart')
                cart_redis = redis_conn.hgetall('cart_%s' % user.id)
                cart_selected = redis_conn.smembers('cart_selected_%s' % user.id)

                # 获取redis中选中的商品的数量
                cart = {}
                for sku_id in cart_selected:
                    # TODO: sku_id不用强转吗？
                    cart[int(sku_id)] = int(cart_redis[sku_id])

                # bug: 乐观锁时不能时时更新 sku_obj_list = SKU.objects.filter(id__in=cart.keys())
                sku_id_list = cart.keys()
                for sku_id in sku_id_list:
                    while True:
                        sku = SKU.objects.get(id=sku_id)
                        # 判断库存是否充足
                        count = cart[sku.id]
                        origin_stock = sku.stock
                        origin_sales = sku.sales

                        if sku.stock < count:
                            # 库存不足时回滚
                            transaction.savepoint_rollback(save_id)
                            raise serializers.ValidationError('库存不足')
                        # 减少库存 增加销量
                        new_stock = origin_stock - count
                        new_sales = origin_sales + count
                        ret = SKU.objects.filter(id=sku.id, stock=origin_stock).update(stock=new_stock, sales=new_sales)

                        if ret == 0:
                            continue

                        order.total_count += count
                        order.total_amount += (sku.price * count)

                        # 保存订单
                        OrderGoods.objects.create(
                            # TODO: 外键的保存形式？
                            order=order,
                            sku=sku,
                            count=count,
                            price=sku.price
                        )

                        break
                #  更新订单的数量与金额
                order.save()
            except serializers.ValidationError:
                raise
            except Exception:
                transaction.savepoint_rollback(save_id)
                raise

            transaction.savepoint_commit(save_id)

            # 清除购物车中已经结算的商品
            pl = redis_conn.pipeline()
            pl.hdel('cart_%s' % user.id, *cart_selected)
            pl.srem('cart_selected_%s' % user.id, *cart_selected)
            pl.execute()

            return order
