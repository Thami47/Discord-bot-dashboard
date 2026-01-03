import os
import threading
import subprocess
from functools import wraps
from flask import Flask, redirect, url_for, session, request, render_template_string, abort
from flask_socketio import SocketIO
import requests

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "supersecret")
socketio = SocketIO(app)

DISCORD_CLIENT_ID = os.environ.get("DISCORD_CLIENT_ID")
DISCORD_CLIENT_SECRET = os.environ.get("DISCORD_CLIENT_SECRET")
DISCORD_REDIRECT_URI = os.environ.get("DISCORD_REDIRECT_URI")

BOTS = {
    "music_bot": ["python", "bots/music_bot.py"],
    "mod_bot": ["python", "bots/mod_bot.py"]
}

bot_processes = {}
USERS = {}

BACKGROUND_URL = "https://i.imgur.com/7M8sE.jpg"
FONT_FAMILY = "Arial, sans-serif"

DASHBOARD_HTML = """... (omitted for brevity; full HTML from earlier) ..."""

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper

def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        user = USERS.get(session.get("user_id"))
        if not user or user.get("role") != "admin":
            abort(403)
        return f(*args, **kwargs)
    return wrapper

def has_bot_access(bot):
    user = USERS.get(session.get("user_id"))
    if not user:
        return False
    if user["bots"] == "*":
        return True
    return bot in user["bots"]

def stream_logs(bot, process):
    if not process or not process.stdout:
        return
    for line in iter(process.stdout.readline, b""):
        socketio.emit("log", {"bot": bot, "message": line.decode(errors="ignore")})

@app.route("/login")
def login():
    return redirect(
        f"https://discord.com/api/oauth2/authorize?client_id={DISCORD_CLIENT_ID}"
        f"&redirect_uri={DISCORD_REDIRECT_URI}"
        f"&response_type=code&scope=identify"
    )

@app.route("/callback")
def callback():
    code = request.args.get("code")
    data = {
        "client_id": DISCORD_CLIENT_ID,
        "client_secret": DISCORD_CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": DISCORD_REDIRECT_URI,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    r = requests.post("https://discord.com/api/oauth2/token", data=data, headers=headers)
    token = r.json().get("access_token")
    if not token:
        return "Error: Could not get access token.", 400

    user = requests.get(
        "https://discord.com/api/users/@me",
        headers={"Authorization": f"Bearer {token}"},
    ).json()

    uid = user["id"]
    if uid not in USERS:
        USERS[uid] = {
            "username": user["username"],
            "role": "user",
            "bots": []
        }

    session["user_id"] = uid
    return redirect(url_for("dashboard"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/")
@login_required
def dashboard():
    visible = {}
    for bot in BOTS:
        if has_bot_access(bot):
            p = bot_processes.get(bot)
            visible[bot] = "Running" if p and p.poll() is None else "Stopped"
    return render_template_string(DASHBOARD_HTML, bots=visible, bg=BACKGROUND_URL, font=FONT_FAMILY)

@app.route("/start/<bot>")
@login_required
def start_bot(bot):
    if not has_bot_access(bot):
        abort(403)
    if bot not in bot_processes or bot_processes[bot].poll() is not None:
        proc = subprocess.Popen(BOTS[bot], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        bot_processes[bot] = proc
        threading.Thread(target=stream_logs, args=(bot, proc), daemon=True).start()
    return redirect(url_for("dashboard"))

@app.route("/stop/<bot>")
@login_required
def stop_bot(bot):
    if not has_bot_access(bot):
        abort(403)
    p = bot_processes.get(bot)
    if p and p.poll() is None:
        p.terminate()
    return redirect(url_for("dashboard"))

@app.route("/restart/<bot>")
@login_required
def restart_bot(bot):
    if not has_bot_access(bot):
        abort(403)
    p = bot_processes.get(bot)
    if p and p.poll() is None:
        p.terminate()
    proc = subprocess.Popen(BOTS[bot], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    bot_processes[bot] = proc
    threading.Thread(target=stream_logs, args=(bot, proc), daemon=True).start()
    return redirect(url_for("dashboard"))

@app.route("/admin/add_user/<uid>")
@admin_required
def add_user(uid):
    if uid not in USERS:
        USERS[uid] = {"username": uid, "role": "user", "bots": []}
    return redirect(url_for("dashboard"))

@app.route("/admin/add_bot/<bot>")
@admin_required
def add_bot(bot):
    if bot not in BOTS:
        BOTS[bot] = ["python", f"bots/{bot}.py"]
    return redirect(url_for("dashboard"))

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=8080)
