import os
import json
import uuid
import datetime
import hashlib
import secrets
from typing import Dict, Any, List, Optional
from pathlib import Path

from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import and_, or_

# 创建Flask应用
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
os.makedirs(os.path.join(BASE_DIR, "license_data"), exist_ok=True)
app = Flask(__name__)
CORS(app)  # 允许跨域请求
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(BASE_DIR, 'license_data', 'licenses.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class License(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    license_key = db.Column(db.String(64), unique=True, nullable=False)
    created_at = db.Column(db.String(32), nullable=False)
    expires_at = db.Column(db.String(32), nullable=False)
    status = db.Column(db.String(16), nullable=False)
    activations = db.Column(db.Text, default='[]')  # 存储为JSON字符串
    request_ip = db.Column(db.String(64))  # 新增：记录申请IP

with app.app_context():
    db.create_all()

# 定义数据存储路径
DATA_DIR = Path("license_data")
LICENSE_FILE = DATA_DIR / "licenses.json"
ADMIN_FILE = DATA_DIR / "admin.json"
CONFIG_FILE = DATA_DIR / "config.json"

# 确保数据目录存在
DATA_DIR.mkdir(exist_ok=True)

# 默认配置
DEFAULT_CONFIG = {
    "license_valid_days": 365,  # 默认授权有效期(天)
    "automatic_approval": True,  # 是否自动批准新授权
    "blacklist": [],             # 机器ID黑名单
    "whitelist": [],             # 机器ID白名单（仅当automatic_approval为False时使用）
    "max_activations": 1,        # 每个授权码最大激活次数（默认改为1台）
    "server_port": 5000,         # 服务器端口
    "secret_key": secrets.token_hex(32),  # 随机生成的密钥
    "max_total_licenses": 100    # 新增：最大授权码数量（默认100，可自定义）
}

# 初始化配置
def init_config():
    if not CONFIG_FILE.exists():
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_CONFIG, f, indent=4)
        return DEFAULT_CONFIG
    
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
        # 确保所有默认配置项都存在
        updated = False
        for key, value in DEFAULT_CONFIG.items():
            if key not in config:
                config[key] = value
                updated = True
        
        if updated:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4)
        
        return config
    except Exception as e:
        print(f"读取配置文件失败: {e}，使用默认配置")
        return DEFAULT_CONFIG

# 初始化管理员账号
def init_admin():
    if not ADMIN_FILE.exists():
        admin_data = {
            "username": "admin",
            "password": generate_password_hash("admin123"),
            "created_at": datetime.datetime.now().isoformat()
        }
        with open(ADMIN_FILE, "w", encoding="utf-8") as f:
            json.dump(admin_data, f, indent=4)
        print("已创建默认管理员账号: admin/admin123")

# 初始化许可证存储
def init_licenses():
    if not LICENSE_FILE.exists():
        with open(LICENSE_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, indent=4)

# 保存许可证数据
def save_licenses(licenses: List[Dict[str, Any]]):
    with open(LICENSE_FILE, "w", encoding="utf-8") as f:
        json.dump(licenses, f, indent=4, ensure_ascii=False)

# 加载许可证数据
def load_licenses() -> List[Dict[str, Any]]:
    if not LICENSE_FILE.exists():
        return []
    
    try:
        with open(LICENSE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"读取许可证文件失败: {e}")
        return []

# 生成唯一的许可证密钥
def generate_license_key() -> str:
    """生成一个唯一的许可证密钥"""
    # 使用uuid和时间戳组合生成唯一密钥
    base = f"{uuid.uuid4()}-{int(datetime.datetime.now().timestamp())}"
    # 使用SHA-256哈希并截取前32个字符
    hashed = hashlib.sha256(base.encode()).hexdigest()[:32]
    # 格式化为5组，每组5个字符，使用连字符分隔
    return "-".join([hashed[i:i+5] for i in range(0, 25, 5)])

# 查找许可证
def find_license(machine_id: str) -> Optional[Dict[str, Any]]:
    """根据机器ID查找许可证"""
    licenses = load_licenses()
    for license in licenses:
        activations = license.get("activations", [])
        for activation in activations:
            if activation.get("machine_id") == machine_id:
                return license
    return None

# 根据许可证密钥查找许可证
def find_license_by_key(license_key: str) -> Optional[Dict[str, Any]]:
    """根据许可证密钥查找许可证"""
    licenses = load_licenses()
    for license in licenses:
        if license.get("license_key") == license_key:
            return license
    return None

# 创建新许可证
def create_license(machine_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """创建一个新的许可证"""
    now = datetime.datetime.now()
    expiry_date = now + datetime.timedelta(days=config["license_valid_days"])
    # 检查是否在黑名单中
    if machine_id in config["blacklist"]:
        return {
            "success": False,
            "message": "此机器已被列入黑名单，无法获取授权"
        }
    # 新增：检查最大授权码数量
    max_total_licenses = config.get("max_total_licenses")
    db_count = License.query.count()
    if max_total_licenses is not None and db_count >= max_total_licenses:
        return {
            "success": False,
            "message": f"已达到最大授权码数量限制（{max_total_licenses}）"
        }
    # 判断审批模式
    if not config["automatic_approval"] and machine_id not in config["whitelist"]:
        # 非自动审批，且不在白名单，生成待审批key
        license_key = generate_license_key()
        db_license = License(
            license_key=license_key,
            created_at=now.isoformat(),
            expires_at=expiry_date.isoformat(),
            status="pending",
            activations=json.dumps([])
        )
        try:
            db.session.add(db_license)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"DB写入失败: {e}")
        return {
            "success": True,
            "license_key": license_key,
            "expires_at": expiry_date.isoformat(),
            "message": "授权请求已提交，待管理员审批后生效"
        }
    # 生成新许可证
    license_key = generate_license_key()
    activations = [
        {
            "machine_id": machine_id,
            "activated_at": now.isoformat(),
            "last_verified": now.isoformat()
        }
    ] if machine_id else []
    db_license = License(
        license_key=license_key,
        created_at=now.isoformat(),
        expires_at=expiry_date.isoformat(),
        status="active",
        activations=json.dumps(activations)
    )
    try:
        db.session.add(db_license)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"DB写入失败: {e}")
    return {
        "success": True,
        "license_key": license_key,
        "expires_at": expiry_date.isoformat(),
        "message": "授权成功，有效期至" + expiry_date.strftime("%Y-%m-%d")
    }

# 添加激活记录
def add_activation(license_data: Dict[str, Any], machine_id: str) -> Dict[str, Any]:
    """为现有许可证添加激活记录"""
    now = datetime.datetime.now()
    
    # 检查是否已过期
    expiry_date = datetime.datetime.fromisoformat(license_data["expires_at"])
    if expiry_date < now:
        return {
            "success": False,
            "message": "许可证已过期"
        }
    
    # 检查是否达到最大激活次数
    config = init_config()
    if len(license_data["activations"]) >= config["max_activations"]:
        return {
            "success": False,
            "message": f"许可证已达到最大激活次数 ({config['max_activations']})"
        }
    
    # 添加激活记录
    license_data["activations"].append({
        "machine_id": machine_id,
        "activated_at": now.isoformat(),
        "last_verified": now.isoformat()
    })
    
    # 更新许可证数据
    licenses = load_licenses()
    for i, license in enumerate(licenses):
        if license["license_key"] == license_data["license_key"]:
            licenses[i] = license_data
            break
    
    save_licenses(licenses)
    
    return {
        "success": True,
        "license_key": license_data["license_key"],
        "expires_at": license_data["expires_at"],
        "message": "设备已激活授权"
    }

# 更新验证时间
def update_verification_time(license_data: Dict[str, Any], machine_id: str) -> None:
    """更新许可证的最后验证时间"""
    now = datetime.datetime.now().isoformat()
    
    # 更新激活记录的最后验证时间
    for activation in license_data["activations"]:
        if activation["machine_id"] == machine_id:
            activation["last_verified"] = now
            break
    
    # 更新许可证数据
    licenses = load_licenses()
    for i, license in enumerate(licenses):
        if license["license_key"] == license_data["license_key"]:
            licenses[i] = license_data
            break
    
    save_licenses(licenses)

# API路由 - 获取新授权
@app.route("/api/license/new", methods=["POST"])
def new_license():
    data = request.json
    machine_id = data.get("machine_id", "")
    config = init_config()
    now = datetime.datetime.now()
    expiry_date = now + datetime.timedelta(days=config.get("license_valid_days", 365))
    # 获取客户端IP
    request_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    # 检查最大授权码数量
    max_total_licenses = config.get("max_total_licenses")
    db_count = License.query.count()
    if max_total_licenses is not None and db_count >= max_total_licenses:
        return jsonify({
            "success": False,
            "message": f"已达到最大授权码数量限制（{max_total_licenses}）"
        })
    # 检查黑名单
    if machine_id and machine_id in config["blacklist"]:
        return jsonify({
            "success": False,
            "message": "此机器已被列入黑名单，无法获取授权"
        })
    # 生成授权码
    license_key = str(uuid.uuid4()).replace("-", "").upper()[:20]
    status = "active"
    message = "授权码已生成，可以直接使用"
    activations = []
    # 非自动审批且不在白名单，设为待审批
    if machine_id and not config["automatic_approval"] and machine_id not in config["whitelist"]:
        status = "pending"
        message = "授权码已生成，待管理员审批后生效"
    if machine_id and status == "active":
        activations = [{
            "machine_id": machine_id,
            "activated_at": now.isoformat(),
            "last_verified": now.isoformat()
        }]
    db_license = License(
        license_key=license_key,
        created_at=now.isoformat(),
        expires_at=expiry_date.isoformat(),
        status=status,
        activations=json.dumps(activations),
        request_ip=request_ip
    )
    try:
        db.session.add(db_license)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"数据库写入失败: {e}"})
    return jsonify({
        "success": True,
        "license_key": license_key,
        "status": status,
        "expires_at": expiry_date.isoformat(),
        "message": message
    })

# API路由 - 验证授权
@app.route("/api/license/verify", methods=["POST"])
def verify_license():
    data = request.json
    license_key = data.get("license_key")
    machine_id = data.get("machine_id")
    if not license_key:
        return jsonify({
            "success": False,
            "valid": False,
            "message": "缺少授权码 (license_key) 参数"
        }), 400
    if not machine_id:
        return jsonify({
            "success": False,
            "valid": False,
            "message": "缺少设备标识 (machine_id) 参数"
        }), 400
    # 先查数据库
    db_license = License.query.filter_by(license_key=license_key).first()
    if db_license:
        try:
            activations = json.loads(db_license.activations)
        except Exception:
            activations = []
        license_data = {
            "license_key": db_license.license_key,
            "created_at": db_license.created_at,
            "expires_at": db_license.expires_at,
            "status": db_license.status,
            "activations": activations
        }
    else:
        # 兼容老数据，查json
        license_data = find_license_by_key(license_key)
        if not license_data:
            return jsonify({
                "success": False,
                "valid": False,
                "message": "授权码不存在"
            }), 404
    # 检查许可证状态，只有active才允许后续激活和验证
    if license_data.get("status") != "active":
        return jsonify({
            "success": False,
            "valid": False,
            "message": f"授权码状态无效: {license_data.get('status')}"
        })
    # 检查是否过期
    expiry_date = datetime.datetime.fromisoformat(license_data["expires_at"])
    if expiry_date < datetime.datetime.now():
        return jsonify({
            "success": False,
            "valid": False,
            "message": "授权码已过期"
        })
    # 检查设备是否已激活
    device_activated = False
    for activation in license_data.get("activations", []):
        if activation.get("machine_id") == machine_id:
            device_activated = True
            # 更新验证时间
            update_verification_time(license_data, machine_id)
            break
    # 只有active状态才允许激活设备
    if not device_activated:
        activation_result = add_activation(license_data, machine_id)
        if not activation_result.get("success"):
            return jsonify({
                "success": False,
                "valid": False,
                "message": activation_result.get("message", "设备激活失败")
            })
    # 授权码有效
    return jsonify({
        "success": True,
        "valid": True,
        "license_key": license_key,
        "expires_at": license_data["expires_at"],
        "message": "授权码验证通过"
    })

# API路由 - 管理员登录
@app.route("/api/admin/login", methods=["POST"])
def admin_login():
    """管理员登录"""
    data = request.json
    username = data.get("username")
    password = data.get("password")
    
    if not username or not password:
        return jsonify({"success": False, "message": "缺少用户名或密码"}), 400
    
    # 加载管理员信息
    if not ADMIN_FILE.exists():
        return jsonify({"success": False, "message": "管理员账号未初始化"}), 500
    
    try:
        with open(ADMIN_FILE, "r", encoding="utf-8") as f:
            admin_data = json.load(f)
        
        # 验证用户名和密码
        if username != admin_data["username"] or not check_password_hash(admin_data["password"], password):
            return jsonify({"success": False, "message": "用户名或密码错误"}), 401
        
        # 生成一个简单的会话令牌（实际应用中应使用更安全的方式）
        token = hashlib.sha256(f"{username}:{datetime.datetime.now().isoformat()}:{DEFAULT_CONFIG['secret_key']}".encode()).hexdigest()
        
        return jsonify({
            "success": True,
            "token": token,
            "message": "登录成功"
        })
    except Exception as e:
        return jsonify({"success": False, "message": f"登录过程发生错误: {str(e)}"}), 500

# API路由 - 获取所有许可证
@app.route("/api/admin/licenses", methods=["GET"])
def get_all_licenses():
    try:
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", 10))
        status = request.args.get("status")
        license_key = request.args.get("license_key")
        expires_start = request.args.get("expires_start")
        expires_end = request.args.get("expires_end")
        query = License.query
        filters = []
        if status:
            filters.append(License.status == status)
        if license_key:
            filters.append(License.license_key.like(f"%{license_key}%"))
        if expires_start:
            filters.append(License.expires_at >= expires_start)
        if expires_end:
            filters.append(License.expires_at <= expires_end)
        if filters:
            query = query.filter(and_(*filters))
        pagination = query.order_by(License.id.desc()).paginate(page=page, per_page=page_size, error_out=False)
        licenses = []
        for lic in pagination.items:
            try:
                acts = json.loads(lic.activations)
            except Exception:
                acts = []
            licenses.append({
                "license_key": lic.license_key,
                "created_at": lic.created_at,
                "expires_at": lic.expires_at,
                "status": lic.status,
                "activations": acts,
                "request_ip": lic.request_ip  # 新增：返回申请IP
            })
        return jsonify({
            "success": True,
            "licenses": licenses,
            "total": pagination.total,
            "page": page,
            "page_size": page_size
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

# 一键迁移老json授权码到数据库
@app.route("/api/admin/licenses/migrate-old-data", methods=["POST"])
def migrate_old_licenses():
    try:
        old_licenses = load_licenses()
        count = 0
        for lic in old_licenses:
            if not License.query.filter_by(license_key=lic["license_key"]).first():
                db_license = License(
                    license_key=lic["license_key"],
                    created_at=lic["created_at"],
                    expires_at=lic["expires_at"],
                    status=lic["status"],
                    activations=json.dumps(lic.get("activations", []))
                )
                db.session.add(db_license)
                count += 1
        db.session.commit()
        return jsonify({"success": True, "migrated": count})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)})

# API路由 - 更新许可证状态
@app.route("/api/admin/licenses/<license_key>", methods=["PUT", "DELETE"])
def update_license(license_key):
    # 这里应该有身份验证逻辑，为简化示例省略
    if request.method == "PUT":
        data = request.json
        new_status = data.get("status")
        new_expires_at = data.get("expires_at")
        if not new_status and not new_expires_at:
            return jsonify({"success": False, "message": "缺少参数"}), 400
        lic = License.query.filter_by(license_key=license_key).first()
        if not lic:
            return jsonify({"success": False, "message": "未找到指定的许可证"}), 404
        updated = False
        if new_status:
            lic.status = new_status
            updated = True
        if new_expires_at:
            lic.expires_at = new_expires_at
            updated = True
        if updated:
            try:
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                return jsonify({"success": False, "message": f"数据库更新失败: {e}"})
            return jsonify({
                "success": True,
                "message": f"许可证已更新",
                "license": {
                    "license_key": lic.license_key,
                    "created_at": lic.created_at,
                    "expires_at": lic.expires_at,
                    "status": lic.status,
                    "activations": json.loads(lic.activations),
                    "request_ip": lic.request_ip
                }
            })
        else:
            return jsonify({"success": False, "message": "未做任何更改"})
    elif request.method == "DELETE":
        lic = License.query.filter_by(license_key=license_key).first()
        if not lic:
            return jsonify({"success": False, "message": "未找到指定的许可证"}), 404
        try:
            db.session.delete(lic)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "message": f"数据库删除失败: {e}"})
        return jsonify({"success": True, "message": "许可证已删除"})

# API路由 - 获取配置
@app.route("/api/admin/config", methods=["GET"])
def get_config():
    """获取服务器配置"""
    # 这里应该有身份验证逻辑，为简化示例省略
    
    config = init_config()
    return jsonify({
        "success": True,
        "config": config
    })

# API路由 - 更新配置
@app.route("/api/admin/config", methods=["PUT"])
def update_config():
    """更新服务器配置"""
    # 这里应该有身份验证逻辑，为简化示例省略
    
    data = request.json
    
    # 加载当前配置
    config = init_config()
    
    # 更新配置项
    for key, value in data.items():
        if key in config:
            config[key] = value
    
    # 保存配置
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)
    
    return jsonify({
        "success": True,
        "message": "配置已更新",
        "config": config
    })

# API路由 - 批量删除许可证
@app.route("/api/admin/licenses/batch-delete", methods=["POST"])
def batch_delete_licenses():
    data = request.json
    license_keys = data.get("license_keys", [])
    if not isinstance(license_keys, list) or not license_keys:
        return jsonify({"success": False, "message": "缺少 license_keys 或格式错误"}), 400
    try:
        deleted_count = License.query.filter(License.license_key.in_(license_keys)).delete(synchronize_session=False)
        db.session.commit()
        return jsonify({"success": True, "deleted": deleted_count})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"数据库批量删除失败: {e}"})

# API路由 - 批量修改许可证状态
@app.route("/api/admin/licenses/batch-update", methods=["POST"])
def batch_update_licenses():
    data = request.json
    license_keys = data.get("license_keys", [])
    new_status = data.get("status")
    new_expires_at = data.get("expires_at")
    if not isinstance(license_keys, list) or not license_keys or (not new_status and not new_expires_at):
        return jsonify({"success": False, "message": "缺少 license_keys 或 status/expires_at"}), 400
    try:
        query = License.query.filter(License.license_key.in_(license_keys))
        updated_count = 0
        for lic in query:
            if new_status:
                lic.status = new_status
            if new_expires_at:
                lic.expires_at = new_expires_at
            updated_count += 1
        db.session.commit()
        return jsonify({"success": True, "updated": updated_count})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"数据库批量更新失败: {e}"})

# API路由 - 批量生成授权码
@app.route("/api/admin/licenses/batch-create", methods=["POST"])
def batch_create_licenses():
    data = request.json
    count = data.get("count", 0)
    machine_ids = data.get("machine_ids", [])
    
    if count <= 0 and not machine_ids:
        return jsonify({"success": False, "message": "缺少 count 或 machine_ids 参数"}), 400
    
    config = init_config()
    licenses = load_licenses()
    
    # 检查是否超过最大授权码数量
    max_total_licenses = config.get("max_total_licenses")
    if max_total_licenses is not None:
        remaining = max_total_licenses - len(licenses)
        if remaining <= 0:
            return jsonify({"success": False, "message": f"已达到最大授权码数量限制（{max_total_licenses}）"})
        if count > remaining:
            count = remaining
    
    created_licenses = []
    
    # 如果提供了机器ID列表
    if machine_ids:
        for machine_id in machine_ids:
            # 检查黑名单
            if machine_id in config["blacklist"]:
                continue
                
            # 创建授权码
            now = datetime.datetime.now()
            expiry_date = now + datetime.timedelta(days=config["license_valid_days"])
            license_key = generate_license_key()
            
            # 根据自动审批设置决定状态
            status = "active"
            if not config["automatic_approval"] and machine_id not in config["whitelist"]:
                status = "pending"
            
            new_license = {
                "license_key": license_key,
                "created_at": now.isoformat(),
                "expires_at": expiry_date.isoformat(),
                "status": status,
                "activations": [
                    {
                        "machine_id": machine_id,
                        "activated_at": now.isoformat(),
                        "last_verified": now.isoformat()
                    }
                ]
            }
            
            licenses.append(new_license)
            created_licenses.append(new_license)
            
            # 检查是否达到最大数量
            if max_total_licenses is not None and len(licenses) >= max_total_licenses:
                break
    
    # 如果指定了数量，生成无机器ID的授权码
    elif count > 0:
        for _ in range(count):
            now = datetime.datetime.now()
            expiry_date = now + datetime.timedelta(days=config["license_valid_days"])
            license_key = generate_license_key()
            
            new_license = {
                "license_key": license_key,
                "created_at": now.isoformat(),
                "expires_at": expiry_date.isoformat(),
                "status": "active",  # 无机器ID的授权码默认为激活状态
                "activations": []
            }
            
            licenses.append(new_license)
            created_licenses.append(new_license)
    
    save_licenses(licenses)
    
    return jsonify({
        "success": True,
        "created": len(created_licenses),
        "licenses": created_licenses,
        "message": f"成功生成 {len(created_licenses)} 个授权码"
    })

# 主页
@app.route("/")
def home():
    return """
    <html>
    <head>
        <title>XBot授权服务器</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 20px;
                line-height: 1.6;
            }
            .container {
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                border: 1px solid #ddd;
                border-radius: 5px;
            }
            h1 {
                color: #333;
            }
            .api-route {
                background: #f4f4f4;
                padding: 10px;
                margin-bottom: 10px;
                border-radius: 3px;
            }
            .method {
                font-weight: bold;
                color: #0066cc;
            }
            footer {
                margin-top: 40px;
                text-align: center;
                color: #777;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>XBot授权服务器</h1>
            <p>此服务器提供XBot程序的授权验证功能。</p>
            
            <h2>API端点:</h2>
            
            <div class="api-route">
                <span class="method">POST</span> /api/license/new - 请求新的授权
            </div>
            
            <div class="api-route">
                <span class="method">POST</span> /api/license/verify - 验证现有授权
            </div>
            
            <div class="api-route">
                <span class="method">POST</span> /api/admin/login - 管理员登录
            </div>
            
            <div class="api-route">
                <span class="method">GET</span> /api/admin/licenses - 获取所有授权
            </div>
            
            <div class="api-route">
                <span class="method">PUT</span> /api/admin/licenses/{license_key} - 更新授权状态
            </div>
            
            <div class="api-route">
                <span class="method">GET</span> /api/admin/config - 获取服务器配置
            </div>
            
            <div class="api-route">
                <span class="method">PUT</span> /api/admin/config - 更新服务器配置
            </div>
            
            <div class="api-route">
                <span class="method">POST</span> /api/admin/licenses/batch-delete - 批量删除许可证
            </div>
            
            <div class="api-route">
                <span class="method">POST</span> /api/admin/licenses/batch-update - 批量修改许可证状态
            </div>
            
            <div class="api-route">
                <span class="method">POST</span> /api/admin/licenses/batch-create - 批量生成授权码
            </div>
            
            <footer>
                <p>XBot授权服务器 &copy; 2023</p>
            </footer>
        </div>
    </body>
    </html>
    """

# 初始化
init_config()
init_admin()
init_licenses()

# 启动服务器
if __name__ == "__main__":
    config = init_config()
    port = config.get("server_port", 5000)
    app.run(host="0.0.0.0", port=port, debug=True)