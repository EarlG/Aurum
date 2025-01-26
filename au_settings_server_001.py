from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Инициализация приложения
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:1234567@localhost:5432/postgres'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Модель таблицы настроек
class Setting(db.Model):
    __tablename__ = 'settings'
    __table_args__ = {'schema': 'aurum'}  # Указание схемы
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(255), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50), nullable=False)
    group_name = db.Column(db.String(255), default=None)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    description = db.Column(db.Text, default=None)

# Эндпоинт для получения всех настроек
@app.route('/api/settings', methods=['GET'])
def get_settings():
    settings = Setting.query.all()
    return jsonify([
        {
            'id': s.id,
            'key': s.key,
            'value': s.value,
            'type': s.type,
            'group_name': s.group_name,
            'updated_at': s.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
            'description': s.description
        }
        for s in settings
    ])

# Эндпоинт для обновления значения настройки
@app.route('/api/settings/<int:setting_id>', methods=['PUT'])
def update_setting(setting_id):
    data = request.json
    setting = Setting.query.get(setting_id)

    if not setting:
        return jsonify({'error': 'Setting not found'}), 404

    # Проверка типа данных
    if setting.type == 'integer':
        try:
            int(data['value'])
        except ValueError:
            return jsonify({'error': 'Invalid value type for integer'}), 400
    elif setting.type == 'boolean':
        if data['value'] not in ['true', 'false', True, False]:
            return jsonify({'error': 'Invalid value type for boolean'}), 400
    elif setting.type == 'json':
        try:
            import json
            json.loads(data['value'])
        except ValueError:
            return jsonify({'error': 'Invalid JSON value'}), 400

    # Обновление значения
    setting.value = data['value']
    db.session.commit()
    return jsonify({'message': 'Setting updated successfully'})

# Маршрут для рендеринга веб-страницы
@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    # app.run(debug=True)
    app.run(host='0.0.0.0', port=5000, debug=True)
