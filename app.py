"""
PencilSketch AI - Flask Backend
Full-stack image processing server powered by OpenCV and Pillow.
"""

import os
import time
import uuid
from pathlib import Path
from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    send_from_directory,
    abort,
    url_for,
)
from werkzeug.utils import secure_filename
import sketch_engine

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_FOLDER = BASE_DIR / "static" / "uploads"
OUTPUT_FOLDER = BASE_DIR / "output"
PRESET_FOLDER = BASE_DIR / "static" / "presets"

# Ensure essential directories exist
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)
PRESET_FOLDER.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB limit

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = str(UPLOAD_FOLDER)
app.config["OUTPUT_FOLDER"] = str(OUTPUT_FOLDER)
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "pencil-sketch-ai-secret-key-2026")


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def index():
    """Render landing page and workspace studio."""
    return render_template("index.html")


@app.route("/api/presets", methods=["GET"])
def get_presets():
    """Return available preset demo images for instant one-click testing."""
    presets = [
        {
            "id": "portrait",
            "name": "Artistic Portrait",
            "category": "Portrait",
            "description": "Rich facial contours and delicate shading",
            "url": "/static/presets/portrait.jpg",
        },
        {
            "id": "architecture",
            "name": "Classic Architecture",
            "category": "Architecture",
            "description": "Geometric columns, arches, and stone textures",
            "url": "/static/presets/architecture.jpg",
        },
        {
            "id": "landscape",
            "name": "Alpine Mountain & Lake",
            "category": "Nature",
            "description": "Majestic mountain ridges, pine trees, and reflections",
            "url": "/static/presets/landscape.jpg",
        },
    ]
    return jsonify({"success": True, "presets": presets})


@app.route("/upload", methods=["POST"])
def upload_file():
    """
    Handle image upload via file drag-and-drop or preset selection.
    Returns unique file_id and original image URL.
    """
    # 1. Check if user selected a preset
    preset_id = request.form.get("preset_id")
    if preset_id:
        preset_filename = f"{secure_filename(preset_id)}.jpg"
        preset_source = PRESET_FOLDER / preset_filename
        if not preset_source.exists():
            return jsonify({"success": False, "error": f"Preset '{preset_id}' not found."}), 404

        file_id = f"preset_{preset_id}_{uuid.uuid4().hex[:8]}"
        saved_filename = f"{file_id}.jpg"
        target_path = UPLOAD_FOLDER / saved_filename
        
        # Copy preset to upload folder for this session
        with open(preset_source, "rb") as src, open(target_path, "wb") as dst:
            dst.write(src.read())

        return jsonify({
            "success": True,
            "file_id": file_id,
            "filename": saved_filename,
            "original_url": f"/static/uploads/{saved_filename}",
            "is_preset": True,
        })

    # 2. Check if a file was uploaded
    if "image" not in request.files:
        return jsonify({"success": False, "error": "No image file provided in request."}), 400

    file = request.files["image"]
    if file.filename == "":
        return jsonify({"success": False, "error": "No file selected."}), 400

    if not allowed_file(file.filename):
        return jsonify({
            "success": False,
            "error": "Invalid file type. Allowed formats are PNG, JPG, JPEG, and WEBP.",
        }), 400

    orig_ext = file.filename.rsplit(".", 1)[1].lower()
    file_id = f"upload_{uuid.uuid4().hex[:12]}"
    saved_filename = f"{file_id}.{orig_ext}"
    saved_path = UPLOAD_FOLDER / saved_filename

    try:
        file.save(str(saved_path))
        # Validate that Pillow / OpenCV can parse it
        from PIL import Image
        with Image.open(str(saved_path)) as img:
            img.verify()
    except Exception as e:
        if saved_path.exists():
            saved_path.unlink()
        return jsonify({"success": False, "error": f"Uploaded file is corrupted or not a valid image: {str(e)}"}), 400

    return jsonify({
        "success": True,
        "file_id": file_id,
        "filename": saved_filename,
        "original_url": f"/static/uploads/{saved_filename}",
        "is_preset": False,
    })


@app.route("/process", methods=["POST"])
def process_image():
    """
    Process image with OpenCV using specified style and parameter sliders.
    Returns sketch URL and processing time.
    """
    start_time = time.time()
    data = request.get_json(silent=True) or request.form

    file_id = data.get("file_id")
    if not file_id:
        return jsonify({"success": False, "error": "Missing 'file_id' parameter."}), 400

    # Search for original file in uploads matching file_id
    matching_files = list(UPLOAD_FOLDER.glob(f"{file_id}.*"))
    if not matching_files:
        return jsonify({"success": False, "error": "Original image not found. Please upload again."}), 404

    input_path = str(matching_files[0])

    style = data.get("style", "graphite")
    intensity = int(data.get("intensity", 50))
    darkness = int(data.get("darkness", 50))
    detail = int(data.get("detail", 50))

    # Generate unique output filename incorporating parameters for cache safety
    output_filename = f"sketch_{file_id}_{style}_i{intensity}_d{darkness}_dt{detail}.png"
    output_path = str(OUTPUT_FOLDER / output_filename)

    try:
        # Check if already cached
        if not os.path.exists(output_path):
            sketch_engine.process_sketch(
                image_path=input_path,
                output_path=output_path,
                style=style,
                intensity=intensity,
                darkness=darkness,
                detail=detail,
            )

        elapsed_ms = int((time.time() - start_time) * 1000)

        return jsonify({
            "success": True,
            "sketch_url": f"/output/{output_filename}",
            "filename": output_filename,
            "style": style,
            "intensity": intensity,
            "darkness": darkness,
            "detail": detail,
            "processing_time_ms": elapsed_ms,
        })
    except Exception as e:
        return jsonify({"success": False, "error": f"Image processing failed: {str(e)}"}), 500


@app.route("/output/<path:filename>")
def serve_output(filename: str):
    """Serve generated sketch files from the output folder."""
    return send_from_directory(str(OUTPUT_FOLDER), filename)


@app.route("/download", methods=["GET"])
def download_sketch():
    """
    Download route: supports downloading the sketch image or a side-by-side comparison image.
    Params:
      filename: generated sketch filename (e.g. sketch_xxx.png)
      mode: 'sketch' or 'comparison'
    """
    filename = request.args.get("filename")
    mode = request.args.get("mode", "sketch")

    if not filename:
        abort(400, description="Filename parameter is required.")

    filename = secure_filename(filename)
    sketch_path = OUTPUT_FOLDER / filename
    if not sketch_path.exists():
        abort(404, description="Requested sketch file was not found.")

    if mode == "comparison":
        # Extract file_id from filename pattern: sketch_<file_id>_<style>_...
        parts = filename.split("_")
        if len(parts) >= 3:
            file_id = f"{parts[1]}_{parts[2]}" if parts[1] == "preset" else parts[1]
            matching_originals = list(UPLOAD_FOLDER.glob(f"{file_id}.*"))
            if matching_originals:
                orig_path = str(matching_originals[0])
                comp_filename = f"comparison_{filename}"
                comp_path = str(OUTPUT_FOLDER / comp_filename)

                if not os.path.exists(comp_path):
                    sketch_engine.create_comparison_image(orig_path, str(sketch_path), comp_path)

                return send_from_directory(
                    str(OUTPUT_FOLDER),
                    comp_filename,
                    as_attachment=True,
                    download_name=f"PencilSketch_AI_Before_After.png",
                )

    # Standard sketch download
    return send_from_directory(
        str(OUTPUT_FOLDER),
        filename,
        as_attachment=True,
        download_name=f"PencilSketch_AI_{filename}",
    )


@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({"success": False, "error": "File exceeds the 16MB maximum size limit."}), 413


if __name__ == "__main__":
    # Ensure demo presets are created if not present
    if not (PRESET_FOLDER / "portrait.jpg").exists():
        import generate_presets
        generate_presets.main()

    port = int(os.environ.get("PORT", 5000))
    print(f"\n==========================================")
    print(f" PencilSketch AI Server Running on http://127.0.0.1:{port}")
    print(f"==========================================\n")
    app.run(host="0.0.0.0", port=port, debug=True)
