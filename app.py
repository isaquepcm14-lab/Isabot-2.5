from flask import Flask, request, redirect, session, render_template_string
import sqlite3
import requests

# ================= CONFIG =================
import os

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)
app.secret_key = "isabot25_secret"

# ================= IA =================
class Isabot:
    def __init__(self):
        self.memory = {}

    def get_memory(self, user):
        if user not in self.memory:
            self.memory[user] = {"assuntos": []}
        return self.memory[user]

    def gerar_imagem(self, prompt):
        return f"https://image.pollinations.ai/prompt/{prompt.replace(' ', '%20')}"

    def explicar_com_api(self, tema):
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }

        prompt = f"""
Você é a Isabot 2.5, uma professora paciente.
Explique o tema abaixo de forma simples, com exemplo,
como se fosse para um estudante iniciante.

Tema: {tema}
"""

        data = {
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.6
        }

        r = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=data
        )
        return r.json()["choices"][0]["message"]["content"]

    def responder(self, texto, usuario):
        memoria = self.get_memory(usuario)

        if texto.startswith("/imagem"):
            desc = texto.replace("/imagem", "").strip()
            img = self.gerar_imagem(desc)
            return f'🖼️<br><img src="{img}" style="max-width:100%;border-radius:12px;">'

        if any(p in texto.lower() for p in ["explique", "o que é", "como funciona"]):
            memoria["assuntos"].append(texto)
            try:
                resposta = self.explicar_com_api(texto)
                return f"📘 **Professora Isabot:**<br>{resposta}"
            except:
                return "❌ Erro ao acessar a IA."

        return "💬 Pode me perguntar algo para eu explicar 😊"

bot = Isabot()

# ================= DB =================
def db():
    return sqlite3.connect("isabot.db")

def init_db():
    c = db().cursor()
    c.execute("CREATE TABLE IF NOT EXISTS users (u TEXT, s TEXT)")
    db().commit()

init_db()

# ================= HTML =================
HTML = """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Isabot 2.5 🤖</title>
<style>
body{background:#0f172a;color:white;font-family:Arial}
.chat{max-width:700px;margin:auto;padding:20px}
.msg{margin:10px;padding:12px;border-radius:10px}
.user{background:#2563eb;text-align:right}
.bot{background:#1e293b}
input{width:80%;padding:10px;border-radius:20px;border:none}
button{padding:10px;border:none;border-radius:20px;background:#22c55e}
</style>
</head>
<body>
<div class="chat">
<h2>🤖 Isabot 2.5</h2>

{% for m in chat %}
<div class="msg {{ m.role }}">{{ m.text|safe }}</div>
{% endfor %}

<form method="POST">
<input name="msg" placeholder="Pergunte algo...">
<button>➤</button>
</form>
</div>
</body>
</html>
"""

# ================= ROUTES =================
@app.route("/", methods=["GET", "POST"])
def chat():
    if "chat" not in session:
        session["chat"] = []

    if request.method == "POST":
        texto = request.form["msg"]
        session["chat"].append({"role": "user", "text": texto})
        resposta = bot.responder(texto, "usuario")
        session["chat"].append({"role": "bot", "text": resposta})

    return render_template_string(HTML, chat=session["chat"])

# ================= START =================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
