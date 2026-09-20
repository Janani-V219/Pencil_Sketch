"""
Integration Test Suite for PencilSketch AI Flask application.
Tests all endpoints: routes, upload, process, download, presets, error handling.
"""

import io
import json
import unittest
from PIL import Image
import numpy as np
from app import app


class PencilSketchTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_01_index_page(self):
        """Test landing page renders with 200 OK."""
        response = self.app.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"PencilSketch", response.data)
        self.assertIn(b"Realistic Graphite", response.data)

    def test_02_presets_endpoint(self):
        """Test /api/presets returns the 3 demo presets."""
        response = self.app.get("/api/presets")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data["success"])
        self.assertEqual(len(data["presets"]), 3)

    def test_03_preset_upload(self):
        """Test uploading via preset_id."""
        response = self.app.post("/upload", data={"preset_id": "portrait"})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data["success"])
        self.assertTrue(data["is_preset"])
        self.assertIn("portrait", data["file_id"])

    def test_04_file_upload(self):
        """Test uploading a synthetic test image."""
        # Create a small in-memory image
        img = Image.new("RGB", (200, 200), color=(180, 120, 90))
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="JPEG")
        img_bytes.seek(0)

        response = self.app.post(
            "/upload",
            data={"image": (img_bytes, "test_photo.jpg")},
            content_type="multipart/form-data",
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data["success"])
        self.assertFalse(data["is_preset"])
        return data["file_id"]

    def test_05_process_sketch_all_styles(self):
        """Test processing with various styles and slider adjustments."""
        # First upload
        file_id = self.test_04_file_upload()

        styles = ["graphite", "soft", "dark", "charcoal", "detailed"]
        for s in styles:
            response = self.app.post(
                "/process",
                json={
                    "file_id": file_id,
                    "style": s,
                    "intensity": 65,
                    "darkness": 70,
                    "detail": 45,
                },
            )
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertTrue(data["success"])
            self.assertEqual(data["style"], s)
            self.assertIn("sketch_url", data)

    def test_06_download_sketch_and_comparison(self):
        """Test downloading generated sketch and side-by-side comparison."""
        file_id = self.test_04_file_upload()
        proc_resp = self.app.post(
            "/process",
            json={"file_id": file_id, "style": "graphite", "intensity": 50, "darkness": 50, "detail": 50},
        )
        proc_data = json.loads(proc_resp.data)
        filename = proc_data["filename"]

        # Download sketch
        dl_sketch = self.app.get(f"/download?filename={filename}&mode=sketch")
        self.assertEqual(dl_sketch.status_code, 200)
        self.assertEqual(dl_sketch.content_type, "image/png")

        # Download comparison
        dl_comp = self.app.get(f"/download?filename={filename}&mode=comparison")
        self.assertEqual(dl_comp.status_code, 200)
        self.assertEqual(dl_comp.content_type, "image/png")


if __name__ == "__main__":
    unittest.main()
