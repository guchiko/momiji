import os
import discord
import urllib
import sqlite3
import pickle
import re
import unicodedata

token = os.environ['token']
conn = sqlite3.connect(":memory:")
cur = conn.cursor()


def escape(s):
    r = s.replace('：', urllib.parse.quote('：'))
    r = r.replace(' ', urllib.parse.quote(' '))
    return r


cur.execute("""CREATE TABLE IF NOT EXISTS grams(
   gurl TEXT PRIMARY KEY,
   jap TEXT,
   eng TEXT);
""")
cur.execute("""CREATE TABLE IF NOT EXISTS mp3s(
   mp3url TEXT PRIMARY KEY,
   normtonfc TEXT,
   tag TEXT,
   gurl TEXT,
   nlvl TEXT);
""")

conn.commit()
with open('mp3List.pkl', 'rb') as f:
    mp3List = pickle.load(f)
with open('grams.pkl', 'rb') as f:
    gramList = pickle.load(f)

for m in gramList:
    cur.execute("INSERT INTO grams VALUES(?, ?, ?);", (m, gramList[m]['jap'], gramList[m]['eng']))
conn.commit()
for m in mp3List:
    nlvl = re.search('/audio/N\d/', m)
    nlvl = nlvl[0][-3:-1] if nlvl and nlvl[0] else ''
    cur.execute("INSERT INTO mp3s VALUES(?, ?, ?, ?, ?);",
                (m, unicodedata.normalize('NFC', m), mp3List[m]['tag'], mp3List[m]['Gurl'],nlvl))
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
            cur.execute("""SELECT * FROM mp3s
                      where normtonfc like '%""" + c + """%' order by tag asc, nlvl desc""")
            result = cur.fetchmany(5)
            str = '\n'.join([escape(f[0]) for f in result])
            if len(result) >= 1:
                await message.channel.send(str)


client = MyClient()

if __name__ == '__main__':
    client.run(token)
