from datetime import datetime
import pandas as pd
import talib as ta
import warnings
import GetInfo

class StockCals:
    def __init__(self):
        self.infoObj = GetInfo.StockKr()
        self.mongo = self.infoObj.mongo
        self.saved_df = pd.DataFrame()  # 분석 or 지표계산할 때 총괄 데이터프레임

        # 이동평균선 리스트
        self.sma_window = [5, 10, 20, 60, 120]
        self.ema_window = [9, 12, 26]

        # 최고가 관련
        self.high_crit = [9, 26]


    ''' X. 총 모듈 '''
    def module(self, code_update=False, day_info=False, compute_criteria=True):
        self.infoObj.module(code_update=code_update, dayinfo_update=day_info)
        if compute_criteria:
            self.module_calc()


    ''' A. 주식 계산 메소드 '''
    def module_calc(self):
        ''' 초기 day_info.xlsx 로부터 MACD, 60평균선 등을 계산하는데 사용하는 함수 (전데이터 수정)
        :param hgih_crit: 최고가 날 기준 (기본값 240일)
        :return:
        '''
        for company, tk in self.infoObj.thema_total_dict.items():
            cals_last_date = datetime(1999, 1, 1)
            print("[" + company + " 지표 계산중...]")
            last_cals_30 = self.mongo.read_last_one("DayInfo", "Cals", "날짜", {"티커": tk}, 30)
            df = None
            try:
                cals_last_date = pd.to_datetime(last_cals_30.next()["날짜"])
                before = self.mongo.read_last_one("DayInfo", "Info", "날짜", {"날짜": {"$lt": cals_last_date}, "티커": tk}, 120)
                last_docunment = None
                for document in before:
                    last_docunment = document

                after = None
                if last_docunment:
                    after = self.mongo.read("DayInfo", "Info", {"날짜": {"$gte": last_docunment["날짜"]}, "티커": tk})
                    df = pd.DataFrame(after).set_index("날짜")
                    info_last_date = df.tail(1).index
                    diff_day = info_last_date - cals_last_date
                    if diff_day.days == 0:
                        continue
                if not after:
                    df = self.infoObj.readDaySQL(company)
            except StopIteration:
                try:
                    df = self.infoObj.readDaySQL(company)
                except KeyError:
                    continue

            self.saved_df = pd.DataFrame(index=df.index)

            try:
                # 1. 주가이동평균 구함.
                print("{주가이동평균(Moving Average) 계산 중 ...}")
                self.movingAverage(cal_df=df)

                # 2. MACD 구함.
                print("{MACD(Moving Average Convergence Divergence) 계산 중 ...}")
                self.macd(cal_df=df)

                # 3. 일목기준표 구함.
                print("{일목균형표(Ichimoku Kinkoyo) 계산 중 ...}")
                self.ichimoku(cal_df=df)

                # 4. X일 중 최고가를 구함.
                print("{" + str(self.high_crit) + "일 최고가(highest price) 계산 중 ...}")
                self.highest_price(cal_df=df)
                #print(self.saved_df.tail(5))
            except KeyError:
                continue

            self.saved_df = self.saved_df.reset_index()
            self.saved_df = self.saved_df.reset_index()
            processing_frame = self.saved_df[self.saved_df["날짜"] > cals_last_date]

            with warnings.catch_warnings():
                warnings.simplefilter("ignore") # 워닝 무시
                ret_dict = processing_frame.to_dict(orient="records")
                for rec in ret_dict:
                    rec["회사명"] = company
                    rec["티커"] = tk
            #print(ret_dict)
            self.mongo.insert("DayInfo", "Cals", ret_dict)


    def movingAverage(self, cal_df: pd.DataFrame):
        ''' A. 이동평균선 계산 (Moving Arerage)
        _ (Junhyeong (20190511))
        :param cal_df: 저장할 DataFrame
        :return: 
        '''
        for w in self.sma_window:
            col_name = "SMA"+str(w)
            self.saved_df[col_name] = ta.SMA(cal_df["종가"], timeperiod=w)
        return self.saved_df

    def macd(self, cal_df: pd.DataFrame):
        ''' B. MACD (Moving Average Convergence Divergence) 계산
        _ (Junhyeong (20190511))
        :param cal_df:저장할 DataFrame
        :return:
        '''
        ema12 = ta.EMA(cal_df["종가"], timeperiod=self.ema_window[1])
        ema26 = ta.EMA(cal_df["종가"], timeperiod=self.ema_window[2])
        self.saved_df["MACD"] = ema12 - ema26
        self.saved_df["MACD_Signal"] = ta.EMA(self.saved_df["MACD"], timeperiod=self.ema_window[0])
        self.saved_df["MACD_Histogram"] = self.saved_df["MACD"] - self.saved_df["MACD_Signal"]
        return self.saved_df

    def ichimoku(self, cal_df: pd.DataFrame):
        ''' C. 일목균형표 계산 (선행, 후행, 전환선, 기준선 계산)
        _ (Junhyeong (20190511))
        전환선: 9일간의 최고가 + 최소가 의 평균
        기준선: 26일간의 최고 + 최소 의 평균
        선행스팬1: 기준선(Kijun-sen)을 26일 전으로 이동시킵니다.
        선행스팬2: 최근 52일의 고가(High)와 저가(Low)를 더한 후, 52로 나눈 값을 26일 전으로 이동시킵니다.
        후행스팬: 현재 주가를 26일 전으로 이동시킵니다.
        :param cal_df: 저장할 DataFrame
        :return:

        '''
        self.saved_df["전환선"] = (cal_df["고가"].rolling(window=9).max() + cal_df["저가"].rolling(window=9).min()) / 2
        self.saved_df["기준선"] = (cal_df["고가"].rolling(window=26).max() + cal_df["저가"].rolling(window=26).min()) / 2
        self.saved_df["선행스팬1"] = ((self.saved_df["기준선"] + self.saved_df["전환선"])/2).shift(26)
        self.saved_df["선행스팬2"] = ((cal_df["고가"].rolling(window=52).max() + cal_df["저가"].rolling(window=52).min()) / 2).shift(26)
        self.saved_df["후행스팬"] = cal_df["종가"].shift(-25)
        # 주가 지표가 트랜젝션으로 넣을 시 NULL 트랜젝션에 스팬만 들어가게 되는데 그러지 말고
        # 현재 지표를 26일로 당기기 전의 값을 기록. (즉, 계산 시 26일 앞으로 당겨서 봐야함)
        self.saved_df["선행스팬1_미래"] = ((self.saved_df["기준선"] + self.saved_df["전환선"])/2)
        self.saved_df["선행스팬2_미래"] = ((cal_df["고가"].rolling(window=52).max() + cal_df["저가"].rolling(window=52).min()) / 2)

    def highest_price(self, cal_df: pd.DataFrame):
        ''' D. high_crit=[9,26] 일 종가 중 최고가?
            (약 2주, 1달 사이의 최고가를 갱신했는가 여부 확인) _ (Junhyeong (20190511))
        :param cal_df:
        :param high_crit:
        :return:
        '''
        for high in self.high_crit:
            naming = str(high) + "일_최고가"
            self.saved_df[naming] = cal_df["종가"].rolling(window=high).max()


    ''' B. Utility '''
    def read_days_cals(self, company: str):
        ''' MongoDB (DayInfo.회사코드) 에서 DayInfo 정보 중 Cals (MACD,SMA,스팬 등등) 받아오기
        _ Junhyeong (20190511)
        :param company: reading할 회사
        :return: 일봉 Dataframe
        '''

        # 회사가 DB에 없을 경우 빈 DataFrame 리턴
        try:
            query = {
                "$or": [
                    {"회사명": company},
                    {"티커": company}
                ]
            }
            findingSQL = self.mongo.read("DayInfo", "Cals", query)
        except Exception:
            print(f"{company} 는 invalid 데이터 입니다.")
            return pd.DataFrame()

        return pd.DataFrame(findingSQL).set_index("날짜")

if __name__ == "__main__":
    obj = StockCals()
    obj.module()

    print(obj.read_days_cals("삼성전자"))
