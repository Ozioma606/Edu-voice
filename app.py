from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
from pathlib import Path
from course_audio_processor import CourseAudioProcessor

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = './uploads'
OUTPUT_FOLDER = './outputs'
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'pptx', 'txt'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'message': 'EduVoice API is running'})

@app.route('/api/upload', methods=['POST'])
def upload_file():
    print("\n" + "="*60)
    print("📤 UPLOAD REQUEST RECEIVED")
    print("="*60)
    
    if 'file' not in request.files:
        print("❌ No file in request")
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    print(f"📎 File object: {file}")
    print(f"📎 Filename: {file.filename}")
    
    if file.filename == '':
        print("❌ Empty filename")
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        print(f"❌ Invalid file type: {file.filename}")
        return jsonify({'error': 'Invalid file type'}), 400
    
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    print(f"💾 Saving file to: {file_path}")
    file.save(file_path)
    
    # Verify file was saved
    if os.path.exists(file_path):
        file_size = os.path.getsize(file_path)
        print(f"✅ File saved successfully!")
        print(f"   Path: {file_path}")
        print(f"   Size: {file_size} bytes")
    else:
        print(f"❌ File was NOT saved!")
        return jsonify({'error': 'File save failed'}), 500
    
    try:
        explanation_level = request.form.get('explanationLevel', 'intermediate')
        print(f"🎓 Explanation level: {explanation_level}")
        
        processor = CourseAudioProcessor(
            explanation_level=explanation_level,
            voice='default',
            speed=1.0,
            engine='gtts'
        )
        
        output_dir = os.path.join(OUTPUT_FOLDER, Path(filename).stem)
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"🎯 Output directory: {output_dir}")
        print(f"🚀 Starting processing...")
        print(f"📄 Processing THIS file: {file_path}")
        print("="*60)
        
        # THIS IS THE KEY LINE - make sure we pass the CORRECT file path
        result = processor.process_document(file_path, output_dir)
        
        if result['success']:
            print("\n" + "="*60)
            print("✅ SUCCESS - Sending response to client")
            print("="*60)
            return jsonify({
                'success': True,
                'message': 'Processing complete',
                'data': {
                    'audioFile': os.path.basename(result['audio_file']),
                    'transcriptFile': os.path.basename(result['transcript_file']),
                    'paragraphsProcessed': result['paragraphs_processed'],
                    'outputDir': os.path.basename(output_dir)
                }
            })
        else:
            return jsonify({'error': 'Processing failed'}), 500
    
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    
    finally:
        # Clean up uploaded file
        if os.path.exists(file_path):
            print(f"🗑️  Cleaning up: {file_path}")
            os.remove(file_path)

@app.route('/api/download/audio/<output_dir>', methods=['GET'])
def download_audio(output_dir):
    audio_file = os.path.join(OUTPUT_FOLDER, output_dir, 'course_material_complete.mp3')
    print(f"📥 Download request for: {audio_file}")
    if os.path.exists(audio_file):
        return send_file(audio_file, mimetype='audio/mpeg', as_attachment=True, download_name='course_audio.mp3')
    return jsonify({'error': 'Audio file not found'}), 404

@app.route('/api/download/transcript/<output_dir>', methods=['GET'])
def download_transcript(output_dir):
    transcript_file = os.path.join(OUTPUT_FOLDER, output_dir, 'transcript.txt')
    print(f"📥 Download request for: {transcript_file}")
    if os.path.exists(transcript_file):
        return send_file(transcript_file, mimetype='text/plain', as_attachment=True, download_name='transcript.txt')
    return jsonify({'error': 'Transcript file not found'}), 404

if __name__ == '__main__':
    print("="*60)
    print("🎧 EDUVOICE API SERVER")
    print("="*60)
    print("API available at: http://localhost:5000")
    print("Upload folder: " + os.path.abspath(UPLOAD_FOLDER))
    print("Output folder: " + os.path.abspath(OUTPUT_FOLDER))
    print("="*60 + "\n")
    app.run(debug=True, host='0.0.0.0', port=5000)

