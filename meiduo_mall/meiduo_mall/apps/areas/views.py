from django.shortcuts import render
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework_extensions.cache.mixins import CacheResponseMixin

from areas.models import Area
from areas.serializers import AreaSerializer, SubAreaSerializer


class AreasViewSet(CacheResponseMixin, ReadOnlyModelViewSet):
    """
    list:
    返回所有的省份

    retrieve:
    返回特定省或市的下属行政规划区域
    """
    # 为什么关闭分页处理？
    # 使用 ListModelMixin 的时候使用的时django默认分页功能
    pagination_class = None

    # 了解下重写query_set方法
    # 使用到数据库查询的时候都必须定义queryset或是使用get_queryset
    # 针对不同请求时做处理
    def get_queryset(self):
        if self.action == 'list':
            return Area.objects.filter(parent=None)
        else:
            return Area.objects.all()

    def get_serializer_class(self):
        if self.action == 'list':
            return AreaSerializer
        else:
            return SubAreaSerializer
