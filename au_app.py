from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import importlib
import threading
import time

# Flask-приложение
app = Flask(__name__)
CORS(app)  # Для взаимодействия с фронтендом

# Конфигурация базы данных
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:1234567@localhost:5432/postgres'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Таблица настроек
class Setting(db.Model):
    __tablename__ = 'settings'
    __table_args__ = {'schema': 'aurum'}  # Указание схемы aurum
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(255), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50), nullable=False)
    group_name = db.Column(db.String(255), default=None)
    updated_at = db.Column(db.TIMESTAMP, default=db.func.now(), onupdate=db.func.now())
    description = db.Column(db.Text, default=None)

# Глобальный реестр запущенных модулей
running_modules = {}

# Функция-оболочка для запуска модулей
def run_module(module_name):
    try:
        module = importlib.import_module(module_name)
        if hasattr(module, module_name):
            module_function = getattr(module, module_name)
            running_modules[module_name]["status"] = "running"

            # Передаем флаг остановки в функцию модуля
            stop_flag = running_modules[module_name]["stop_flag"]
            module_function(stop_flag)
        else:
            running_modules[module_name]["status"] = "error"
    except Exception as e:
        print(f"Ошибка при запуске модуля {module_name}: {e}")
        running_modules[module_name]["status"] = "error"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if request.method == 'GET':
        settings = Setting.query.all()
        data = [{"id": s.id, "key": s.key, "value": s.value, "type": s.type, "group_name": s.group_name, "description": s.description} for s in settings]
        return jsonify(data)

    if request.method == 'POST':
        data = request.json
        setting = Setting.query.get(data["id"])
        if not setting:
            return jsonify({"error": "Setting not found"}), 404

        # Валидация типа данных
        if setting.type == "integer":
            try:
                int(data["value"])
            except ValueError:
                return jsonify({"error": "Invalid value for type 'integer'"}), 400
        elif setting.type == "boolean":
            if data["value"].lower() not in ["true", "false"]:
                return jsonify({"error": "Invalid value for type 'boolean'"}), 400
        elif setting.type == "json":
            try:
                import json
                json.loads(data["value"])
            except ValueError:
                return jsonify({"error": "Invalid value for type 'json'"}), 400

        # Обновление значения в таблице
        setting.value = data["value"]
        db.session.commit()
        return jsonify({"message": "Setting updated successfully"})

@app.route('/modules', methods=['GET'])
def modules():
    core_modules = Setting.query.filter_by(group_name='core').all()
    data = [{"id": m.id, "key": m.key, "value": m.value, "status": running_modules.get(m.key, {}).get("status", "stopped")} for m in core_modules]
    return jsonify(data)

@app.route('/modules/<module_name>/<action>', methods=['POST'])
def module_action(module_name, action):
    if action == "start":
        if module_name in running_modules and running_modules[module_name]["status"] == "running":
            return jsonify({"message": "Module already running"}), 400

        stop_flag = threading.Event()  # Флаг для остановки потока
        running_modules[module_name] = {"thread": None, "status": "starting", "stop_flag": stop_flag}
        thread = threading.Thread(target=run_module, args=(module_name,), daemon=True)
        running_modules[module_name]["thread"] = thread
        thread.start()
        return jsonify({"message": f"Module {module_name} started successfully"})

    elif action == "stop":
        if module_name not in running_modules or running_modules[module_name]["status"] != "running":
            return jsonify({"message": "Module not running"}), 400

        # Устанавливаем флаг остановки
        running_modules[module_name]["stop_flag"].set()
        running_modules[module_name]["status"] = "stopped"
        return jsonify({"message": f"Module {module_name} stopped successfully"})

    return jsonify({"error": "Invalid action"}), 400


if __name__ == '__main__':
    # Создаем контекст приложения для корректной работы с базой данных
    with app.app_context():
        db.create_all()  # Создаем таблицы в базе данных
    app.run(debug=True)
