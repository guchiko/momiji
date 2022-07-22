import threading
from flask import Flask

if __name__ == '__main__':

    app = Flask(__name__)

    @app.route("/")
    def hello_world():
        return "<p>Hello, World!</p><br><a href='mp3/勉強の欲望を持っているかどうかは能力以前の問題だ。.mp3'>asdf</a>"

    
    app.run()


