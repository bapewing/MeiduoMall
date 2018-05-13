# 图片验证码Redis有效期， 单位：秒
IMAGE_CODE_REDIS_EXPIRES = 300

# 短信验证码Redis有效期，单位：秒
SMS_CODE_REDIS_EXPIRES = 300

# 短信验证码发送时间间隔
SMS_CODE_REDIS_INTERVAL = 60

# 短信验证码模板
SMS_CODE_TEMPLATE_ID = 1

# 七牛空间域名
QINIU_DOMIN_PREFIX = "http://p7os57adh.bkt.clouddn.com/"

# 首页展示最多的新闻数量
HOME_PAGE_MAX_NEWS = 10

# 用户的关注每一页最多数量
USER_FOLLOWED_MAX_COUNT = 4

# 用户收藏展示最多新闻数量
USER_COLLECTION_MAX_NEWS = 10

# 其他用户每一页最多新闻数量
OTHER_NEWS_PAGE_MAX_COUNT = 10

# 点击排行展示的最多新闻数据
CLICK_RANK_MAX_NEWS = 6

# 管理员页面用户每页多最数据条数
ADMIN_USER_PAGE_MAX_COUNT = 10

# 管理员页面新闻每页多最数据条数
ADMIN_NEWS_PAGE_MAX_COUNT = 10

# 设置开发环境
DEVELOPMENT = "development"
PRODUCTION = "production"
TESTING = "testing"