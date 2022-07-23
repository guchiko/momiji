import threading
from flask import Flask, redirect, request
import os
import discord

class MyClient(discord.Client):
    async def on_ready(self):
        print('Logged on as', self.user)

    async def on_message(self, message):
        c = message.content
        print(c)
        # don't respond to ourselves
        if message.author == self.user or message.author.bot or message.author == client.user:
            return

        if c == 'ping':
            await message.channel.send('pong')
client = MyClient()

app = Flask(__name__)

@app.route("/", methods = ['GET', 'POST'])
def hello_world():
    return "<p>Hello, World!</p><br><a href='token/'>asdf</a>"

@app.route("/token/", methods = ['GET', 'POST'])
def settoken():
    if os.path.exists('token.txt'):
        return redirect("/", code=302)
    if request.method == 'GET':
        return """<form action="/token/" method="POST"><input name="t" id="t" value="asdf"><button>snd</button></form>"""
    if request.method == 'POST':
        token = request.form['t']
        with open('token.txt', "w", encoding="utf-8") as f:
            f.write(request.form['t'])
            threading.Thread(target=lambda: client.run(token)).start()
            print("asdfasdf2")
        return "ok"

if __name__ == '__main__':
    print("hi")
    if os.path.exists('token.txt'):
        with open('token.txt', "r", encoding="utf-8") as f:
            token = f.read()
            threading.Thread(target=lambda: client.run(token)).start()
            print("asdfasdf")
    app.run(debug=True, use_reloader=False)