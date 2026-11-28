"""Flask pages for receipt upload and preview."""

from flask import Flask, render_template

app = Flask(__name__)


@app.get("/")
def upload_receipt():
    """Render the receipt upload and preview page."""
    return render_template("upload.html")
