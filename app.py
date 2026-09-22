from flask import Flask, render_template, request, redirect, url_for, session, jsonify, Response
import sqlite3, os, csv, io, secrets
from datetime import datetime, timezone
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax")

DB_PATH = os.environ.get("DB_PATH", os.path.join(os.path.dirname(__file__), "responses.db"))
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")

Q1 = "あなたにとって、憧れの存在はいますか？"
Q2 = "「一度でいいから、この人のように1日を生きてみたい」や「この人が見ている世界を自分もみてみたい」と思ったことはありますか？"

def get_db():
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            q1 TEXT NOT NULL CHECK(q1 IN ('はい','いいえ')),
            q2 TEXT NOT NULL CHECK(q2 IN ('はい','いいえ')),
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

init_db()

def admin_required(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        if not session.get("admin"):
            return redirect(url_for("admin_login"))
        return fn(*args, **kwargs)
    return wrapped

@app.get("/")
def survey():
    if session.get("submitted"):
        return redirect(url_for("thanks"))
    return render_template("survey.html", q1=Q1, q2=Q2)

@app.post("/submit")
def submit():
    if session.get("submitted"):
        return redirect(url_for("thanks"))
    q1 = request.form.get("q1")
    q2 = request.form.get("q2")
    if q1 not in ("はい","いいえ") or q2 not in ("はい","いいえ"):
        return render_template("survey.html", q1=Q1, q2=Q2, error="2問とも回答してください。"), 400
    conn = get_db()
    conn.execute("INSERT INTO responses (q1, q2, created_at) VALUES (?, ?, ?)",
                 (q1, q2, datetime.now(timezone.utc).isoformat(timespec="seconds")))
    conn.commit()
    conn.close()
    session["submitted"] = True
    return redirect(url_for("thanks"))

@app.get("/thanks")
def thanks():
    return render_template("thanks.html")

@app.route("/admin", methods=["GET","POST"])
def admin_login():
    if request.method == "POST":
        if not ADMIN_PASSWORD:
            return render_template("admin_login.html", error="管理者パスワードが未設定です。"), 503
        if secrets.compare_digest(request.form.get("password",""), ADMIN_PASSWORD):
            session["admin"] = True
            return redirect(url_for("dashboard"))
        return render_template("admin_login.html", error="パスワードが違います。"), 401
    if session.get("admin"):
        return redirect(url_for("dashboard"))
    return render_template("admin_login.html")

@app.get("/admin/dashboard")
@admin_required
def dashboard():
    return render_template("admin.html", q1=Q1, q2=Q2)

@app.get("/admin/data")
@admin_required
def admin_data():
    conn = get_db()
    total = conn.execute("SELECT COUNT(*) AS c FROM responses").fetchone()["c"]
    q1_yes = conn.execute("SELECT COUNT(*) AS c FROM responses WHERE q1='はい'").fetchone()["c"]
    q2_yes = conn.execute("SELECT COUNT(*) AS c FROM responses WHERE q2='はい'").fetchone()["c"]
    conn.close()
    def pack(yes):
        no = total - yes
        return {
            "yes": yes, "no": no,
            "yes_pct": round(yes/total*100, 1) if total else 0,
            "no_pct": round(no/total*100, 1) if total else 0
        }
    return jsonify({"total":total, "q1":pack(q1_yes), "q2":pack(q2_yes)})

@app.get("/admin/export.csv")
@admin_required
def export_csv():
    conn = get_db()
    rows = conn.execute("SELECT id, q1, q2, created_at FROM responses ORDER BY id").fetchall()
    conn.close()
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(["id", Q1, Q2, "created_at"])
    for r in rows:
        w.writerow([r["id"], r["q1"], r["q2"], r["created_at"]])
    return Response("\ufeff"+out.getvalue(), mimetype="text/csv; charset=utf-8",
                    headers={"Content-Disposition":"attachment; filename=success_march_survey.csv"})

@app.post("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect(url_for("admin_login"))

@app.get("/health")
def health():
    return {"status":"ok"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",5000)))
