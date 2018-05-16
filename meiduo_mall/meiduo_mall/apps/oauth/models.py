from django.db import models

from meiduo_mall.utils.basemodels import BaseModel


class OauthQQUser(BaseModel):
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, verbose_name='用户')
    openid = models.CharField(max_length=64, db_index=True, verbose_name='qq_openid')

    class Meta:
        db_table = "tb_oauth_qq"
        verbose_name = "QQ登录用户信息"
        verbose_name_plural = verbose_name
