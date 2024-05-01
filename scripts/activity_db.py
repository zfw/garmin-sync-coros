import os
import sys
import logging

import sqlite3
from sqlite_db import  SqliteDB
from config import DB_DIR

logger = logging.getLogger(__name__)

class ActivityDB:
    
    def __init__(self, db_name):
        ## Garmin数据库
        self._db_name = db_name

    @property
    def db_name(self):
        return self._db_name

     ## 保存Stryd运动信息
    def saveActivity(self, id, source='garmin'):
        exists_select_sql = 'SELECT * FROM activity_table WHERE activity_id = ? AND activity_source = ?'
        with SqliteDB(self._db_name) as db:
            exists_query_set = db.execute(exists_select_sql, (id, source)).fetchall()
            query_size = len(exists_query_set)
            logger.warning(f"db saveActivity {id} {source} query_size: {query_size}")
            if query_size == 0:
                db.execute('insert into activity_table (activity_id, activity_source) values (?, ?)', (id, source))
                self.saveActivity(id, source)
                
    
    def getUnSyncActivity(self, source = 'garmin'):
        select_un_upload_sql = 'SELECT activity_id FROM activity_table WHERE is_sync = 0 AND activity_source = ?'
        with SqliteDB(self._db_name) as db:
            un_upload_result = db.execute(select_un_upload_sql, (source,)).fetchall() #注意：一个值时需要有最后面的,
            query_size = len(un_upload_result)
            logger.warning(f"db getUnSyncActivity {source} query_size: {query_size}")
            if query_size == 0:
                return None
            else:
                activity_id_list = []
                for result in un_upload_result:
                    activity_id_list.append(result[0])
                return activity_id_list
            
    def updateSyncStatus(self, id:int, source:str = 'garmin'):
        update_sql = "update activity_table set is_sync = 1 WHERE activity_id = ? AND activity_source = ?"
        with SqliteDB(self._db_name) as db:
          db.execute(update_sql, (id, source))
    
    def updateExceptionSyncStatus(self, id:int, source:str = 'garmin'):
        update_sql = "update activity_table set is_sync = 2 WHERE activity_id = ? AND activity_source = ?"
        with SqliteDB(self._db_name) as db:
          db.execute(update_sql, (id, source))

    def initDB(self):
      with SqliteDB(os.path.join(DB_DIR, self._db_name)) as db:
          db.execute('''

          CREATE TABLE activity_table(
              id INTEGER NOT NULL PRIMARY KEY  AUTOINCREMENT ,
              activity_source VARCHAR(50) NOT NULL DEFAULT 'garmin' ,
              activity_id INTEGER NOT NULL  , 
              is_sync INTEGER NOT NULL  DEFAULT 0,
              create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
              update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
          ) 

          '''
          )