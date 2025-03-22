from flask import Flask, jsonify, request

# Инициализация приложения Flask
app = Flask(__name__)

# Главная страница
@app.route('/')
def home():
    return "Hello, Flask!"

# Пример API-эндпоинта
@app.route('/api', methods=['GET'])
def api():
    return jsonify({"message": "Hello, this is an API response!"})

# Пример с параметром в URL
@app.route('/greet/<name>', methods=['GET'])
def greet(name):
    return jsonify({"greeting": f"Hello, {name}!"})

# Пример обработки POST-запроса
@app.route('/api/data', methods=['POST'])
def post_data():
    data = request.json  # Получаем JSON из тела запроса
    return jsonify({"received_data": data}), 201

# Запуск приложения
if __name__ == '__main__':
    app.run(debug=True)
