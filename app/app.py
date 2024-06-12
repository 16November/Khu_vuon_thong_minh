import time
import uuid
from flask import Flask, render_template, request, redirect, url_for, flash, session,jsonify
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_restful import Api, Resource, reqparse
import os
from tensorflow.keras.preprocessing import image
from tensorflow.keras.models import load_model


import requests
from models import UserModel, db  # Import đối tượng db từ models.py
from flask_wtf.csrf import CSRFProtect
import tensorflow as tf
import numpy as np

app = Flask(__name__)
api = Api(app)
csrf = CSRFProtect(app)
app.config['SECRET_KEY'] = 'your_secret_key'
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'instance', 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
esp32_cam_ip = '192.168.111.181'
# Liên kết đối tượng db với ứng dụng Flask
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)

# UserRegister reqparse 
user_register = reqparse.RequestParser()
user_register.add_argument('username', type=str, required=True, help='Username is required', location='form')
user_register.add_argument('password', type=str, required=True, help='Password is required', location='form')
user_register.add_argument('email', type=str, help='Email', location='form')
user_register.add_argument('name', type=str, help='Name', location='form')

# UserLogin reqparse
user_login = reqparse.RequestParser()
user_login.add_argument('username', type=str, required=True, help='Username is required', location='form')
user_login.add_argument('password', type=str, required=True, help='Password is required', location='form')

@login_manager.user_loader
def load_user(username):
    return UserModel.get(username)

# Xử lý Login (Resource)
class Login(Resource):
    def post(self):
        args = user_login.parse_args()
        username = args['username']
        password = args['password']
        user = UserModel.query.filter_by(username=username).first()
        if user and user.verify_password(password):
            login_user(user)
            print ('Login successful')
            return redirect(url_for('information'))
        else :
            print("Login Failed: Incorrect username or password")
            flash("Login Failed: Incorrect username or password")
            return redirect(url_for('home'))
        
        

# Xử lý Register 
class Register(Resource):
    def post(self):
        args = user_register.parse_args()
        username = args['username']
        password = args['password']
        email = args['email']
        name = args['name']
        user = UserModel.query.filter_by(username=username).first()
        if user:
            print({"Message": "Register Failed: Username already exists"}, 401)
            flash("Register Failed: Username already exists")
            return redirect(url_for('register_view'))
        
        else:
            user_add = UserModel(
                username=username,
                email=email,
                name=name
            )
            user_add.set_password(password)  # Sử dụng phương thức set_password để băm mật khẩu
            db.session.add(user_add)
            db.session.commit()
            print({"Message": "Register Successfully"}, 200)
            return redirect(url_for('home'))
        

#Handle logout       
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("you have been logged out")
    return redirect(url_for('home'))

# Home route
@app.route('/', endpoint = 'home', methods = ['POST','GET'])
def home():
    return render_template('login.html')

#Load registerform
@app.route('/register')
def register_view():
    return render_template('register.html')

# Render Information Template
@app.route('/information')
def information():
    info = {'temperature': None, 'humidity': None, 'soilhumidity1': None, 'soilhumidity2': None, 'soilhumidity3': None}
    return render_template('Information.html', info=info)


#Render Control Template
@app.route('/control_view')
def control_view():
    status_start()
    return render_template('control.html',session=session)


#Redirect form
@app.route('/redirect_form', methods= ['GET', 'POST'])
def redirect_form():
    if request.method == 'GET':
        action= request.args.get('action')
        if action == 'info':
            print("chuyen form info sucess")
            return redirect(url_for('information'))
        elif action == 'control':
            print("chuyen form control sucess")
            return redirect(url_for('control_view'))

# Create Status
def status_start():
    data = send_and_receive_data()
    if data is None:
        if 'pump' not in session:
            session['pump'] = {
            "pump1_status": "Tắt",
            "pump2_status": "Tắt",
            "pump3_status": "Tắt",
            "pump4_status": "Tắt",
            "pump5_status": ""
            }
    else :

        if data[0] == '0':
            pump1_status = "Tắt";
        elif data[0] == '1':
            pump1_status = "Bật";  
        
        if data[1] == '0':
            pump2_status = "Tắt";
        elif data[1] == '1':
            pump2_status = "Bật";
        
        if data[2] == '0':
            pump3_status = "Tắt";
        elif data[2] == '1':
            pump3_status = "Bật";
        
        if data[3] == '0':
            pump4_status = "Tắt";
        elif data[3] == '1':
            pump4_status = "Bật";   
        
        if data[9] == '1':
            pump5_status = "1";
        elif data[9] == '2':
            pump5_status = "2";
        elif data[9] == '3':
            pump5_status = "3";
        if 'pump' not in session:
            session['pump'] = {
                "pump1_status": pump1_status,
                "pump2_status": pump2_status,
                "pump3_status": pump3_status,
                "pump4_status": pump4_status,
                "pump5_status": pump5_status
            }

# Update Status
def update_status(key, value):
    # Lấy giá trị hiện tại của session
    pumps = session['pump']
    # Cập nhật giá trị mới
    pumps[key] = value
    # Lưu lại giá trị mới vào session
    session['pump'] = pumps
    # Trả về giá trị đã được cập nhật (không cần thiết trong trường hợp này

@app.route('/control_device', methods=['GET'], endpoint='control_device')
def control_device():
    pump_status = request.args.get('Pump')
    if pump_status in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', '1', '2', '3']:
        if pump_status == 'A':
            session['pump']['pump4_status'] = 'Bật'
            print(pump_status)
        elif pump_status == 'B':
            session['pump']['pump4_status'] = 'Tắt'
            print(pump_status)
        elif pump_status == 'C':
            session['pump']['pump1_status'] = 'Bật'
            print(pump_status)
        elif pump_status == 'D':
            session['pump']['pump1_status'] = 'Tắt'
            print(pump_status)
        elif pump_status == 'E':
            session['pump']['pump2_status'] = 'Bật'
            print(pump_status)
        elif pump_status == 'F':
            session['pump']['pump2_status'] = 'Tắt'
            print(pump_status)
        elif pump_status == 'G':
            session['pump']['pump3_status'] = 'Bật'
            print(pump_status)
        elif pump_status == 'H':
            session['pump']['pump3_status'] = 'Tắt'
            print(pump_status)
        elif pump_status == '1':
            session['pump']['pump5_status'] = '1'
            print(pump_status)
        elif pump_status == '2':
            session['pump']['pump5_status'] = '2'
            print(pump_status)
        elif pump_status == '3':
            session['pump']['pump5_status'] = '3'
            print(pump_status)
        
        # send_data_to_esp32(pump_status)
        session.modified = True

        # Trả về phản hồi với giá trị cập nhật
        return jsonify(session['pump'])

    # Trả về phản hồi mặc định
    return jsonify({"status": "Ok"}), 200

#Gửi data to ESP32 cam 
def send_data_to_esp32(text):
    
    send_data_url = f'http://{esp32_cam_ip}/send'#HTTP 
    try:
        response = requests.get(send_data_url, params={'text': text})
        if response.status_code == 200:
            print("Data sent and received by ESP32-CAM:", response.text)
        else:
            print("Failed to send data. Status code:", response.status_code)
    except requests.exceptions.RequestException as e:
        print("Error:", e)
   
def send_and_receive_data():
    update_url = f'http://{esp32_cam_ip}/update'
    try:
        response = requests.get(update_url, params={'text':'dummy'})
        if response.status_code == 200:
            # print("Data sent and received by ESP32-CAM:", response.text)
            data = response.text.split(',')
            # print(data)
            return data
        else:
            print("Failed to send data. Status code:", response.status_code)
            return None
    except requests.exceptions.RequestException as e:
        print("Error:", e)

# Model AI dự đoán 
#Load model
model = tf.keras.models.load_model('D:/Code VSCode/Python/PBL5/app/PBL05.h5')

def predict(image_path):
    try:
        # Load the image and preprocess it
        img = image.load_img(image_path, target_size=(128, 128))  # Điều chỉnh target_size theo nhu cầu
        img_array = image.img_to_array(img)
        img_array = np.expand_dims(img_array, axis=0)
        # Thực hiện dự đoán
        prediction = model.predict(img_array)

        # Chuyển dự đoán thành định dạng đọc được
        predicted_class = prediction.argmax(axis=-1)

        # Giả sử bạn có một danh sách tên lớp
        class_names = ['Healthy', 'Multiple_diseases', 'Yellow']  # Cập nhật với tên lớp thực tế của bạn
        predicted_label = class_names[predicted_class[0]]
        print(predicted_label)
        return predicted_label
    except Exception as e:
        return str(e)  # Chuyển lỗi thành chuỗi

# Đảm bảo thư mục lưu trữ hình ảnh tồn tại
UPLOAD_FOLDER = os.path.join(app.root_path, 'static/images')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/upload_predict', methods=['GET'])
def upload_predict():
    action = request.args.get('action')
    if action == 'upload':
        url = f'http://{esp32_cam_ip}/saved-photo'
        take_photo = f'http://{esp32_cam_ip}/capture'

        requests.get(take_photo)
        time.sleep(10)
        response2 = requests.get(url)
        if response2.status_code == 200:
            image_filename = f'esp32_cam_image_{uuid.uuid4().hex}.jpg'
            image_path = os.path.join(UPLOAD_FOLDER, image_filename)
            print(image_path)
            with open(image_path, 'wb') as f:
                f.write(response2.content)
            image_url = f'/static/images/{image_filename}'
            print(image_url)
            return jsonify({"image_url": image_url}) 
        else:
            return jsonify({"error": "Không thể nhận ảnh từ ESP32-CAM"}), 400
    elif action == 'predict':
        image_url = request.args.get('image_url')
        if image_url.startswith('http://127.0.0.1:5000'):
            image_url = image_url.replace('http://127.0.0.1:5000', '')
        image_path = os.path.join(app.root_path, image_url.strip('/'))
        
        # Chuyển URL thành đường dẫn tệp cục bộ trước khi truyền vào hàm predict
        prediction = predict(image_path)
        return jsonify({"prediction": prediction})

#Handle Information
@app.route('/update_info', methods=['GET', 'POST'], endpoint='update_info')
def update_info():
    if request.method == 'GET':
        data = send_and_receive_data();
        if data is None:
            info = {
            "temperature":"None",
            "humidity":"None",
            "soilhumidity1":"None",
            "soilhumidity2":"None",
            "soilhumidity3":"None"
            }
        else :
            info={
            "temperature":data[8],
            "humidity":data[7],
            "soilhumidity1":data[4],
            "soilhumidity2":data[5],
            "soilhumidity3":data[6]
            }
        return jsonify(info)
    else :
        return render_template('Information.html')
    
api.add_resource(Login, '/api/login', endpoint = 'login')
api.add_resource(Register, '/api/register', endpoint='register_user')

# # Đảm bảo thư mục instance tồn tại
# if not os.path.exists(os.path.join(basedir, 'instance')):
#     os.makedirs(os.path.join(basedir, 'instance'))

# # Tạo cơ sở dữ liệu nếu nó không tồn tại
# with app.app_context():
#     db.create_all()
#     print("created database successfully")

if __name__ == "__main__":
    # send_and_receive_data()
    app.run(debug=True)
