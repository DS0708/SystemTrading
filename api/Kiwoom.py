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


