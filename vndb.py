import json
import random
import re
import socket
import textwrap


def login(bot):
    bot.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    bot.sock.connect(('api.vndb.org', 19534))
    with open('tokens/vndb', 'rb') as token:
        bot.sock.send(token.read())
    print(bot.sock.recv(128))


async def create_embed(bot, data, description, channel):
    if not data['num']:
        await channel.send('Visual novel not found.')
        return

    title = '{} ({})'.format(data['items'][0]['original'], data['items'][0]['title'])
    url = 'https://vndb.org/v{}'.format(data['items'][0]['id'])
    footer = 'Release date: {}'.format(data['items'][0]['released'])
    if not data['items'][0]['image_nsfw']:
        thumbnail = data['items'][0]['image']
    else:
        thumbnail = 'https://i.imgur.com/p8HQTjm.png'

    await bot.post_embed(title=title, description=description, url=url,
        thumbnail=thumbnail, footer=footer, channel=channel)


async def search(bot, filter, channel):
    query = bytes('get vn basic,details {}\x04'.format(filter), encoding='utf8')
    bot.sock.send(query)
    # I want to do this loop better
    res = bot.sock.recv(2048)
    while res[-1:] != b'\x04':
        res += bot.sock.recv(2048)

    try:
        # more elegant way to do this?
        res = json.loads(res.decode()[8:-1])
        if res['items'][0]['description']:
            description = textwrap.shorten(res['items'][0]['description'], width=1000, placeholder='...')
            description = re.sub('\[From.*]', '', description)
            description = re.sub('\[.*?](.*?)\[/.*?]', '\g<1>', description)
        else:
            description = 'No description.'

        await create_embed(bot, res, description, channel)

    except:
        await channel.send('API Error.')


async def rand(bot, channel):
    bot.sock.send(b'dbstats\x04')
    stats = json.loads(bot.sock.recv(256).decode()[8:-1])
    filter = '(id = {})'.format(random.randint(1, stats['vn']))
    await search(bot, filter, channel)


async def relations(bot, filter, channel):
    query = bytes('get vn basic,details,relations {}\x04'.format(filter), encoding='utf8')
    bot.sock.send(query)
    # I want to do this loop better
    res = bot.sock.recv(2048)
    while res[-1:] != b'\x04':
        res += bot.sock.recv(2048)

    try:
        res = json.loads(res.decode()[8:-1])
        description = '**Related Visual Novels:**\n\n'
        for r in res['items'][0]['relations']:
            description += r['title'] + '\n'
            description += 'https://vndb.org/v' + r['id'] + '\n\n'

        await create_embed(bot, res, description, channel)

    except:
        await channel.send('API Error.')


async def character(bot, filter, channel):
    query = bytes('get character basic,details,voiced {}\x04'.format(filter), encoding='utf8')
    bot.sock.send(query)
    # I want to do this loop better
    res = bot.sock.recv(2048)
    while res[-1:] != b'\x04':
        res += bot.sock.recv(2048)

    try:
        res = json.loads(res.decode()[8:-1])
        # print(json.dumps(res, sort_keys=True, indent=4, separators=(',', ': ')))
        if not res['num']:
            await channel.send('Character not found.')
            return

        title = '{} ({})'.format(res['items'][0]['original'], res['items'][0]['name'])
        if res['items'][0]['description']:
            description = textwrap.shorten(res['items'][0]['description'], width=1000, placeholder='...')
            description = re.sub('\[Spoiler]|\[/Spoiler]', '||', description)
        else:
            description = 'No description.'
        url = 'https://vndb.org/c{}'.format(res['items'][0]['id'])
        image = res['items'][0]['image']

        await bot.post_embed(title=title, description=description, url=url, image=image,
            channel=channel)

    except:
        await channel.send('API Error.')


async def help(bot, channel):
    with open('data/help') as help:
        await bot.post_embed(title='Commands:', description=help.read(), channel=channel)
        

async def interject(message):
    if random.randint(0, 1):
        msg = "I'd just like to interject for a moment. What you're referring to as eroge, is in fact, erogay, or as I've recently taken to calling it, ero plus gay."
    else:
        msg = re.sub('eroge', '**erogay**', message.content)
    await message.channel.send(msg)
