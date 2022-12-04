import os
import discord
from discord.ext import commands
import urllib
import sqlite3
import pickle
import re
import unicodedata
from flask import Flask
import threading



app = Flask(__name__)
token = os.environ['token']
conn = sqlite3.connect(":memory:")
cur = conn.cursor()


def escape(s):
    r = s.replace('：', urllib.parse.quote('：'))
    r = r.replace(' ', urllib.parse.quote(' '))
    return r

cur.execute("""CREATE TABLE IF NOT EXISTS data(
   mp3url TEXT PRIMARY KEY,
   normtonfc TEXT,
   tag TEXT,
   gurl TEXT,
   nlvl TEXT,
   jptext TEXT,
   entext TEXT);
""")
conn.commit()
with open('data.pkl', 'rb') as f:
    dataList = pickle.load(f)

for m in dataList:
    nlvl = re.search('/audio/N\d/', m)
    nlvl = nlvl[0][-3:-1] if nlvl and nlvl[0] else ''
    cur.execute("INSERT INTO data VALUES(?, ?, ?, ?, ?, ?, ?);",
                (m, unicodedata.normalize('NFC', m), dataList[m]['tag'], dataList[m]['Gurl'],nlvl,
                 str(dataList[m]['jptext']),str(dataList[m]['entext'])))
conn.commit()


class MyClient(discord.Client):
    async def on_ready(self):
        print('Logged on as', self.user)

    async def on_message(self, message):
        c = message.content
        # don't respond to ourselves
        if message.author == self.user or message.author.bot or message.author == client.user:
            return
        if c == 'ping':
            await message.channel.send('pong')
        if (not (bool(re.search('[а-яА-Я]', c)))) & \
                (not (c.isascii())):
            c = unicodedata.normalize('NFC', c)
            cur.execute("""SELECT mp3url,jptext,entext FROM data
                      where normtonfc like '%""" + c + """%' order by tag asc, nlvl desc""")
            result = cur.fetchmany(5)
            # str = '\n'.join([escape(f[0]) for f in result])
            if len(result) >= 1:
                for s in result:
                    await message.channel.send(escape(s[0])+'\n'+s[1]+'\n'+s[2])
                # await message.channel.send(str)


@app.route('/')
def hello_world():
    return 'Hello'

# client = MyClient()

intents = discord.Intents.default()
intents.message_content = True
client = MyClient(intents=intents)

if __name__ == '__main__':
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=8000, debug=False, use_reloader=False)).start()
    client.run(token)
