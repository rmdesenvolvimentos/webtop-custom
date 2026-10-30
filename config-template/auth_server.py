#!/usr/bin/env python3
"""
Webtop Security Authentication Server
- HMAC-SHA256 Token Signing & Constant-Time Verification
- Rate Limiting & Anti-Brute-Force Lockout
- Timing Attack Protection (Constant-Time Password Hash Verification)
- Authenticated Profile Updates Only (No unauthenticated privilege escalation)
- Idle Lock / Session Management
"""

import os
import sys
import json
import time
import hmac
import hashlib
import subprocess
import re
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from collections import defaultdict

SECRET_PATH = "/config/.auth_secret"
HTPASSWD_PATH = "/etc/nginx/.htpasswd"
PROFILE_PATH = "/config/user_profile.json"
LOCK_TRIGGER_PATH = "/tmp/webtop_lock_trigger"
PORT = 9099

# Brute-force protection: IP -> list of failed timestamps
FAILED_ATTEMPTS = defaultdict(list)
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_WINDOW_SECONDS = 300  # 5 minutes lockout

def get_secret():
    """Retrieve or generate high-entropy 256-bit secret with strict permissions."""
    if not os.path.exists(SECRET_PATH):
        secret = os.urandom(32).hex()
        try:
            with open(SECRET_PATH, "w") as f:
                f.write(secret)
            os.chmod(SECRET_PATH, 0o600)
        except Exception:
            pass
        return secret
    try:
        with open(SECRET_PATH) as f:
            secret = f.read().strip()
            if len(secret) >= 32:
                return secret
    except Exception:
        pass
    return os.urandom(32).hex()

def get_profile():
    default_user = os.environ.get("CUSTOM_USER", "Admin")
    defaults = {
        "username": default_user,
        "displayName": default_user,
        "idleTimeoutMinutes": 15
    }
    if os.path.exists(PROFILE_PATH):
        try:
            with open(PROFILE_PATH) as f:
                data = json.load(f)
                defaults.update(data)
        except Exception:
            pass
    elif os.path.exists(HTPASSWD_PATH):
        try:
            with open(HTPASSWD_PATH) as f:
                for line in f:
                    line = line.strip()
                    if line and ":" in line:
                        u = line.split(":", 1)[0]
                        defaults["username"] = u
                        defaults["displayName"] = u
                        break
        except Exception:
            pass
    return defaults

def save_profile(profile_data):
    current = get_profile()
    current.update(profile_data)
    with open(PROFILE_PATH, "w") as f:
        json.dump(current, f, indent=2)
    return current

def sign_token(username):
    """Generates a tamper-proof HMAC-SHA256 session token with timestamp and nonce."""
    secret = get_secret()
    ts = str(int(time.time()))
    nonce = os.urandom(16).hex()
    payload = f"v1:{username}:{ts}:{nonce}"
    sig = hmac.new(secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{payload}:{sig}"

def verify_token(token, max_age_days=30):
    """Verifies token validity using constant-time comparison."""
    if not token or not isinstance(token, str):
        return False, None
    try:
        parts = token.split(":")
        if len(parts) != 5 or parts[0] != "v1":
            return False, None
        _, u, ts_str, nonce, sig = parts
        secret = get_secret()
        payload = f"v1:{u}:{ts_str}:{nonce}"
        expected_sig = hmac.new(secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()
        
        # Constant-time comparison
        if not hmac.compare_digest(sig, expected_sig):
            return False, None
        
        ts = int(ts_str)
        now = time.time()
        # Check expiration & prevent future timestamps
        if now - ts > max_age_days * 86400 or ts > now + 120:
            return False, None
        
        return True, u
    except Exception:
        return False, None

def verify_password(username, password):
    """Timing-safe password verification with apr1 / sha1 / crypt support."""
    if not os.path.exists(HTPASSWD_PATH) or not password:
        # Dummy computation to normalize execution time
        subprocess.run(["openssl", "passwd", "-apr1", "-salt", "dummysalt", "dummypass"], capture_output=True, text=True)
        return False

    found_user = False
    valid = False

    try:
        with open(HTPASSWD_PATH) as f:
            for line in f:
                line = line.strip()
                if not line or ":" not in line:
                    continue
                u, h = line.split(":", 1)
                if hmac.compare_digest(u.lower(), username.lower()):
                    found_user = True
                    # Verify Apache MD5 (apr1)
                    if h.startswith("$apr1$"):
                        parts = h.split("$")
                        salt = parts[2] if len(parts) > 2 else ""
                        res = subprocess.run(["openssl", "passwd", "-apr1", "-salt", salt, password], capture_output=True, text=True)
                        computed = res.stdout.strip()
                        valid = hmac.compare_digest(computed, h)
                    # Verify SHA1
                    elif h.startswith("{SHA}"):
                        import base64
                        sha1_hash = "{SHA}" + base64.b64encode(hashlib.sha1(password.encode()).digest()).decode()
                        valid = hmac.compare_digest(sha1_hash, h)
                    # Plaintext fallback
                    else:
                        valid = hmac.compare_digest(password, h)
                    break
    except Exception:
        valid = False

    if not found_user:
        # Execute dummy hash to prevent username enumeration timing
        subprocess.run(["openssl", "passwd", "-apr1", "-salt", "dummysalt", password], capture_output=True, text=True)
        return False

    return valid

def check_rate_limit(ip):
    """Enforces brute-force lockout: max 5 failed attempts in 5 minutes."""
    now = time.time()
    # Filter attempts within window
    recent = [t for t in FAILED_ATTEMPTS[ip] if now - t < LOCKOUT_WINDOW_SECONDS]
    FAILED_ATTEMPTS[ip] = recent
    if len(recent) >= MAX_FAILED_ATTEMPTS:
        retry_after = int(LOCKOUT_WINDOW_SECONDS - (now - recent[0]))
        return False, max(1, retry_after)
    return True, 0

def record_failed_attempt(ip):
    FAILED_ATTEMPTS[ip].append(time.time())

def clear_failed_attempts(ip):
    if ip in FAILED_ATTEMPTS:
        del FAILED_ATTEMPTS[ip]

def set_user_credentials(username, password, display_name=None):
    disp = display_name.strip() if display_name else username
    clean_user = re.sub(r'[^a-zA-Z0-9_-]', '', username.strip().replace(" ", "_").lower()) or "admin"

    if password:
        res = subprocess.run(["openssl", "passwd", "-apr1", password], capture_output=True, text=True)
        hashed = res.stdout.strip()
        with open(HTPASSWD_PATH, "w") as f:
            f.write(f"{username}:{hashed}\n")
        try:
            p = subprocess.Popen(["sudo", "chpasswd"], stdin=subprocess.PIPE)
            p.communicate(f"abc:{password}\n".encode())
        except Exception:
            pass

    try:
        subprocess.run(["sudo", "usermod", "-c", disp, "abc"], check=False)
    except Exception:
        pass

    prompt_conf = f"""# Custom terminal identity generated by auth server
export USER="{clean_user}"
export CUSTOM_USER="{clean_user}"
export CUSTOM_DISPLAY="{disp}"
export CUSTOM_HOST="cloud-vps"
PS1='\\[\\033[01;32m\\]{clean_user}@cloud-vps\\[\\033[00m\\]:\\[\\033[01;34m\\]\\w\\[\\033[00m\\]\\$ '
"""
    try:
        with open("/config/.custom_prompt_env", "w") as f:
            f.write(prompt_conf)
    except Exception:
        pass

    save_profile({"username": username, "displayName": disp})
    return True

def parse_cookies(cookie_header):
    cookies = {}
    if not cookie_header:
        return cookies
    for item in cookie_header.split(";"):
        item = item.strip()
        if "=" in item:
            k, v = item.split("=", 1)
            cookies[k.strip()] = v.strip()
    return cookies

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True

class AuthHandler(BaseHTTPRequestHandler):
    def get_client_ip(self):
        # Support X-Forwarded-For if set by Nginx
        forwarded = self.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return self.client_address[0]

    def log_message(self, format, *args):
        if "auth_verify" not in self.path and "auth_lock_status" not in self.path:
            super().log_message(format, *args)

    def do_GET(self):
        url_path = self.path.split("?")[0]
        
        if url_path == "/auth_verify":
            cookie_header = self.headers.get("Cookie", "")
            cookies = parse_cookies(cookie_header)
            session_token = cookies.get("webtop_session")
            
            if session_token:
                valid, username = verify_token(session_token)
                if valid:
                    self.send_response(200)
                    self.send_header("Content-Type", "text/plain")
                    self.send_header("X-Auth-User", username)
                    self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
                    self.end_headers()
                    self.wfile.write(b"OK")
                    return
            
            self.send_response(401)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
            self.end_headers()
            self.wfile.write(b"Unauthorized")
            return

        elif url_path == "/auth_user":
            profile = get_profile()
            # Only expose safe public profile fields
            safe_profile = {
                "username": profile.get("username", "Admin"),
                "displayName": profile.get("displayName", "Admin"),
                "idleTimeoutMinutes": profile.get("idleTimeoutMinutes", 15)
            }
            resp = json.dumps(safe_profile).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(resp)))
            self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
            self.end_headers()
            self.wfile.write(resp)
            return

        elif url_path == "/auth_lock":
            # Triggers lock request
            try:
                with open(LOCK_TRIGGER_PATH, "w") as f:
                    f.write(str(time.time()))
            except Exception:
                pass
            resp = b'{"success": true, "message": "Lock requested"}'
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(resp)))
            self.end_headers()
            self.wfile.write(resp)
            return

        elif url_path == "/auth_lock_status":
            locked = False
            if os.path.exists(LOCK_TRIGGER_PATH):
                try:
                    os.remove(LOCK_TRIGGER_PATH)
                    locked = True
                except Exception:
                    locked = True
            resp = json.dumps({"locked": locked}).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(resp)))
            self.send_header("Cache-Control", "no-store, no-cache")
            self.end_headers()
            self.wfile.write(resp)
            return

        elif url_path == "/auth_logout":
            self.send_response(302)
            self.send_header("Set-Cookie", "webtop_session=; Path=/; HttpOnly; SameSite=Lax; Max-Age=0")
            self.send_header("Location", "/login")
            self.end_headers()
            return

        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        url_path = self.path.split("?")[0]
        client_ip = self.get_client_ip()
        
        if url_path == "/auth_login":
            # 1. Check Anti-Brute-Force Rate Limiting
            allowed, retry_after = check_rate_limit(client_ip)
            if not allowed:
                err_msg = f"Muitas tentativas incorretas. Sistema bloqueado temporariamente por segurança. Tente novamente em {retry_after} segundos."
                resp = json.dumps({"success": False, "error": err_msg, "lockout": True, "retryAfter": retry_after}).encode("utf-8")
                self.send_response(429)  # Too Many Requests
                self.send_header("Content-Type", "application/json")
                self.send_header("Retry-After", str(retry_after))
                self.send_header("Content-Length", str(len(resp)))
                self.end_headers()
                self.wfile.write(resp)
                return

            length = int(self.headers.get("Content-Length", 0))
            if length > 4096:
                self.send_response(400)
                self.end_headers()
                return

            body = self.rfile.read(length).decode("utf-8")
            
            username = None
            password = None
            try:
                data = json.loads(body)
                username = data.get("username")
                password = data.get("password")
            except Exception:
                pass
            
            profile = get_profile()
            if not username:
                username = profile.get("username", os.environ.get("CUSTOM_USER", "Admin"))
            
            if password and verify_password(username, password):
                clear_failed_attempts(client_ip)
                token = sign_token(username)
                
                # Check if HTTPS was used
                proto = self.headers.get("X-Forwarded-Proto", "").lower()
                secure_flag = "; Secure" if proto == "https" else ""
                cookie_val = f"webtop_session={token}; Path=/; HttpOnly; SameSite=Lax; Max-Age=2592000{secure_flag}"
                
                resp = json.dumps({"success": True, "redirect": "/"}).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Set-Cookie", cookie_val)
                self.send_header("Content-Length", str(len(resp)))
                self.end_headers()
                self.wfile.write(resp)
            else:
                record_failed_attempt(client_ip)
                time.sleep(1.0)  # Defense against rapid automated credential stuffing
                attempts_left = max(0, MAX_FAILED_ATTEMPTS - len(FAILED_ATTEMPTS[client_ip]))
                warning = f" Acesso será bloqueado após mais {attempts_left} tentativa(s)." if attempts_left > 0 else " Acesso bloqueado por 5 minutos."
                resp = json.dumps({"success": False, "error": f"A senha está incorreta.{warning}"}).encode("utf-8")
                self.send_response(401)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(resp)))
                self.end_headers()
                self.wfile.write(resp)
            return

        elif url_path == "/auth_update_profile":
            # SECURITY HARDENING: Must have an active, valid authenticated session!
            cookie_header = self.headers.get("Cookie", "")
            cookies = parse_cookies(cookie_header)
            session_token = cookies.get("webtop_session")
            
            valid, session_user = verify_token(session_token) if session_token else (False, None)
            if not valid:
                resp = json.dumps({"success": False, "error": "Acesso não autorizado. Faça login primeiro."}).encode("utf-8")
                self.send_response(401)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(resp)))
                self.end_headers()
                self.wfile.write(resp)
                return

            length = int(self.headers.get("Content-Length", 0))
            if length > 8192:
                self.send_response(400)
                self.end_headers()
                return

            body = self.rfile.read(length).decode("utf-8")
            try:
                data = json.loads(body)
                u = data.get("username")
                p = data.get("password")
                d = data.get("displayName")
                timeout = data.get("idleTimeoutMinutes")
                
                profile = get_profile()
                target_user = u if u else profile.get("username", session_user)
                
                if p:
                    set_user_credentials(target_user, p, d or target_user)
                else:
                    updates = {}
                    if u: updates["username"] = u
                    if d: updates["displayName"] = d
                    if timeout is not None: updates["idleTimeoutMinutes"] = int(timeout)
                    save_profile(updates)
                
                resp = b'{"success": true}'
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(resp)))
                self.end_headers()
                self.wfile.write(resp)
                return
            except Exception as e:
                resp = json.dumps({"success": False, "error": str(e)}).encode("utf-8")
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(resp)))
                self.end_headers()
                self.wfile.write(resp)
                return

        self.send_response(404)
        self.end_headers()

def run():
    get_secret()
    server = ThreadedHTTPServer(("127.0.0.1", PORT), AuthHandler)
    print(f"Auth server listening on 127.0.0.1:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    run()
