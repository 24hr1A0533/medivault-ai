from flask import Flask, request, jsonify
from inference import load_models, predict_diabetes_risk, predict_cardio_risk

app = Flask(__name__)

# Security flaw: Eager loading on import without sandbox or error containment
load_models()

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'service': 'disease-prediction'})

@app.route('/predict/diabetes', methods=['POST'])
def predict_diabetes():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Missing JSON body'}), 400
    try:
        # Flaw: No Pydantic validation; will raise unhandled 500 on missing or invalid types
        result = predict_diabetes_risk(data)
        return jsonify(result)
    except KeyError as e:
        return jsonify({'error': f'Missing required feature: {str(e)}'}), 422
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/predict/cardio', methods=['POST'])
def predict_cardio():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Missing JSON body'}), 400
    try:
        result = predict_cardio_risk(data)
        return jsonify(result)
    except KeyError as e:
        return jsonify({'error': f'Missing required feature: {str(e)}'}), 422
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(port=8001, debug=True)
