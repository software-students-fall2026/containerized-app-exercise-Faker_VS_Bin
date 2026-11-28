from flask import Flask, render_template

app = Flask(__name__)


@app.get("/")
def upload_receipt():
    return render_template("upload.html")