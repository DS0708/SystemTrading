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

# df = Kiwoom.get_price_data("005930")
# print(df)

deposit = Kiwoom.get_deposit()

app.exec_()

