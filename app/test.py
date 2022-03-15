from flask import Flask
from prometheus_flask_exporter import PrometheusMetrics

app = Flask(__name__)
metrics = PrometheusMetrics(app, default_labels={"zone_id": "ru-central1-b"})

metrics.info('app_info', 'Application info', version='1.0.3')

@app.route('/')
def main():
    return 'OK'

app.run(debug=True, host='0.0.0.0', port=5000)
