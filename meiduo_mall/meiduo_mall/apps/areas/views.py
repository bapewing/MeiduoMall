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
    # TODO:关闭分页处理
    pagination_class = None

    # TODO:了解下重写query_set方法
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
