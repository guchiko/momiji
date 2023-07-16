import os
import discord
import urllib
import sqlite3
import re
import unicodedata
import yt_dlp  # yt-dlp https://github.com/yt-dlp/yt-dlp
from discord.ext.commands import bot
from pydub import AudioSegment
import requests
from bs4 import BeautifulSoup
from discord.ext import tasks
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api import _errors  # youtube-transcript-api
from requests import get
from flask import Flask, send_from_directory, redirect
import threading

# from discord.ext import commands
# import pickle
# import math
# import pytube


app = Flask(__name__)
token = os.environ['token']
ip = get('https://api.ipify.org').content.decode('utf8')
lurkchannel = 'testji' if token[-2:] == '2I' else 'momiji'
lurkedport = '8614' if token[-2:] == '2I' else '8613'
print('lurkchannel is ' + lurkchannel + '\tlurkedport is ' + lurkedport)
# conn = sqlite3.connect(":memory:")
conn = sqlite3.connect("bpro.db")
cur = conn.cursor()
conny = sqlite3.connect("ytsubs.db")
cury = conny.cursor()
cury.execute("""CREATE TABLE IF NOT EXISTS ytsubs(
   vid TEXT,
   sub TEXT,
   sub_nobrackets TEXT,
   start FLOAT,
   duration FLOAT);
""")
ytmp3s = {}
bpromp3s = {}


def reinitbpromp3s():
    global bpromp3s
    mp3list = os.listdir('bpro/')
    bpromp3s = dict(zip(mp3list, range(len(mp3list))))


reinitbpromp3s()


async def mal_watch(c):
    try:
        url = "https://myanimelist.net/animelist/kli5an?status=6"
        html = requests.get(url).text
        soup = BeautifulSoup(html, 'html.parser')
        plan_to_watch = soup.find_all('a', class_='animetitle')
        if len(plan_to_watch) <= 0:
            return 0
        airingnow = []
        for a in plan_to_watch:
            t = str.strip(a.text)
            if a.parent.find_all(string='Airing'):
                airingnow.append(t)
            if a.parent.find_all(string='Airing') and t not in c.airing:
                c.airing.append(t)

        r = set(c.airing) - set(airingnow)
        if len(r) != 0:
            c.airing = airingnow
            print(f'вышло чёт!\n{r}')
            # channel_to_upload_to = client.get_channel(1062362157733396550)
            channel_to_upload_to = discord.utils.get(c.get_all_channels(), name=lurkchannel)
            await channel_to_upload_to.send(f'вышло чёт!\n{r}')
    except Exception as e:
        # channel_to_upload_to = client.get_channel(1062362157733396550)
        channel_to_upload_to = discord.utils.get(c.get_all_channels(), name=lurkchannel)
        await channel_to_upload_to.send(f"shit happened in malWatcher: {e}")
        print(f"shit happened in malWatcher: {e}")


def escape(s):
    r = s.replace('：', urllib.parse.quote('：'))
    r = r.replace(' ', urllib.parse.quote(' '))
    return r


def get_valid_filename(s):
    return re.sub(r'(?u)[^-\w.]', '_', s)


# cur.execute("""CREATE TABLE IF NOT EXISTS data(
#    mp3url TEXT PRIMARY KEY,
#    normtonfc TEXT,
#    tag TEXT,
#    gurl TEXT,
#    nlvl TEXT,
#    jptext TEXT,
#    entext TEXT);
# """)
# conn.commit()
# with open('data.pkl', 'rb') as f:
#     dataList = pickle.load(f)
#
# for m in dataList:
#     nlvl = re.search('/audio/N\d/', m)
#     nlvl = nlvl[0][-3:-1] if nlvl and nlvl[0] else ''
#     cur.execute("INSERT INTO data VALUES(?, ?, ?, ?, ?, ?, ?);",
#                 (m, unicodedata.normalize('NFC', m), dataList[m]['tag'], dataList[m]['Gurl'],nlvl,
#                  str(dataList[m]['jptext']),str(dataList[m]['entext'])))
# conn.commit()

def get_vid_from_url(c):
    if '/shorts/' in c:
        return re.search(r'shorts/[\w-]+', c).group(0)[7:]
    if 'watch?v=' in c:
        return re.search(r'watch\?v=[\w-]+', c).group(0)[8:]
    if 'youtu.be/' in c:
        return re.search(r'youtu.be/[\w-]+', c).group(0)[9:]
    return ''


async def ytdl(s, m, c):
    try:
        if c == 'yt':
            await m.channel.send("yt_url !s2 !e5.5")
            return
        start = 0
        end = 0
        vol = 0
        ytu = get_vid_from_url(c)
        if ytu == '':
            await m.channel.send('shitUrl')
        if ' !s' in c:
            start = int(
                float(
                    re.search(r'\s!s-?[,\.\d]+', c).group(0)[3:].replace(',', '.'))
                * 1000)
        if ' !e' in c:
            end = int(
                float(
                    re.search(r'\s!e[-]?[,\.\d]+', c).group(0)[3:].replace(
                        ',', '.')) * 1000)
        if ' v' in c or ' !v' in c:
            if (re.search(r'\sv[+-]+[,\.\d]+', c)):
                vol = int(re.search(r'\sv[+-]+[,\.\d]+', c).group(0)[2:])
            elif (re.search(r'\s!v[+-]+[,\.\d]+', c)):
                vol = int(re.search(r'\s!v[+-]+[,\.\d]+', c).group(0)[3:])

        if c[c.find(ytu) + len(ytu):].count(':') == 1 and ' !s' not in c and ' !e' not in c:
            r = re.search(r'[-]?[,\.\d]+:[-]?[,\.\d]+', c[c.find(ytu) + len(ytu):]).group(0).replace(',', '.')
            start = int(float(r[:r.find(':')]) * 1000)
            end = int(float(r[r.find(':') + 1:]) * 1000)
        ytid = ytu
        if ytid == '':
            await m.channel.send('shiturl?')
        ytu = 'https://www.youtube.com/watch?v=' + ytu

        # pt = pytube.YouTube(ytu)
        filename = ytid + ".mp3"
        filename = 'mp3/' + filename
        if not os.path.exists(os.getcwd() + '/mp3'):
            os.makedirs(os.getcwd() + '/mp3', exist_ok=True)
        if not os.path.exists(os.getcwd() + '/cut'):
            os.makedirs(os.getcwd() + '/cut', exist_ok=True)

        if not os.path.isfile(filename):
            await m.channel.send("downloading...", delete_after=5)
            info = yt_dlp.YoutubeDL().extract_info(ytu, download=False)
            duration = info.get('duration')
            # if pt.length > 420 and not '!f' in c:
            if duration > 420 and '!f' not in c:
                await m.channel.send("too long, use !f to force")
                return
            # df = pt.streams.filter(only_audio=True).order_by('abr').desc().first().download('mp3')
            # os.rename(df, filename)
            ydl_opts = {
                'format': 'm4a/bestaudio/best',
                'outtmpl': (filename[:-4]),
                # 'outtmpl': ('/dls/%(id)s'),
                'postprocessors': [{  # Extract audio using ffmpeg
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                }]
            }
            yt_dlp.YoutubeDL(ydl_opts).download(ytu)
            await ytsubs(None, None, c, True)

        if start != 0 or end != 0 or vol != 0:
            if start < 0:
                start = 0
            await m.channel.send("converting...", delete_after=3)
            sound = AudioSegment.from_file(filename)
            filename = filename[:-4] + '_cut' + str(start / 1000) + 'to' + str(end / 1000) + filename[-4:]
            sound = sound[start if start != 0 else None:end if end != 0 else None]
            if vol != 0:
                filename = filename[:-4] + 'v' + str(vol) + filename[-4:]
                sound = sound + vol
            sound.export('cut/' + filename[4:], format="mp3")
            filename = 'cut/' + filename[4:]

        await m.channel.send(file=discord.File(filename))
    except Exception as e:
        await m.channel.send(f"shit happened in ytdl: {e}")
        print(f"shit happened in ytdl: {e}")


async def ytsubs(s, m, c, silent=False):
    def get_ja_sub(vid):
        list_transcripts = YouTubeTranscriptApi.list_transcripts(vid)
        js = list_transcripts.find_manually_created_transcript(['ja'])
        unique_subs = []
        all_subs = []
        res = []
        for line in js.fetch():
            sub = line['text'].replace('​', '').rstrip().strip()
            start = line['start']
            duration = line['duration']
            if len(all_subs) == 0 or (len(all_subs) != 0 and all_subs[len(all_subs) - 1] != str) \
                    and sub != all_subs[len(all_subs) - 1]['sub']:
                all_subs.append({'sub': sub, 'start': start, 'duration': duration})
            if sub == all_subs[len(all_subs) - 1]['sub']:
                all_subs[len(all_subs) - 1]['duration'] = all_subs[len(all_subs) - 1]['duration'] + duration
        for s in all_subs:
            if s['sub'] in unique_subs:
                continue
            unique_subs.append(s['sub'])
            res.append(s)
        return res

    def isHaveJaSub(vid):
        try:
            list = YouTubeTranscriptApi.list_transcripts(vid)
            js = list.find_manually_created_transcript(['ja'])
            return js.language_code == 'ja'
        except (_errors.NoTranscriptFound, _errors.TranscriptsDisabled):
            return False

    ytu = get_vid_from_url(c)
    if ytu == '':
        if not silent:
            await m.channel.send('shitUrl')
        return

    cury.execute(f"Select count(1) from ytsubs s where vid='{ytu}'")
    if cury.fetchone()[0] > 0:
        print(f"{ytu} уже распотрашён")
        if not silent:
            await m.channel.send(f"{ytu} уже распотрашён")
    else:
        if isHaveJaSub(ytu):
            subs = get_ja_sub(ytu)
            for sub in subs:
                cury.execute("INSERT INTO ytsubs VALUES(?, ?, ?, ?, ?);",
                             (
                                 ytu, sub['sub'], re.sub("[\(\[].*?[\)\]]", "", sub['sub']), sub['start'],
                                 sub['duration']))
            conny.commit()
            print(f"{ytu} распотрошён, вставлено {len(subs)}")
            if not silent:
                await m.channel.send(f"{ytu} распотрошён, вставлено {len(subs)}")


async def bpro(s, m, c, howmany=3, startfrom=0):
    try:
        cur.execute("""SELECT mp3url,jptext,entext,nlvl FROM data
                              where normtonfc like '%""" + c + """%' order by tag asc, nlvl desc""")
        result = cur.fetchmany(howmany)
        if len(result) >= 1:
            for i, s in enumerate(result):
                if i >= startfrom:
                    furl = escape(s[0])
                    fname = furl[furl.rfind('/') + 1:]
                    print(fname)
                    if not os.path.isfile('bpro/' + fname):
                        print(f'downloading {fname}')
                        get_response = requests.get(furl, stream=True)
                        with open('bpro/' + fname, 'wb') as f:
                            for chunk in get_response.iter_content(chunk_size=1024):
                                if chunk:  # filter out keep-alive new chunks
                                    f.write(chunk)
                        bpromp3s[fname] = len(bpromp3s)
                    if os.path.isfile('bpro/' + fname):
                        print(f'mp3 found locally for fname {fname}')
                        print(bpromp3s[fname])
                        furl = f'http://{ip}:{lurkedport}/{str(bpromp3s[fname])}'
                    await m.channel.send('👨‍🎓  ' + furl + '\t' + s[3] + '\n' + s[1] + '\n' + re.sub("<.*?>", "", s[2]))

    except Exception as e:
        await m.channel.send(f"shit happened in bpro: {e}")
        print(f"shit happened in bpro: {e}")


class MyClient(discord.Client):
    airing = []

    @tasks.loop(hours=2)
    async def mal_watcher(self):
        await mal_watch(self)

    async def on_ready(self):
        print('Logged on as', self.user)
        self.mal_watcher.start()

    async def on_reaction_add(self, reaction, user):
        if reaction.count > 1 and reaction.me is True and reaction.emoji in {"▶",'⌚'}:
            s = ytmp3s[reaction.message.id]
            MORE = 5 if reaction.emoji == '⌚' else 0
            await ytdl(self, reaction.message, f'https://www.youtube.com/watch?v={s[0]-0.5} {s[1]}:{s[1] + s[2]+MORE}')


    async def on_message(self, message):
        c = message.content
        if message.author == self.user or message.author.bot or message.author == client.user:
            return
        print(message)
        if message.channel.name != lurkchannel:
            return
        if c == 'ping':
            await message.channel.send('pong')
        if ('youtube.com' in c or 'youtu.be' in c or 'yt' == c) and not c.startswith('s '):
            await ytdl(self, message, c)
        if ('youtube.com' in c or 'youtu.be' in c or 'yt' == c) and c.startswith('s '):
            await ytsubs(self, message, c)
        if c == '!quit':
            await client.close()
        if (not (bool(re.search('[а-яА-Я]', c)))) & \
                (not (c.isascii())):
            c = unicodedata.normalize('NFC', c)
            # bpro
            await bpro(self, message, c)
            # yt
            cury.execute(f"Select vid, sub, sub_nobrackets, start, duration "
                         f"from ytsubs s where sub like '%{c}%' or sub_nobrackets like '%{c}%'")
            result = cury.fetchmany(3)
            if len(result) >= 1:
                for s in result:
                    sendedmsg = await message.channel.send(
                        '<https://www.youtube.com/watch?v=' + s[0] + '&t=' + str(int(s[3])) + '>\n' + s[2])
                    await sendedmsg.add_reaction("▶")
                    await sendedmsg.add_reaction("⌚")
                    ytmp3s[sendedmsg.id] = [s[0], s[3], s[4]]


@app.route('/')
def hello_world():
    print(client.latency)
    if str(client.status) == 'online' and client.is_closed() is not True:
        return str(client.latency)


@app.route('/bpro/<path:path>')
def send_bpromp3(path):
    return send_from_directory('bpro', path)


@app.route('/<short_id>')
def redirect_url(short_id):
    r = next((url for url, shid in bpromp3s.items() if str(shid) == short_id), None)
    print(f'unshort {short_id} to{r}')
    if r:
        return redirect(('/bpro/' + r), 301)
    return f'shithappened  short_id:{short_id} unshorted:{r}'


intents = discord.Intents.default()
intents.message_content = True
client = MyClient(intents=intents)

if __name__ == '__main__':
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=int(lurkedport), debug=False, use_reloader=False),
                     daemon=True).start()
    client.run(token)
