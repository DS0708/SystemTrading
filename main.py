from api.Kiwoom import *
import sys


app = QApplication(sys.argv)
Kiwoom = Kiwoom()

# kospi_code_list = Kiwoom.get_code_list_by_market("0")
# print(kospi_code_list)
# for code in kospi_code_list:
#     code_name = Kiwoom.get_master_code_name(code)
#     print(code,code_name)
#
# kosdaq_code_list = Kiwoom.get_code_list_by_market("10")
# print(kosdaq_code_list)
# for code in kosdaq_code_list:
#     code_name = Kiwoom.get_master_code_name(code)
#     print(code,code_name)

# 특정 종목 일봉 정보 가져오기 (삼성전자)
# df = Kiwoom.get_price_data("005930")
# print(df)

deposit = Kiwoom.get_deposit()

# 삼성전자 1주 주문하기
# order_result = Kiwoom.send_order('send_buy_order', '1001','1','005930',1,74200,'00')
# print(order_result)

# 그날 주문 정보 self.order 딕셔너리에 저장되는지 확인하기
# 아직 내부적으로 여러 개의 주문 중 마지막 주문으로 덮어쓰도록 구현되어 있는 문제가 있음
orders = Kiwoom.get_order()
print(orders)

app.exec_()

