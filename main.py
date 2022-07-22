import threading
import discord
from flask import Flask, send_from_directory

if __name__ == '__main__':

    app = Flask(__name__)

    @app.route("/")
    def hello_world():
        return "<p>Hello, World!</p><br><a href='mp3/勉強の欲望を持っているかどうかは能力以前の問題だ。.mp3'>asdf</a>"

    @app.route('/mp3/<path:path>')
    def send_report(path):
        return send_from_directory('mp3s', path)
    threading.Thread(target=lambda: app.run(host='0.0.0.0', debug=True, use_reloader=False)).start()


    class MyClient(discord.Client):
        async def on_ready(self):
            print('Logged on as', self.user)

        async def on_message(self, message):
            # don't respond to ourselves
            if message.author == self.user:
                return

            if message.content == 'ping':
                await message.channel.send('pong')


    client = MyClient()
    # client.run('token')
