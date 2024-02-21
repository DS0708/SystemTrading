from PyQt5.QAxContainer import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *


class Kiwoom(QAxWidget):
    """ QAxWidget를 상속 받은 것, QAxWidget는 Open API를 사용할 수 있도록 연결하는 기능을 제공 """
    def __init__(self):
        super().__init__()
        self._make_kiwoom_instance()    # 설치한 API를 사용할 수 있도록 설정
        self._set_signal_slots()        # 로그인, 실시간 정보, 기타 제공받을 수 있는 데이터에 대한 응답을 받을 수 있는 slot함수들을 등록
        self._comm_connect()            # 로그인 요청 보내기, _login_slot에서 응답을 받음

        self.account_number = self.get_account_number() # 계좌번호 저장

    def _make_kiwoom_instance(self):
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")

    def _set_signal_slots(self):
        """API로 보내는 요청들을 받아올 slot을 등록하는 함수"""
        # 로그인 응답의 결과를 _on_login_connect을 통해 받도록 설정
        self.OnEventConnect.connect(self._login_slot)

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
        print(account_number)
        return account_number

    def get_code_list_by_market(self, market_type): # 주식 시장별 종목 코드 리스트 뽑기 ,market_type은 어떤 시장에서 종목을 얻어 올지 의미하는 구분 값
        code_list = self.dynamicCall("GetCodeListByMarket(QString)", market_type)
        code_list = code_list.split(';')[:-1]   # 마지막 항목에는 ''이 붙어 있으므로 이것을 제외하고 넣기
        return code_list

    def get_master_code_name(self, code): #종목 코드 리스트를 종목명으로 반환
        code_name = self.dynamicCall("GetMasterCodeName(QString)", code)
        return code_name


