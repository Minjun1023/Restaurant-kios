from flask import Flask, request
import json
from json import JSONEncoder
import numpy as np
import os, logging

app = Flask(
    __name__,
    static_url_path='',
    static_folder='./',
)

# 데이터 폴더 경로 설정
data_folder = './data'
order_counter_file = os.path.join(data_folder, 'order_counter.txt')
staff_call_file = os.path.join(data_folder, 'staff_call.json')

# 데이터 폴더가 없으면 생성
if not os.path.exists(data_folder):
    os.makedirs(data_folder)

# 다음 주문 번호 가져오기
def get_next_order_number():
    if not os.path.exists(order_counter_file):
        with open(order_counter_file, 'w') as f:
            f.write('1')
        return 1
    else:
        with open(order_counter_file, 'r') as f:
            current_number = int(f.read())
        next_number = current_number + 1
        with open(order_counter_file, 'w') as f:
            f.write(str(next_number))
        return next_number

# 초기 설정
@app.route('/')
@app.route('/home')
def home():
    return app.send_static_file("./index.html")

# 직원 호출 처리
@app.route('/kiosk_page/callStaff', methods=['POST'])
def callStaff():
    message = request.form["message"]
    # '직원을 호출하였습니다.' 메시지를 저장
    staff_call_data = {
        'order_id': 'staff_call',
        'items': [{'name': '직원을 호출하였습니다.', 'price': 0, 'quantity': 1}],
        'status': 'call'
    }
    with open(staff_call_file, 'w') as f:
        json.dump(staff_call_data, f)
    return outputJSON({"message": message}, "ok")

# 주문 처리
@app.route('/kiosk_page/order', methods=['POST'])
def order():
    logDisable(False)  # 로그 저장

    order_menu = request.form["order"]
    fileSave(order_menu)
    output = {"output": "none"}
    output = json.dumps(output, cls=NumpyArrayEncoder)
    return outputJSON(json.loads(output), "ok")

# 주문 정보 가져오기
@app.route('/kitch_page/getOrder', methods=['POST'])
def getOrder():
    logDisable(True)  # 로그 저장 X

    currentOrder = []
    order_files = [f for f in os.listdir(data_folder) if f.endswith('_order.json') or f == 'staff_call.json']
    for order_file in order_files:
        with open(os.path.join(data_folder, order_file), 'r') as f:
            order_data = json.load(f)
            order_data['order_id'] = str(order_data['order_id'])  # order_id를 문자열로 변환
            currentOrder.append(order_data)
    
    output = {"output": currentOrder}
    output = json.dumps(output, cls=NumpyArrayEncoder)
    return outputJSON(json.loads(output), "ok")

# 결제 처리
@app.route('/kiosk_page/payment', methods=['POST'])
def payment():
    logDisable(False)  # 로그 저장

    order_data = request.json
    total_price = sum(item['price'] * item['quantity'] for item in order_data['items'])

    # 주문 번호 생성
    order_id = get_next_order_number()

    # 주문 정보 저장
    order_info = {
        'order_id': str(order_id),  # order_id를 문자열로 변환
        'items': order_data['items'],
        'total_price': total_price,
        'status': 'paid'
    }
    with open(os.path.join(data_folder, f'{order_id}_order.json'), 'w') as f:
        json.dump(order_info, f)

    output = {"output": "payment successful"}
    output = json.dumps(output, cls=NumpyArrayEncoder)
    return outputJSON(json.loads(output), "ok")

# 요리 완료 처리
@app.route('/kitch_page/completeOrder', methods=['POST'])
def completeOrder():
    logDisable(False)  # 로그 저장

    items_to_delete = request.json.get("items", [])
    for item in items_to_delete:
        order_id, item_name = item.split('-')

        # staff_call.json 파일 삭제 처리
        if order_id == 'staff_call' and item_name == 'deleteStaffCall':
            if os.path.exists(staff_call_file):
                try:
                    os.remove(staff_call_file)
                    print("staff_call.json deleted")  # 디버그 로그
                except Exception as e:
                    print(f"Error deleting staff_call.json: {e}")
        else:
            order_file = os.path.join(data_folder, f'{order_id}_order.json')
            if os.path.exists(order_file):
                try:
                    with open(order_file, 'r') as f:
                        order_data = json.load(f)
                    order_data['items'] = [i for i in order_data['items'] if i['name'] != item_name]
                    if order_data['items']:
                        with open(order_file, 'w') as f:
                            json.dump(order_data, f)
                    else:
                        os.remove(order_file)
                except Exception as e:
                    print(f"Error processing order file {order_file}: {e}")

    output = {"output": "completed"}
    output = json.dumps(output, cls=NumpyArrayEncoder)
    return outputJSON(json.loads(output), "ok")


################################################################################
# 테스트 코드: 참고용
@app.route('/kiosk_page/test', methods=['POST'])
def test():
    output = request.form["name"]
    output = {"output": output}
    output = json.dumps(output, cls=NumpyArrayEncoder)
    return outputJSON(json.loads(output), "ok")

def fileSave(content):
    path = './data'
    if not os.path.exists(path):
        os.makedirs(path)
    with open(f'{path}/{content}.txt', 'w') as f:
        f.write('test-test')

def logDisable(n):
    log = logging.getLogger('werkzeug')
    log.disabled = n

def outputJSON(msg, status="error"):
    return {"data": msg, "status": status}

class NumpyArrayEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return JSONEncoder.default(self, obj)

if __name__ == '__main__':
    app.run(debug=True)
