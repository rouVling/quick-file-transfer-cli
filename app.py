from flask import Flask, request, send_from_directory, abort
import argparse
import os
import time
import hashlib

from werkzeug.utils import secure_filename

app = Flask(__name__)

parser = argparse.ArgumentParser(description="跨平台传文件小工具")
parser.add_argument("--port", type=int, default=9963, help="端口号")
parser.add_argument("--host", type=str, default="0.0.0.0", help="主机地址")
parser.add_argument("--base_dir", type=str, help="文件保存路径")
parser.add_argument("--prefix", type=str, help="安全访问前缀")

args = parser.parse_args()

base_dir = args.base_dir

if not os.path.exists(base_dir):
    os.makedirs(base_dir)

def auth(token):
    current_time = str(int(time.time()))[:-1]
    correct_token = hashlib.sha256((args.prefix + current_time).encode()).hexdigest()
    return token == correct_token

@app.route("/upload", methods=["POST"])
def upload():
    if not auth(request.headers.get("Authorization")):
        abort(403, "Invalid or expired password")
    print("enter upload")
    if "file" not in request.files:
        print("No file part")
        abort(400, "No file part")
    print("file in request.files")
    file = request.files["file"]
    if file.filename == "":
        print("No selected file")
        abort(400, "No selected file")

    if file:
        filename = secure_filename(file.filename)
        file.save(os.path.join(base_dir, filename))
        return "upload success", 200
    else:
        print("upload failed")
        abort(400, "upload failed")


@app.route("/download/<filename>", methods=["GET"])
def download(filename):
    if not auth(request.headers.get("Authorization")):
        abort(403, "Invalid or expired password")
    try:
        return send_from_directory(base_dir, filename, as_attachment=True)
    except FileNotFoundError:
        abort(404, "File not found")


@app.route(
    "/remove/<filename>", methods=["POST"]
)  # in this function, download first, and then remove
def download_and_remove(filename):
    if not auth(request.headers.get("Authorization")):
        abort(403, "Invalid or expired password")
    try:
        # return send_from_directory(
        #     base_dir, filename, as_attachment=True
        # ), lambda response: response.delete_cookie(filename) or os.remove(
        #     os.path.join(base_dir, filename)
        # )

        # file = send_from_directory(base_dir, filename, as_attachment=True)
        os.remove(os.path.join(base_dir, filename))
        return "remove success", 200
        # return file
        # code above will send a empty file

    except FileNotFoundError:
        abort(404, "File not found")

# @app.route("/test", methods=["GET"])
# def test():
#     current_time = str(int(time.time()))[:-1]
#     token = hashlib.sha256((args.prefix + current_time).encode()).hexdigest()
#     print("token: ", token)
#     print("auth:  ", request.headers.get('Authorization'))
#     if token == request.headers.get('Authorization'):
#         return "success", 200
#     else:
#         return "failed", 403

if __name__ == "__main__":
    app.run(host=args.host, port=args.port)
