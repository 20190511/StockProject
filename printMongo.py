from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import pymongo
uri = "mongodb+srv://baejh724:project@stocksql.bn49sg9.mongodb.net/?retryWrites=true&w=majority&appName=StockSQL"
# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))

'''
db = client["testDatabase"]
collections = db["testTable"]
'''



db = client["testDatabase"]
collections = db["testTable"]

for item in collections.find():
    print(item)
#data = {"name":"chanho", "age":26, "city":"seoul"}
#collections.insert_one(data)

    #print(item["name"])
#print(collections.find_one())