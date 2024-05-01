import os

import urllib3
import json
import hashlib
import logging

from config import COROS_FIT_DIR

logger = logging.getLogger(__name__)

class CorosClient:
    
    def __init__(self, email, password) -> None:
        
        self.email = email
        self.password = password
        self.req = urllib3.PoolManager()
        self.accessToken = None
        self.userId = None
    
    ## 登录接口
    def login(self):
        
        login_url = "https://teamcnapi.coros.com/account/login"

        login_data = {
            "account": self.email,
            "pwd": hashlib.md5(self.password.encode()).hexdigest(),  ##MD5加密密码
            "accountType": 2,
        }
        headers = {
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json;charset=UTF-8",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.39 Safari/537.36",
            "referer": "https://trainingcn.coros.com/",
            "origin": "https://trainingcn.coros.com/",
        }

        login_body = json.dumps(login_data)
        response = self.req.request('POST', login_url, body=login_body, headers=headers)

        login_response = json.loads(response.data)
        login_result = login_response["result"]
        if login_result != "0000":
            raise CorosLoginError("高驰登录异常，异常原因为：" + login_response["message"])

        accessToken = login_response["data"]["accessToken"]
        userId = login_response["data"]["userId"]
        self.accessToken = accessToken
        self.userId = userId

    ## 上传运动
    def uploadActivity(self, file_path):
        ## 判断Token 是否为空
        if self.accessToken == None:
            self.login()

        upload_url = "https://teamcnapi.coros.com/activity/fit/import"

        headers = {
            "Accept": "application/json, text/plain, */*",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.39 Safari/537.36",
            "referer": "https://trainingcn.coros.com/",
            "origin": "https://trainingcn.coros.com/",
            "accesstoken": self.accessToken,
        }

        with open(file_path, 'rb') as f:
            file_data = f.read()
        try:
            response = self.req.request(
                method='POST',
                url=upload_url,
                fields={'sportData': (os.path.basename(file_path), file_data),
                        "jsonParameter": """{"source":1,"timezone":32}"""},
                headers=headers
            )
            upload_response = json.loads(response.data)
            upload_result = upload_response["result"]
            return upload_result
        except Exception as err:
            exit()

    ## 登录装饰器
    def loginCheck(func):
        def ware(self, *args, **kwargs):
            ## 判断Token 是否为空
            if self.accessToken == None:
                self.login()

            return func(self, *args, **kwargs)

        return ware

    def getHeaders(self):
        headers = {
            "Accept": "application/json, text/plain, */*",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.39 Safari/537.36",
            "referer": "https://trainingcn.coros.com/",
            "origin": "https://trainingcn.coros.com/",
            "accesstoken": self.accessToken,
        }
        return headers

    ## 获取下载链接
    @loginCheck
    def getDownloadUrl(self, labelId,  sportType, fileType = 4):
        down_url = f'https://teamcnapi.coros.com/activity/detail/download?labelId={labelId}&sportType={sportType}&fileType=4'
        try:
            response = self.req.request(
                method='POST',
                url=down_url,
                fields={},
                headers=self.getHeaders()
            )
            down_response = json.loads(response.data)
            return down_response["data"]["fileUrl"]
        except Exception as err:
            exit()

    ## 下载
    @loginCheck
    def download(self, url):
        try:
            response = self.req.request(
                method='GET',
                url=url,
                fields={},
                headers=self.getHeaders()
            )
            return response
        except Exception as err:
            exit()

    ## 获取运动
    @loginCheck
    def getActivities(self, pageNumber: int, pageSize: int):

        listUrl = f'https://teamcnapi.coros.com/activity/query?size={str(pageSize)}&pageNumber={str(pageNumber)}&modeList='

        try:
            response = self.req.request(
                method='GET',
                url=listUrl,
                fields={},
                headers=self.getHeaders()
            )
            responseData = json.loads(response.data)
            data = responseData.get('data', {})
            dataList = data.get('dataList', [])
            return dataList
        except Exception as err:
            exit()

    ## 获取所有运动
    def getAllActivities(self):
        all_urlList = []
        pageNumber = 1
        while (True & pageNumber < 2):
            activitiyInfoList = self.getActivities(pageNumber=pageNumber, pageSize=100)
            urlList = []
            for activitiyInfo in activitiyInfoList:
                labelId = activitiyInfo["labelId"]
                sportType = activitiyInfo["sportType"]
                activityDownloadUrl = self.getDownloadUrl(labelId, sportType)
                if (activityDownloadUrl):
                    urlList.append((labelId, activityDownloadUrl)) # 已元祖形式存储
            if len(urlList) > 0:
                all_urlList.extend(urlList)
            else:
                return all_urlList
            pageNumber += 100
        
    @staticmethod
    def find_url_from_id(list, id): 
        for item in list:
            if item[0] == id:
                return item[1]
        return None

    def uploadToGarmin(self, garminClient, db):
        all_activities = self.getAllActivities()
        if all_activities == None or len(all_activities) == 0:
            logger.warning("has no coros activities.")
            exit()
        for activity in all_activities:
            activity_id = activity[0]
            db.saveActivity(activity_id, 'coros')

        un_sync_id_list = db.getUnSyncActivity('coros')
        if un_sync_id_list == None or len(un_sync_id_list) == 0:
            logger.warning("has no un sync coros activities.")
            exit()
        for un_sync_id in un_sync_id_list:
            try:
                file_url = self.find_url_from_id(all_activities, str(un_sync_id))
                if (file_url == None):
                    continue 
                
                fileResponse = self.download(file_url)
                file_path = os.path.join(COROS_FIT_DIR, f"{un_sync_id}.fit")
                with open(file_path, "wb") as fb:
                    fb.write(fileResponse.data)
                
                try:
                    logger.warning(f"uploading garmin ${un_sync_id} {file_path}.")
                    upload_result = garminClient.upload_activity(file_path)
                    if upload_result.status_code == 202:
                        logging.warning(f"Upload to garmin {un_sync_id} success.")
                        self.update_db_status(db, un_sync_id)
                except Exception as e:
                    # 解析上传失败原因，比如是否是因为重复
                    try:
                        responseData = json.loads(e.error.response.text)
                        messages = responseData['detailedImportResult']['failures'][0]['messages']
                        code = messages[0]['code']
                        content = messages[0]['content']
                        logging.warning(f"Upload to garmin fail: {code}:{content}")
                        if '202' == str(code):
                            self.update_db_status(db, un_sync_id)
                    except Exception as e:
                        logging.warning(f"Upload to garmin error inside: {e}")
            except Exception as err:
                print(err)
                logging.warning(f"download garmin activity fail: {err}")
    # 更新数据库同步状态            
    @staticmethod
    def update_db_status(db, un_sync_id):
        try:
            db.updateSyncStatus(un_sync_id, 'coros')
            logger.warning(f"sync coros ${un_sync_id} success.")
        except Exception as err:
            print(err)
            db.updateExceptionSyncStatus(un_sync_id, 'coros')
            logger.warning(f"sync coros ${un_sync_id} exception.")
                


class CorosLoginError(Exception):

    def __init__(self, status):
        """Initialize."""
        super(CorosLoginError, self).__init__(status)
        self.status = status

class CorosActivityUploadError(Exception):

    def __init__(self, status):
        """Initialize."""
        super(CorosActivityUploadError, self).__init__(status)
        self.status = status
