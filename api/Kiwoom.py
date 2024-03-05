from PyQt5.QAxContainer import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import time
import pandas as pd
from util.const import *


class Kiwoom(QAxWidget):
    """ QAxWidget를 상속 받은 것, QAxWidget는 Open API를 사용할 수 있도록 연결하는 기능을 제공 """
    def __init__(self):
        super().__init__()
        self._make_kiwoom_instance()    # 설치한 API를 사용할 수 있도록 설정
        self._set_signal_slots()        # 로그인, 실시간 정보, 기타 제공받을 수 있는 데이터에 대한 응답을 받을 수 있는 slot함수들을 등록

        self._comm_connect()            # 로그인 요청 보내기, _login_slot에서 응답을 받음

        self.account_number = self.get_account_number() # 계좌번호 저장

        self.tr_event_loop = QEventLoop() #tr요청에 대한 응답 대기를 위한 변수

        self.order = {}     #종목 코드를 키 값으로 해당 종목의 주문 정보를 담은 딕셔너리
        self.balance = {}   #종목 코드를 키 값으로 해당 종목의 매수 정보를 담은 딕셔너리

    def _make_kiwoom_instance(self):
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")

    def _set_signal_slots(self):
        """API로 보내는 요청들을 받아올 slot을 등록하는 함수"""
        # 로그인 응답의 결과를 _on_login_connect을 통해 받도록 설정
        self.OnEventConnect.connect(self._login_slot)

        # TR의 응답 결과를 _on_receive_tr_data를 통해 받도록 설정
        self.OnReceiveTrData.connect(self._on_receive_tr_data)

        # TR/주문 메시지를 _on_receive_msg을 통해 받도록 설정
        self.OnReceiveMsg.connect(self._on_receive_msg)
        # 주문 접수/체결 결과를 _on_chejan_slot을 통해 받도록 설정
        self.OnReceiveChejanData.connect(self._on_chejan_slot)

    def _login_slot(self, err_code):
        if err_code == 0:
            print("connected")
        else:
            print("not connected")

        self.login_event_loop.exit()

    def _comm_connect(self):
        # API서버로 로그인 요청 보내기
        self.dynamicCall("CommConnect()")

        # 로그인 요청에 대한 응답이 올때까지 대기
        self.login_event_loop = QEventLoop()
        self.login_event_loop.exec_()

    def get_account_number(self, tag="ACCNO"): # 계좌번호를 의미하는 "ACCNO", tag에 따라 얻어 오는 값 변경
        account_list = self.dynamicCall("GetLoginInfo(QString)", tag)  # tag로 전달한 요청에 대한 응답을 받아옴
        account_number = account_list.split(';')[0]   # 국내 주식 모의투자만 신청했을때를 가정, 계좌가 한 개임을 보장
        print("계좌번호 :",account_number)
        return account_number

    def get_code_list_by_market(self, market_type): # 주식 시장별 종목 코드 리스트 뽑기 ,market_type은 어떤 시장에서 종목을 얻어 올지 의미하는 구분 값
        code_list = self.dynamicCall("GetCodeListByMarket(QString)", market_type)
        code_list = code_list.split(';')[:-1]   # 마지막 항목에는 ''이 붙어 있으므로 이것을 제외하고 넣기
        return code_list

    def get_master_code_name(self, code): #종목 코드 리스트를 종목명으로 반환
        code_name = self.dynamicCall("GetMasterCodeName(QString)", code)
        return code_name

    def get_price_data(self, code):     #종목의 상장일부터 가장 최근 일자까지 일봉 정보를 가져오는 함수
        self.dynamicCall("SetInputValue(QString, QString)", "종목코드", code)
        self.dynamicCall("SetInputValue(QString, QString)", "수정주가구분", "1")
        self.dynamicCall("CommRqData(QString, QString, int, QString)", "opt10081_req", "opt10081", 0, "0001")

        self.tr_event_loop.exec_()

        ohlcv = self.tr_data

        while self.has_next_tr_data:
            self.dynamicCall("SetInputValue(QString, QString)", "종목코드", code)
            self.dynamicCall("SetInputValue(QString, QString)", "수정주가구분", "1")
            self.dynamicCall("CommRqData(QString, QString, int, QString)", "opt10081_req", "opt10081", 2, "0001")
            self.tr_event_loop.exec_()

            for key, val in self.tr_data.items():   # 이미 받아온 데이터의 마지막 부분에 붙이는 코드
                ohlcv[key] += val

        df = pd.DataFrame(ohlcv, columns=['open', 'high', 'low', 'close', 'volume'], index=ohlcv['date'])

        return df[::-1] #index를 기준으로 오름차순 정렬하여 return, 내림차순은 return df

    def _on_receive_tr_data(self, screen_no, rqname, trcode, record_name, next, unused1, unused2, unused3, unused4):
        "TR조회의 응답 결과를 얻어오는 함수"
        print("[Kiwoom] _on_receive_tr_data is called {} / {} / {}".format(screen_no, rqname, trcode))
        tr_data_cnt = self.dynamicCall("GetRepeatCnt(QString, QString)", trcode, rqname)

        if next == '2':
            self.has_next_tr_data = True
        else:
            self.has_next_tr_data = False

        if rqname == "opt10081_req": #해당 종목의 일봉을 얻어오는 TR
            ohlcv = {'date': [], 'open': [], 'high': [], 'low': [], 'close': [], 'volume': []}

            for i in range(tr_data_cnt):
                date = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "일자")
                open = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "시가")
                high = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "고가")
                low = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "저가")
                close = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "현재가")
                volume = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "거래량")

                ohlcv['date'].append(date.strip())
                ohlcv['open'].append(int(open))
                ohlcv['high'].append(int(high))
                ohlcv['low'].append(int(low))
                ohlcv['close'].append(int(close))
                ohlcv['volume'].append(int(volume))

            self.tr_data = ohlcv

        elif rqname == "opw00001_req": #예수금을 얻어오는 TR
            deposit = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, 0, "주문가능금액")
            self.tr_data = int(deposit)
            print("주문 가능 금액 :",self.tr_data)

        elif rqname == "opt10075_req": #당일 주문 정보 얻어 오는 TR
            for i in range(tr_data_cnt):
                code = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "종목코드")
                code_name = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "종목명")
                order_number = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "주문번호")
                order_status = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "주문상태")
                order_quantity = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i,
                                                  "주문수량")
                order_price = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "주문가격")
                current_price = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "현재가")
                order_type = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "주문구분")
                left_quantity = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i,
                                                 "미체결수량")
                executed_quantity = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i,
                                                     "체결량")
                ordered_at = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "시간")
                fee = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "당일매매수수료")
                tax = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "당일매매세금")

                # 데이터 형변환 및 가공
                code = code.strip()
                code_name = code_name.strip()
                order_number = str(int(order_number.strip()))
                order_status = order_status.strip()
                order_quantity = int(order_quantity.strip())
                order_price = int(order_price.strip())

                current_price = int(current_price.strip().lstrip('+').lstrip('-'))
                order_type = order_type.strip().lstrip('+').lstrip('-')  # +매수,-매도처럼 +,- 제거
                left_quantity = int(left_quantity.strip())
                executed_quantity = int(executed_quantity.strip())
                ordered_at = ordered_at.strip()
                fee = int(fee)
                tax = int(tax)

                # code를 key값으로 한 딕셔너리 변환
                self.order[code] = {
                    '종목코드': code,
                    '종목명': code_name,
                    '주문번호': order_number,
                    '주문상태': order_status,
                    '주문수량': order_quantity,
                    '주문가격': order_price,
                    '현재가': current_price,
                    '주문구분': order_type,
                    '미체결수량': left_quantity,
                    '체결량': executed_quantity,
                    '주문시간': ordered_at,
                    '당일매매수수료': fee,
                    '당일매매세금': tax
                }

            self.tr_data = self.order

        elif rqname == "opw00018_req": # 주식 잔고 정보를 얻어오는 TR
            for i in range(tr_data_cnt):
                code = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "종목번호")
                code_name = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "종목명")
                quantity = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "보유수량")
                purchase_price = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i,
                                                  "매입가")
                return_rate = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i,
                                               "수익률(%)")
                current_price = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "현재가")
                total_purchase_price = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i,
                                                        "매입금액")
                available_quantity = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i,
                                                      "매매가능수량")

                # 데이터 형변환 및 가공
                code = code.strip()[1:]
                code_name = code_name.strip()
                quantity = int(quantity)
                purchase_price = int(purchase_price)
                return_rate = float(return_rate)
                current_price = int(current_price)
                total_purchase_price = int(total_purchase_price)
                available_quantity = int(available_quantity)

                # code를 key값으로 한 딕셔너리 변환
                self.balance[code] = {
                    '종목명': code_name,
                    '보유수량': quantity,
                    '매입가': purchase_price,
                    '수익률': return_rate,
                    '현재가': current_price,
                    '매입금액': total_purchase_price,
                    '매매가능수량': available_quantity
                }

            self.tr_data = self.balance

        self.tr_event_loop.exit()
        time.sleep(0.5)

    def get_deposit(self): # 조회 대상 계좌의 예수금을 얻어 오는 함수
        self.dynamicCall("SetInputValue(QString, QString)", "계좌번호", self.account_number)
        self.dynamicCall("SetInputValue(QString, QString)", "비밀번호입력매체구분", "00")
        self.dynamicCall("SetInputValue(QString, QString)", "조회구분", "2")
        self.dynamicCall("CommRqData(QString, QString, int, QString)", "opw00001_req", "opw00001", 0, "0002")

        self.tr_event_loop.exec_()
        return self.tr_data

    # SendOrder(주문 발생) -> OnReceiveTrData(주문 응답) -> OnReceiveMsg(주문 메시지 수신) -> OnReceiveChejan(주문 접수/체결)
    def send_order(self, rqname, screen_no, order_type, code, order_quantity, order_price, order_classification,
                   origin_order_number=""): #주문 발생 함수
        # order_type : 매수/매도/취소 주문 같은 주문 유형, order_quantity: 매매할 종목의 주문 수량
        # order_pricee: 주문 가격을 나타내며 시장가로 주문할 때는 의미가 없느 필드, 이 프로젝트에서는 시장가 주문으로 인한 슬리피지를 없애고자 주문 가격을 지정하여 사용
        # order_classification: 거래 구분을 나타내는 매개변수이며, 원하는 주문 방식마다 코드로 구분(예: 지정가 00, 시장가 03)
        # order_order_number : 정정 혹은 취소하려는 주문 번호를 의미하는 매개변수, 신규 주문 때는 빈 값
        order_result = self.dynamicCall(
            "SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
            [rqname, screen_no, self.account_number, order_type, code, order_quantity, order_price,
             order_classification, origin_order_number])
        return order_result

    def _on_receive_msg(self, screen_no, rqname, trcode, msg):  #OnReceiveMsg에 대한 응답을 받아 오는 slot
        print("[Kiwoom] _on_receive_msg is called {} / {} / {} / {}".format(screen_no, rqname, trcode, msg))

    #
    def _on_chejan_slot(self, s_gubun, n_item_cnt, s_fid_list):
        print("[Kiwoom] _on_chejan_slot is called "
              "{} / {} / {}".format(s_gubun, n_item_cnt, s_fid_list))

        # 9201;9203;9205;9001;912;913;302;900;901;처럼 전달되는 fid 리스트를 ';' 기준으로 구분함
        for fid in s_fid_list.split(";"):
            if fid in FID_CODES:
                # 9001-종목코드 얻어오기, 종목코드는 A007700처럼 앞자리에 문자가 오기 때문에 앞자리를 제거함
                code = self.dynamicCall("GetChejanData(int)", '9001')[1:]

                # fid를 이용해 data를 얻어오기(ex: fid:9203를 전달하면 주문번호를 수신해 data에 저장됨)
                data = self.dynamicCall("GetChejanData(int)", fid)

                # 데이터에 +,-가 붙어있는 경우 (ex: +매수, -매도) 제거
                data = data.strip().lstrip('+').lstrip('-')

                # 수신한 데이터는 전부 문자형인데 문자형 중에 숫자인 항목들(ex:매수가)은 숫자로 변형이 필요함
                if data.isdigit():
                    data = int(data)

                # fid 코드에 해당하는 항목(item_name)을 찾음(ex: fid=9201 > item_name=계좌번호)
                item_name = FID_CODES[fid]

                # 얻어온 데이터를 출력(ex: 주문가격 : 37600)
                print("{}: {}".format(item_name, data))

                # 접수/체결(s_gubun=0)이면 self.order, 잔고이동이면 self.balance에 값을 저장
                if int(s_gubun) == 0:
                    # 아직 order에 종목코드가 없다면 신규 생성하는 과정
                    if code not in self.order.keys():
                        self.order[code] = {}
                    # order 딕셔너리에 데이터 저장
                    self.order[code].update({item_name: data})
                elif int(s_gubun) == 1:
                    # 아직 balance에 종목코드가 없다면 신규 생성하는 과정
                    if code not in self.balance.keys():
                        self.balance[code] = {}
                    # balance 딕셔너리에 데이터 저장
                    self.balance[code].update({item_name: data})
        # s_gubun값에 따라 저장한 결과를 출력
        if int(s_gubun) == 0:
            print()
            print("* 주문 출력(self.order)")
            print(self.order)
            print()
        elif int(s_gubun) == 1:
            print()
            print("* 잔고 출력(self.balance)")
            print(self.balance)
            print()

    def get_order(self): # 주문 정보를 얻어 오는 함수
        self.dynamicCall("SetInputValue(QString, QString)", "계좌번호", self.account_number)
        self.dynamicCall("SetInputValue(QString, QString)", "전체종목구분", "0")
        self.dynamicCall("SetInputValue(QString, QString)", "체결구분", "0")  # 0:전체, 1:미체결, 2:체결
        self.dynamicCall("SetInputValue(QString, QString)", "매매구분", "0")  # 0:전체, 1:매도, 2:매수
        self.dynamicCall("CommRqData(QString, QString, int, QString)", "opt10075_req", "opt10075", 0, "0002")

        self.tr_event_loop.exec_()
        return self.tr_data

    def get_balance(self): # 계좌의 주식 잔고를 얻어 오는 함수
        self.dynamicCall("SetInputValue(QString, QString)", "계좌번호", self.account_number)
        self.dynamicCall("SetInputValue(QString, QString)", "비밀번호입력매체구분", "00")
        self.dynamicCall("SetInputValue(QString, QString)", "조회구분", "1")
        self.dynamicCall("CommRqData(QString, QString, int, QString)", "opw00018_req", "opw00018", 0, "0002")

        self.tr_event_loop.exec_()
        return self.tr_data