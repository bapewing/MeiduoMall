from rest_framework import serializers

from carts.serializers import CartSKUSerializer


class OrderSettlementSerializer(serializers.Serializer):
    freight = serializers.DecimalField
    skus = CartSKUSerializer(many=True, read_only=True)
