import os
import sys
import logging

logger = logging.getLogger(__name__)


CURRENT_DIR = os.path.split(os.path.abspath(__file__))[0]  # 当前目录
garmin_path = CURRENT_DIR + os.path.sep + 'garmin'
coros_path = CURRENT_DIR + os.path.sep + 'coros'
sys.path.append(garmin_path)
sys.path.append(coros_path)

from config import DB_DIR, GARMIN_FIT_DIR, COROS_FIT_DIR
from garmin.garmin_client import GarminClient
from activity_db import ActivityDB
from coros.coros_client import CorosClient

# 此处无需填值，方便后面的for in根据这里的key从环境变量里面取值即可
SYNC_CONFIG = {
    'GARMIN_AUTH_DOMAIN': '',
    'GARMIN_EMAIL': '',
    'GARMIN_PASSWORD': '',
    "COROS_EMAIL": '',
    "COROS_PASSWORD": '',
}


def init(coros_db):
    ## 判断RQ数据库是否存在
    print(os.path.join(DB_DIR, coros_db.db_name))
    if not os.path.exists(os.path.join(DB_DIR, coros_db.db_name)):
        ## 初始化建表
        coros_db.initDB()
    if not os.path.exists(GARMIN_FIT_DIR):
        os.mkdir(GARMIN_FIT_DIR)
    if not os.path.exists(COROS_FIT_DIR):
        os.mkdir(COROS_FIT_DIR)


def getClient():
    # 首先读取 面板变量 或者 github action 运行变量
    for k in SYNC_CONFIG:
        if os.getenv(k):
            v = os.getenv(k)
            SYNC_CONFIG[k] = v

    ## db 名称
    db_name = "garmin.db"
    ## 建立DB链接
    garmin_db = ActivityDB(db_name)
    ## 初始化DB位置和下载文件位置
    init(garmin_db)

    GARMIN_EMAIL = SYNC_CONFIG["GARMIN_EMAIL"]
    GARMIN_PASSWORD = SYNC_CONFIG["GARMIN_PASSWORD"]
    GARMIN_AUTH_DOMAIN = SYNC_CONFIG["GARMIN_AUTH_DOMAIN"]
    garminClient = GarminClient(GARMIN_EMAIL, GARMIN_PASSWORD, GARMIN_AUTH_DOMAIN)

    COROS_EMAIL = SYNC_CONFIG["COROS_EMAIL"]
    COROS_PASSWORD = SYNC_CONFIG["COROS_PASSWORD"]
    corosClient = CorosClient(COROS_EMAIL, COROS_PASSWORD)

    return garminClient, corosClient, garmin_db


# 将高驰运动记录导入到佳明
def coros_to_garmin():
    garminClient, corosClient, db = getClient()
    corosClient.uploadToGarmin(garminClient, db)


if __name__ == "__main__":
    coros_to_garmin()
