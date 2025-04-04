import os
from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename
from PIL import Image
import numpy as np
from datetime import datetime

app = Flask(__name__, static_folder='static', template_folder='templates')

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

class DiseaseModel:
    def __init__(self):
        self.disease_db = {
            'rice': ['Healthy', 'Bacterial Blight', 'Leaf Smut', 'Brown Spot'],
            'wheat': ['Healthy', 'Rust', 'Powdery Mildew', 'Fusarium Head Blight'],
            'corn': ['Healthy', 'Common Rust', 'Gray Leaf Spot', 'Northern Leaf Blight'],
            'poultry': ['Healthy', 'Newcastle Disease', 'Avian Influenza', 'Infectious Bronchitis'],
            'cattle': ['Healthy', 'Foot and Mouth', 'Lumpy Skin', 'Blackleg']
        }
    
    def predict(self, image_path, crop_type):
        try:
            diseases = self.disease_db.get(crop_type, ['Healthy'])
            preds = np.random.dirichlet(np.ones(len(diseases)), size=1)[0]
            pred_idx = np.argmax(preds)
            
            return {
                'diagnosis': diseases[pred_idx],
                'confidence': round(float(preds[pred_idx]) * 100, 2),
                'all_predictions': dict(zip(diseases, preds))
            }
        except Exception as e:
            print(f"Prediction error: {e}")
            return {
                'diagnosis': 'Error',
                'confidence': 0.0,
                'all_predictions': {}
            }

model = DiseaseModel()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_recommendations(diagnosis, crop_type):
    recommendations_db = {
        'rice': {
            'Bacterial Blight': 'Apply copper-based fungicides, remove infected plants, ensure proper drainage',
            'Leaf Smut': 'Use resistant varieties, practice crop rotation, apply appropriate fungicides',
            'Brown Spot': 'Apply fungicides containing azoxystrobin, improve field drainage'
        },
        'poultry': {
            'Newcastle Disease': 'Isolate infected birds, vaccinate healthy flock, maintain strict biosecurity',
            'Avian Influenza': 'Immediate reporting to authorities, culling of infected birds, strict quarantine'
        },
        'cattle': {
            'Foot and Mouth': 'Quarantine infected animals, disinfect premises, report to veterinary authorities',
            'Lumpy Skin': 'Vaccination, insect control, supportive care for infected animals'
        }
    }
    
    if diagnosis == 'Healthy':
        return 'No signs of disease detected. Continue with good agricultural practices.'
    
    return recommendations_db.get(crop_type, {}).get(diagnosis, 
        'Consult your local agricultural extension officer or veterinarian for specific guidance.')

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/diagnose', methods=['POST'])
def diagnose():
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type'}), 400
    
    try:

        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        farmer_id = request.form.get('farmerId', 'Unknown')
        location = request.form.get('location', 'Unknown')
        crop_type = request.form.get('cropType', '')
        symptoms_desc = request.form.get('symptomsDesc', '')
        
        img = Image.open(filepath)
        img = img.resize((256, 256))
        
        prediction = model.predict(filepath, crop_type)
        
        requires_expert = prediction['confidence'] < 70 or any(
            disease in prediction['diagnosis'] for disease in 
            ['Influenza', 'Foot and Mouth', 'Newcastle']
        )
        
        recommendations = get_recommendations(prediction['diagnosis'], crop_type)
        
        response = {
            'status': 'success',
            'diagnosis': prediction['diagnosis'],
            'confidence': prediction['confidence'],
            'recommendations': recommendations,
            'requires_expert': requires_expert,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/api/reports', methods=['GET'])
def get_reports():
    sample_reports = [
        {
            'date': '2025-03-15',
            'type': 'Rice',
            'diagnosis': 'Bacterial Blight',
            'status': 'Self-Treatable'
        },
        {
            'date': '2025-04-03',
            'type': 'Poultry',
            'diagnosis': 'Newcastle Disease',
            'status': 'Expert Notified'
        }
    ]
    return jsonify({'reports': sample_reports})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)