from flask import Flask, render_template, request, send_file, jsonify
from PyPDF2 import PdfReader, PdfWriter
import os
import tempfile
from werkzeug.utils import secure_filename
import zipfile
import io

app = Flask(__name__, static_folder='static')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()

def split_pdf(input_path, ranges):
    """
    Split a PDF file into multiple files based on page ranges.
    Returns a list of (filename, file_data) tuples.
    """
    output_files = []
    reader = PdfReader(input_path)
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    
    for start, end, file_name in ranges:
        # Adjust for 0-based indexing
        start_idx = start - 1
        end_idx = min(end, len(reader.pages))
        
        if start_idx < 0 or start_idx >= len(reader.pages):
            continue
            
        writer = PdfWriter()
        for page_num in range(start_idx, end_idx):
            writer.add_page(reader.pages[page_num])
        
        # Write to bytes buffer instead of file
        output_buffer = io.BytesIO()
        writer.write(output_buffer)
        output_buffer.seek(0)
        
        filename = f"{file_name}.pdf" if file_name else f"{base_name}_pages_{start}-{end}.pdf"
        output_files.append((filename, output_buffer))
    
    return output_files

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/split', methods=['POST'])
def split():
    if 'pdf_file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['pdf_file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'File must be a PDF'}), 400
    
    # Parse ranges from form data
    ranges_str = request.form.get('ranges', '')

    try:
        # Convert ranges string to list of tuples
        ranges = []
        for range_str in ranges_str.split(','):
            if range_str.strip():
                start, end, file_name = range_str.strip().split('-')
                ranges.append((int(start), int(end), file_name))
    except ValueError:
        return jsonify({'error': 'Invalid range format'}), 400

    
    if not ranges:
        return jsonify({'error': 'No ranges specified'}), 400
    
    try:
        # Save uploaded file temporarily
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Split the PDF
        output_files = split_pdf(filepath, ranges)
        
        # Create zip file containing all split PDFs
        memory_file = io.BytesIO()
        with zipfile.ZipFile(memory_file, 'w') as zf:
            for fname, fdata in output_files:
                zf.writestr(fname, fdata.getvalue())
        
        memory_file.seek(0)
        
        # Clean up
        os.remove(filepath)
        for _, fdata in output_files:
            fdata.close()
        
        return send_file(
            memory_file,
            mimetype='application/zip',
            as_attachment=True,
            download_name='split_pdfs.zip'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)