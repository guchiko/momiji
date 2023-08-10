import os
import discord
from urllib import parse
import sqlite3
import re
import unicodedata
import yt_dlp  # yt-dlp https://github.com/yt-dlp/yt-dlp
from pydub import AudioSegment
import requests
from bs4 import BeautifulSoup
from discord.ext import tasks
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api import _errors  # youtube-transcript-api
from requests import get
from flask import Flask, send_from_directory, redirect  # , request
import threading

# from discord.ext.commands import bot
# import signal
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
mp3list = os.listdir('bpro/')
bpromp3s_shorts = dict(zip(mp3list, range(len(mp3list))))


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
    r = s.replace('：', parse.quote('：'))
    r = r.replace(' ', parse.quote(' '))
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
            start = 0 if start < 0 else start
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

        filename = 'mp3/' + ytid + ".mp3"
        if not os.path.exists(os.getcwd() + '/mp3'):
            os.makedirs(os.getcwd() + '/mp3', exist_ok=True)
        if not os.path.exists(os.getcwd() + '/cut'):
            os.makedirs(os.getcwd() + '/cut', exist_ok=True)

        # if ('!x' in c):
        # external downloader
        filename = 'mp3/' + ytid + '.mp3'
        ydl_opts = {
            'format': 'm4a/bestaudio/best',
            'outtmpl': (filename[:-4]),
            'postprocessors': [{  # Extract audio using ffmpeg
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
            }]
        }
        if start != 0 or end != 0:
            filename = 'cut/' + filename[4:]
            filename = filename[:-4] + '_cut' + str(start / 1000) + 'to' + str(end / 1000) + filename[-4:]
            ydl_opts['outtmpl'] = (filename[:-4])

            ydl_opts["external_downloader"] = "ffmpeg"
            # ydl_opts["external_downloader_args"] = {"ffmpeg_i": ["-ss", str(start/1000), "-to", str(end/1000)]}
            dargs = []
            if start != 0:
                dargs.append("-ss")
                dargs.append(str(start / 1000))
            if end != 0:
                dargs.append("-to")
                dargs.append(str(end / 1000))
            ydl_opts["external_downloader_args"] = {"ffmpeg_i": dargs}

        if not os.path.isfile(filename):
            await m.channel.send("downloading...", delete_after=5)
            yt_dlp.YoutubeDL(ydl_opts).download(ytid)

        if vol != 0:
            await m.channel.send("vol adjusting...", delete_after=3)
            sound = AudioSegment.from_file(filename)
            sound = sound + vol
            filename = filename[:-4] + f'v{vol}' + filename[-4:]
            sound.export(filename, format="mp3")
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
            return len(subs)
    return 0


async def ytsubs_multy(s, m, c):
    pasted = 0
    ripped = 0
    vids = c.split(',')
    for vid in vids:
        pasted += await ytsubs(s, m, 'https://www.youtube.com/watch?v=' + vid, silent=True)
        ripped += 1
    await m.channel.send(f"прислано {len(vids)},распотрошёно {ripped}, вставлено {pasted}")


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
                    if not os.path.isfile('bpro/' + fname):
                        print(f'downloading {fname}')
                        get_response = requests.get(furl, stream=True)
                        with open('bpro/' + fname, 'wb') as f:
                            for chunk in get_response.iter_content(chunk_size=1024):
                                if chunk:  # filter out keep-alive new chunks
                                    f.write(chunk)
                        bpromp3s_shorts[fname] = len(bpromp3s_shorts)
                    if os.path.isfile('bpro/' + fname):
                        print(f'mp3 found locally for fname {fname}: {bpromp3s_shorts[fname]}')
                        furl = f'http://{ip}:{lurkedport}/{str(bpromp3s_shorts[fname])}'
                    await m.channel.send(
                        '👨‍🎓  ' + furl + '\t' + s[3] + '\n' + s[1] + '\n' + re.sub("<.*?>", "", s[2]))

    except Exception as e:
        await m.channel.send(f"shit happened in bpro: {e}")
        print(f"shit happened in bpro: {e}")


async def yt(s, m, c, howmany=3, startfrom=0):
    cury.execute(f"Select vid, sub, sub_nobrackets, start, duration "
                 f"from ytsubs s where sub like '%{c}%' or sub_nobrackets like '%{c}%'")
    result = cury.fetchmany(howmany)
    if len(result) >= 1:
        for i, s in enumerate(result):
            if i >= startfrom:
                sendedmsg = await m.channel.send(
                    '<https://www.youtube.com/watch?v=' + s[0] + '&t=' + str(int(s[3])) + '>\n' + s[2])
                await sendedmsg.add_reaction("▶")
                await sendedmsg.add_reaction("⌚")
                ytmp3s[sendedmsg.id] = [s[0], s[3], s[4]]


class MyClient(discord.Client):
    airing = []

    @tasks.loop(hours=2)
    async def mal_watcher(self):
        await mal_watch(self)

    async def on_ready(self):
        print('Logged on as', self.user)
        self.mal_watcher.start()

    async def on_reaction_add(self, reaction, user):
        if reaction.count > 1 and reaction.me is True and reaction.emoji in {"▶", '⌚'}:
            s = ytmp3s[reaction.message.id]
            MORE = 5 if reaction.emoji == '⌚' else 0
            await ytdl(self, reaction.message,
                       f'https://www.youtube.com/watch?v={s[0]} {s[1] - 0.5}:{s[1] + s[2] + MORE}')
            c = reaction.message.content
            await reaction.message.edit(content=c[c.find('\n') + 1:])

    async def on_message(self, message):
        c = message.content
        c = unicodedata.normalize('NFC', c)
        if message.author == self.user or message.author.bot or message.author == client.user:
            return
        print(message)
        if message.channel.name != lurkchannel:
            return
        if c == 'ping':
            await message.channel.send('pong')
        if c == '?' or c == 'halp' or c == 'help':
            await message.channel.send("""download: yt_url !s2 !e5.5 or yt_url 2:5.5
            grab subs: s yt_url
            grab many subs: ss yt_id,yt_id
            bpro: b# text
            yt: y# text""")
        if ('youtube.com' in c or 'youtu.be' in c) and not c.lower().startswith('s '):
            await ytdl(self, message, c)
        if ('youtube.com' in c or 'youtu.be' in c) and c.lower().startswith('s '):
            await ytsubs(self, message, c)
        if c == '!quit':
            await client.close()
        # bpro
        if c.lower().startswith('b '):
            await bpro(self, message, c[2:], 5)
        if c.lower().startswith('b'):
            if re.search(r'^b\d+?\s', c):
                await bpro(self, message, c[c.find(' ') + 1:], int(re.search(r'^b\d+?\s', c).group(0)[1:-1]))
        # grab many subs
        if c.lower().startswith('ss '):
            await ytsubs_multy(self, message, c[3:])
        # yt
        if c.lower().startswith('y '):
            await yt(self, message, c[2:], 5)
        if c.lower().startswith('y') and re.search(r'^y\d+?\s', c):
            await yt(self, message, c[c.find(' ') + 1:], int(re.search(r'^y\d+?\s', c).group(0)[1:-1]))
        # bpro+yt
        if ((not (bool(re.search('[а-яА-Я]', c)))) and (not (c.isascii()))):
            cury.execute(f"Select count(1) from ytsubs s where sub like '%{c}%' or sub_nobrackets like '%{c}%'")
            cnty = cury.fetchone()[0]

            cur.execute(f"""SELECT count(1) FROM data
                        where normtonfc like '%{c}%' order by tag asc, nlvl desc""")
            cntb = cur.fetchone()[0]
            await message.channel.send(f"bpro: {cntb} yt: {cnty}")
            await bpro(self, message, c)
            await yt(self, message, c)


@app.route('/')
def hello_world():
    print(client.latency)
    if str(client.status) == 'online' and client.is_closed() is not True:
        return str(client.latency)


@app.route('/bpro/<path:path>')
def send_bpromp3(path):
    # if 'Discordbot' not in request.headers.get('User-Agent'):
    #     print(f'send_bpromp3:path={path}')
    return send_from_directory('bpro', path)


@app.route('/<short_id>')
def redirect_url(short_id):
    r = next((url for url, shid in bpromp3s_shorts.items() if str(shid) == short_id), None)
    # print(f'unshort {short_id} to{r}')
    if r:
        return redirect(('/bpro/' + r), 301)
    return f'shithappened  short_id:{short_id} unshorted:{r}'


intents = discord.Intents.default()
intents.message_content = True
client = MyClient(intents=intents)

# def shutdown(q,w):
#     print('shutdown')
#     client.close()

if __name__ == '__main__':
    # signal.signal(signal.SIGINT, shutdown)
    # signal.signal(signal.SIGTERM, shutdown)
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=int(lurkedport), debug=False, use_reloader=False),
                     daemon=True).start()
    client.run(token)
