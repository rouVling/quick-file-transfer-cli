from flask import Flask, request, send_from_directory, abort, render_template, jsonify
import argparse
import os
import time
import hashlib
import re
from werkzeug.utils import secure_filename as werkzeug_secure_filename

# from werkzeug.utils import secure_filename


def secure_filename(filename) -> str:
    if isinstance(filename, str):
        from unicodedata import normalize

        filename = normalize("NFKD", filename).encode("utf-8", "ignore")  # 转码
        filename = filename.decode("utf-8")  # 解码
    for sep in os.path.sep, os.path.altsep:
        if sep:
            filename = filename.replace(sep, " ")

    # 正则增加对汉字的过滤	\u4E00-\u9FBF	中文
    # 自定义构建新正则
    _filename_ascii_add_strip_re = re.compile(r"[^A-Za-z0-9_\u4E00-\u9FBF.-]")

    # 使用正则
    # 根据文件名中的空字符，包括空格、换行(\n)、制表符(\t)等，把文件名分割成列表，然后使用下划线“_”进行连接，再过滤掉正则之外的字符，最后去掉字符串两头的“._”字符，最终生成新的文件名
    filename = str(
        _filename_ascii_add_strip_re.sub("", "_".join(filename.split()))
    ).strip("._")

    return filename


app = Flask(__name__)

parser = argparse.ArgumentParser(description="跨平台传文件小工具")
parser.add_argument("--port", type=int, default=9963, help="端口号")
parser.add_argument("--host", type=str, default="0.0.0.0", help="主机地址")
parser.add_argument("--base_dir", type=str, help="文件保存路径")
parser.add_argument("--password", type=str, help="访问密钥")

parser.add_argument("--no_auth", action="store_true", help="取消密码验证")
parser.add_argument("--lsdir", action="store_true", help="允许列出目录")
parser.add_argument("-r", "--recursive", action="store_true", help="递归访问所有子目录")

args = parser.parse_args()

print(args)

if args.no_auth:
    print("Warning: password authentication is disabled")

base_dir = args.base_dir

if not os.path.isabs(base_dir):
    base_dir = os.path.abspath(base_dir)

if not os.path.exists(base_dir):
    os.makedirs(base_dir)


def auth(token):
    if args.no_auth:
        return True
    current_time = str(int(time.time()))[:-1]
    correct_token = hashlib.sha256((args.password + current_time).encode()).hexdigest()
    return token == correct_token


@app.route("/<filename>", methods=["GET"])
def get_css_resource(filename):
    if filename.endswith(".css") or filename.endswith(".map"):
        return send_from_directory("templates", filename)
    return abort(404, "File not found")


import json
import logging
from datetime import datetime, timedelta

CHUNK_SIZE = 1024 * 1024  # 1MB chunks
UPLOAD_TEMP_DIR = os.path.join(base_dir, '.temp_uploads')
CHUNK_TIMEOUT = timedelta(hours=24)  # 临时文件保留24小时

# 配置日志记录
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(base_dir, 'upload.log')),
        logging.StreamHandler()
    ]
)

if not os.path.exists(UPLOAD_TEMP_DIR):
    os.makedirs(UPLOAD_TEMP_DIR)

def cleanup_old_uploads():
    """清理过期的临时文件"""
    try:
        now = datetime.now()
        for file_id in os.listdir(UPLOAD_TEMP_DIR):
            temp_dir = os.path.join(UPLOAD_TEMP_DIR, file_id)
            meta_file = os.path.join(temp_dir, 'meta.json')
            
            if not os.path.exists(meta_file):
                continue
                
            try:
                with open(meta_file, 'r') as f:
                    meta = json.load(f)
                last_modified = datetime.fromtimestamp(meta.get('last_modified', 0))
                
                if now - last_modified > CHUNK_TIMEOUT:
                    import shutil
                    shutil.rmtree(temp_dir)
                    logging.info(f'Cleaned up expired upload: {file_id}')
            except Exception as e:
                logging.error(f'Error cleaning up {file_id}: {str(e)}')
    except Exception as e:
        logging.error(f'Error in cleanup: {str(e)}')

@app.route("/upload/status/<file_id>", methods=["GET"])
def upload_status(file_id):
    """获取上传状态"""
    if not auth(request.headers.get("Authorization")):
        abort(403, "Invalid or expired password")
        
    temp_dir = os.path.join(UPLOAD_TEMP_DIR, file_id)
    if not os.path.exists(temp_dir):
        return jsonify({
            'status': 'not_found',
            'uploaded_chunks': []
        })
        
    try:
        meta_file = os.path.join(temp_dir, 'meta.json')
        if os.path.exists(meta_file):
            with open(meta_file, 'r') as f:
                meta = json.load(f)
            return jsonify({
                'status': 'in_progress',
                'uploaded_chunks': meta.get('uploaded_chunks', []),
                'filename': meta.get('filename', '')
            })
    except Exception as e:
        logging.error(f'Error reading upload status: {str(e)}')
        
    return jsonify({
        'status': 'error',
        'message': 'Could not read upload status'
    })

@app.route("/upload", methods=["POST"])
def upload():
    """处理文件上传"""
    try:
        if not auth(request.headers.get("Authorization")):
            abort(403, "Invalid or expired password")

        if "file" not in request.files:
            abort(400, "No file part")

        file = request.files["file"]
        if file.filename == "":
            abort(400, "No selected file")

        chunk_number = request.form.get('chunk', 0, type=int)
        total_chunks = request.form.get('total', 0, type=int)
        file_id = request.form.get('file_id', '')

        if not file_id:
            abort(400, "Missing file ID")

        filename = secure_filename(file.filename)
        temp_dir = os.path.join(UPLOAD_TEMP_DIR, file_id)
        
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)

        # 更新元数据
        meta_file = os.path.join(temp_dir, 'meta.json')
        meta = {
            'filename': filename,
            'total_chunks': total_chunks,
            'last_modified': datetime.now().timestamp()
        }
        
        if os.path.exists(meta_file):
            try:
                with open(meta_file, 'r') as f:
                    existing_meta = json.load(f)
                meta['uploaded_chunks'] = existing_meta.get('uploaded_chunks', [])
            except Exception:
                meta['uploaded_chunks'] = []
        else:
            meta['uploaded_chunks'] = []

        # 保存分块
        chunk_file = os.path.join(temp_dir, f'chunk_{chunk_number}')
        file.save(chunk_file)
        
        if chunk_number not in meta['uploaded_chunks']:
            meta['uploaded_chunks'].append(chunk_number)
        
        with open(meta_file, 'w') as f:
            json.dump(meta, f)

        logging.info(f'Received chunk {chunk_number} for file {filename} (ID: {file_id})')

        # 检查是否所有分块都已上传
        if len(meta['uploaded_chunks']) == total_chunks:
            final_path = os.path.join(base_dir, filename)
            
            try:
                with open(final_path, 'wb') as outfile:
                    for i in range(total_chunks):
                        chunk_path = os.path.join(temp_dir, f'chunk_{i}')
                        if not os.path.exists(chunk_path):
                            raise FileNotFoundError(f"Missing chunk {i}")
                        with open(chunk_path, 'rb') as infile:
                            outfile.write(infile.read())
                
                # 清理临时文件
                import shutil
                shutil.rmtree(temp_dir)
                logging.info(f'Successfully completed upload of {filename} (ID: {file_id})')
                
                return jsonify({
                    'status': 'success',
                    'message': 'File uploaded successfully',
                    'complete': True
                })
            except Exception as e:
                logging.error(f'Error completing upload of {filename}: {str(e)}')
                return jsonify({
                    'status': 'error',
                    'message': str(e)
                }), 500
        
        return jsonify({
            'status': 'success',
            'message': f'Chunk {chunk_number} received',
            'complete': False
        })
        
    except Exception as e:
        logging.error(f'Upload error: {str(e)}')
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# 定期清理过期的上传
import atexit
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()
scheduler.add_job(func=cleanup_old_uploads, trigger="interval", hours=1)
scheduler.start()
atexit.register(lambda: scheduler.shutdown())


@app.route("/download/<path:filepath>", methods=["GET"])
def download(filepath):
    if not auth(request.headers.get("Authorization")):
        abort(403, "Invalid or expired password")
    
    # 解析文件路径
    file_dir, filename = os.path.split(filepath)
    full_dir = os.path.join(base_dir, file_dir) if file_dir else base_dir
    
    # 安全检查：确保路径在 base_dir 内
    if not os.path.normpath(full_dir).startswith(os.path.normpath(base_dir)):
        abort(403, "Access denied")
        
    try:
        return send_from_directory(full_dir, filename, as_attachment=True)
    except FileNotFoundError:
        abort(404, "File not found")

@app.route("/webdownload/<path:filepath>", methods=["GET"])
def webdownload(filepath):
    if not auth(request.args.get("tk")):
        abort(403, "Invalid or expired password")
    
    # 解析文件路径
    file_dir, filename = os.path.split(filepath)
    full_dir = os.path.join(base_dir, file_dir) if file_dir else base_dir
    
    # 安全检查：确保路径在 base_dir 内
    if not os.path.normpath(full_dir).startswith(os.path.normpath(base_dir)):
        abort(403, "Access denied")
        
    try:
        return send_from_directory(full_dir, filename, as_attachment=True)
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
#     token = hashlib.sha256((args.password + current_time).encode()).hexdigest()
#     print("token: ", token)
#     print("auth:  ", request.headers.get('Authorization'))
#     if token == request.headers.get('Authorization'):
#         return "success", 200
#     else:
#         return "failed", 403


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/ls", methods=["GET"])
@app.route("/ls/", methods=["GET"])
@app.route("/ls/<path:subpath>", methods=["GET"])
def ls(subpath=None):
    if not args.lsdir:
        abort(403, "lsdir is disabled")
    if not args.no_auth:
        abort(403, "no_auth need to be enabled to use lsdir")
    
    # 处理尾部斜杠的情况
    if subpath == "":
        subpath = None
    
    if not args.recursive and subpath:
        abort(403, "recursive mode is disabled")
    
    # 构建当前目录的完整路径
    current_dir = base_dir
    if subpath:
        current_dir = os.path.join(base_dir, subpath)
        # 检查路径是否在 base_dir 范围内
        if not os.path.normpath(current_dir).startswith(os.path.normpath(base_dir)):
            abort(403, "Access denied")
    
    if not os.path.exists(current_dir) or not os.path.isdir(current_dir):
        abort(404, "Directory not found")
    
    files = []
    dirs = []
    
    for item in os.listdir(current_dir):
        item_path = os.path.join(current_dir, item)
        if os.path.isdir(item_path):
            dirs.append(item)
        else:
            files.append(item)
    
    # 计算相对路径用于导航
    rel_path = subpath if subpath else ""
    parent_path = os.path.dirname(rel_path) if rel_path else None
    
    return render_template(
        "directory.html", 
        files=files, 
        dirs=dirs, 
        current_path=rel_path, 
        parent_path=parent_path,
        recursive=args.recursive
    )


if __name__ == "__main__":
    app.run(host=args.host, port=args.port)
