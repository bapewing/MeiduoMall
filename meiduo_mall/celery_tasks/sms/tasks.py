from celery_tasks.main import celery_app
from celery_tasks.sms import constants
from celery_tasks.sms.yuntongxun.sms import CCP
import logging

logger = logging.getLogger('django')


@celery_app.task(name='send_sms_code')
def send_sms_code(mobile, sms_code):
    try:
        ccp = CCP()
        result = ccp.send_template_sms(mobile, [sms_code, int(constants.SMS_CODE_REDIS_EXPIRES / 60)],
                                       constants.SMS_CODE_TEMPLATE_ID)
    except Exception as e:
        logger.error('发送短信验证码[异常][mobile:%s message:%s]' % (mobile, e))
    else:
        if result == 0:
            logger.info('发送短信验证码[正常][mobile:%s]', mobile)
        else:
            logger.warning('发送短信验证码[失败][mobile:%s]', mobile)
