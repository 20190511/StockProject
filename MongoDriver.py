from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import pymongo


class MongoDB:
    def __init__(self):
        self.uri = "mongodb+srv://baejh724:project@stocksql.bn49sg9.mongodb.net/?retryWrites=true&w=majority&appName=StockSQL"
        self.err = False
        try:
            self.client = MongoClient(self.uri, server_api=ServerApi('1'))
        except pymongo.errors.ConnectionFailure:
            self.err = True

        #MongDB Database Logical Set
        self.dbDict = {
            "StockCode": {"KOSDAQ", "KOSPI", "HIGHVOLUMN"},
            "DayInfo": "상장회사 티커",
            "DayCals": "상장회사 티커",
            "DayAnalys": "상장회사 티커"
        }

    def insert(self, dbName:"str", tableName:"str", queryList: list, primaryKey="", primaryKeySet=False):
        ''' MongoDB의 dbName.tableName 에 insert를 하는 메소드
         _ Junhyeong (20190511)
        :param dbName: Database Name
        :param tableName: table Name
        :param queryList: query List
        :param primaryKey: PK 설정 시 index 이름
        :param primaryKeySet: PK 설정여부
        :return: 성공 시 True 에러시 False
        :return:
        '''
        db = self.client[dbName]
        collections = db[tableName]

        if primaryKeySet:
            for queryDict in queryList:
                queryDict["_id"] = queryDict[primaryKey]

        try:
            collections.insert_many(queryList)
        except pymongo.errors.BulkWriteError:
            return self.insert_listone(dbName, tableName, queryList, primaryKey, primaryKeySet)
        return True

    def insert_listone(self, dbName:"str", tableName:"str", queryList: list, primaryKey="", primaryKeySet=False):
        ''' Primary Key 충돌로 인하여 한 Query 씩 Insert 할 시 돌아가는 System Method
         _ Junhyeong (20190511)
        :param dbName: Database Name
        :param tableName: table Name
        :param queryList: query List
        :param primaryKey: PK 설정 시 index 이름
        :param primaryKeySet: PK 설정여부
        :return: 성공 시 True 에러시 False
        '''
        db = self.client[dbName]
        collections = db[tableName]

        if primaryKeySet:
            for queryDict in queryList:
                queryDict["_id"] = queryDict[primaryKey]

        #print(queryList)
        for item in queryList:
            try:
                collections.insert_one(item)
            except pymongo.errors.DuplicateKeyError:
                print(f"key:{item} 이미 존재 하므로 pass ...")
                continue
            except Exception:
                print(f"Key:{item} 알 수 없는 에러..")
                return False

        return True

    def read(self, dbname: str, tablename: str) -> list:
        ''' MongoDB 에서 dbName.tablename 에 해당하는 모든 Record 를 dictionary List 형태로 반환
        _ Junhyeong (20190511)
        :param dbname: database name 
        :param tablename: table name
        :return: 해당 table의 딕셔너리가 들어있는 리스트
        '''
        db = self.client[dbname]
        collections = db[tablename]
        rawDict = collections.find()
        retDict = [{k: v for k, v in d.items() if k != "_id"} for d in rawDict]
        return retDict

    def read_first_one(self, dbname: str, tablename: str) -> dict:
        ''' MongoDB 에서 dbName.tableName 에 해당 하는 가장 첫 번째 record 반환
         _ Junhyeong (20190511)
        :param dbname: Database Name
        :param tablename: Table Name
        :return: 해당 하는 dictionary 값
        '''
        db = self.client[dbname]
        collections = db[tablename]
        retData = collections.find_one(sort=[("_id", pymongo.ASCENDING)])
        return retData

    def read_last_one(self, dbname: str, tablename: str) -> dict:
        ''' MongoDB 에서 dbName.tableName 에 해당 하는 가장 마지막 record 반환
         _ Junhyeong (20190511)
        :param dbname: Database Name
        :param tablename: Table Name
        :return: 해당하는 dictionary 값
        '''
        db = self.client[dbname]
        collections = db[tablename]
        retData = collections.find_one(sort=[("_id", pymongo.DESCENDING)])
        return retData

if __name__ == "__main__":

    # DB에 들어가는지 확인..
    test = [{"company":"APS", "code":"054620"}, {"company":"AP시스템", "code":"265520"}, {"company":"AP위성", "code":"211270"}, {"company":"3S", "code":"060310"}]
    obj = MongoDB()
    #bj.insert("StockCode", "KOSDAQ", test, "code", primaryKeySet=True)
