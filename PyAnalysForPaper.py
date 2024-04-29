import MongoDriver
import pandas as pd
import datetime
import warnings
from pykrx import stock, bond
import GetInfo
import marcap
import matplotlib.pyplot as plt

def drawGraph(df: pd.DataFrame):
    # 그래프 그리기
    plt.figure(figsize=(10, 6))

    # 각 열을 그래프로 표현
    for column in df.columns[1:]:  # '날짜' 열을 제외한 나머지 열을 그래프로 표현
        plt.plot(df[column], label=column)

    # 그래프 속성 설정
    plt.title('Example Graph')
    plt.xlabel('회사명')
    plt.ylabel('Probability')
    plt.ylim(0,1)
    plt.legend(loc='upper left')
    plt.grid(True)
    plt.xticks(rotation=45)

    # 그래프 출력
    plt.tight_layout()
    plt.show()

class Support:
    def __init__(self):
        self.stk = GetInfo.StockKr()
        self.mongo = self.stk.mongo
        self.today = GetInfo.global_today
        self.cap_dict = {
            "대기업": 10000000000000,
            "중견기업": 500000000000
        }
    def update_amount(self):
        ''' 시가총액을 업데이트 하는 메소드  _Junhyeong (04.29)
        :return: None
        '''
        dates = self.stk.day_counter(offset=5)
        df = marcap.marcap_data(dates, dates).reset_index()
        df = df[["Code", "Name", "Marcap"]]
        df.columns.values[0] = "code"
        df.columns.values[1] = "회사명"
        df.columns.values[2] = "시가총액"
        print(df)
        dicts = df.to_dict(orient="records")
        self.stk.mongo.insert("StockCode", "Amount", dicts, "code", True)
        #print(dicts)

    def get_company(self):

        queryBig = {"시가총액": {"$gte": self.cap_dict["대기업"]}}
        queryMiddle = {"시가총액": {"$gte": self.cap_dict["중견기업"], "$lte": self.cap_dict["대기업"]}}
        querySmall = {"시가총액": {"$lte": self.cap_dict["중견기업"]}}


        listBig = self.mongo.read_last_one("StockCode", "Amount", "시가총액", queryBig, 100)[25:35]
        listMiddle = self.mongo.read_last_one("StockCode", "Amount", "시가총액", queryMiddle, 100)[35:45]
        listSmall = self.mongo.read_last_one("StockCode", "Amount", "시가총액", querySmall, 100)[45:55]

        ret_dict = {
            "대기업": [],
            "중견기업": [],
            "중소기업": []
        }

        for li in listBig:
            ret_dict["대기업"].append((li["code"], li["회사명"], li["시가총액"]))

        for li in listMiddle:
            ret_dict["중견기업"].append((li["code"], li["회사명"], li["시가총액"]))

        for li in listSmall:
            ret_dict["중소기업"].append((li["code"], li["회사명"], li["시가총액"]))
        return ret_dict

    def propAnalys(self, name_dict: dict, names):
        df_list = []
        # 대기업 분류
        for ticker, com, cap in name_dict[names]:
            read_probs = self.mongo.read_last_date("DayInfo", "Probs", {"티커": ticker},  client=self.mongo.client2)
            df = pd.DataFrame([read_probs])
            df.drop(columns=["날짜"], inplace=True)
            df["회사명"] = com
            df_list.append(df)

        total_df = pd.concat(df_list, ignore_index=True)
        total_df.set_index("회사명", inplace=True)

        total_df.to_excel(f"D:\\Bae's File\\2024년\\1학기\\컴퓨터학개론\\논문\\{names}.xlsx")
        drawGraph(total_df)
if __name__ == "__main__":
    s = Support()
    ret_dict = s.get_company()
    s.propAnalys(ret_dict, "대기업")
