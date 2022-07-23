import threading
from flask import Flask, redirect, request
import os
import discord
token = os.environ['token']

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


if __name__ == '__main__':
    client.run(token)