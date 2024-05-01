import os

# 此处无需填值，方便后面的for in根据这里的key从环境变量里面取值即可
SYNC_CONFIG = {
    'GARMIN_AUTH_DOMAIN': '',
    'GARMIN_EMAIL': '',
    'GARMIN_PASSWORD': '',
    "GARMIN_START_TIME": '',
    "COROS_EMAIL": '',
    "COROS_PASSWORD": '',
    "COROS_START_TIME": ''
}


# 首先读取 面板变量 或者 github action 运行变量
for k in SYNC_CONFIG:
    if os.getenv(k):
        v = os.getenv(k)
        SYNC_CONFIG[k] = v

# getting content root directory
current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)


GARMIN_FIT_DIR = os.path.join(parent, "garmin-fit")
COROS_FIT_DIR = os.path.join(parent, "coros-fit")

DB_DIR =  os.path.join(parent, "db")
