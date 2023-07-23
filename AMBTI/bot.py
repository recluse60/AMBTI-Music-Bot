import discord
from discord.ext import commands
import youtube_dl
import re
import requests
import asyncio
from youtubesearchpython import VideosSearch


intents = discord.Intents.all()
intents.guilds = True
intents.messages = True
intents.voice_states = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Bot olarak giriş yapıldı: {bot.user}')

def after_play(error):
    if error:
        print('Oynatma hatası:', error)

@bot.command()
async def katıl(ctx):
    # Kullanıcının sesli kanala bağlı olduğundan emin olalım
    if ctx.author.voice:
        voice_channel = ctx.author.voice.channel
        voice_client = await voice_channel.connect()
        await ctx.send(f'Giriş yapıldı: {voice_channel}')
    else:
        await ctx.send('Sesli bir kanala bağlı değilsiniz.')




@bot.command()
async def çal(ctx, *, arg):
    if not arg:
        await ctx.send('Lütfen bir şarkı adı veya YouTube URL\'si girin!')
        return

    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }

        # YouTube'dan şarkı araması yapma ve şarkıyı çalma işlemleri
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            # Eğer gelen argüman bir YouTube URL'si ise, video_info içindeki bilgileri alalım
            if 'youtube.com' in arg or 'youtu.be' in arg:
                video_info = ydl.extract_info(arg, download=False)
                video_url = video_info['formats'][0]['url']
            else:
                # Eğer gelen argüman bir şarkı adı ise, YouTube'da aratarak video_url alalım
                search_url = f'https://www.youtube.com/results?search_query={arg}'
                response = requests.get(search_url)
                if response.status_code == 200:
                    content = response.content.decode('utf-8')
                    video_ids = re.findall(r"watch\?v=(\S{11})", content)
                    if video_ids:
                        video_url = f'https://www.youtube.com/watch?v={video_ids[0]}'
                    else:
                        await ctx.send('Arama sonuçları bulunamadı.')
                        return
                else:
                    await ctx.send('YouTube\'a bağlanırken bir hata oluştu.')
                    return

        # Kullanıcının sesli kanala bağlı olduğundan emin olalım
        if ctx.author.voice:
            sesli_kanal = ctx.author.voice.channel

            # Eğer bot zaten bir sesli kanala bağlıysa, bağlı olduğu kanalı kontrol edelim
            if ctx.guild.voice_client and ctx.guild.voice_client.channel != sesli_kanal:
                await ctx.guild.voice_client.disconnect()

            # Şarkıyı sesli kanalda çalma
            sesli_istemci = None
            if not ctx.guild.voice_client:
                sesli_istemci = await sesli_kanal.connect()

            if sesli_istemci:
                sesli_istemci.play(discord.FFmpegPCMAudio(executable=r"C:\ffmpeg\bin\ffmpeg.exe", source=video_url), after=after_play)
                await ctx.send(f'Şimdi çalınıyor: {video_info["title"]}')
            else:
                await ctx.send('Sesli kanala bağlanırken bir hata oluştu.')
        else:
            await ctx.send('Sesli bir kanala bağlı değilsiniz.')
    except Exception as e:
        print('Hata:', e)
        await ctx.send('Bir hata oluştu.')
@bot.command()
async def ara(ctx, *, sorgu):
    try:
        # YouTube'da arama yapın
        videos_search = VideosSearch(sorgu, limit=5)
        results = videos_search.result()

        if 'result' in results and len(results['result']) > 0:
            videolar = results['result']
            sarkilar = {}

            for i, video in enumerate(videolar):
                sarkilar[i + 1] = video['link']
                await ctx.send(f"{i + 1}. {video['title']}")

            await ctx.send("Lütfen çalmak istediğiniz şarkının numarasını yazın.")

            def check(mesaj):
                return mesaj.author == ctx.author and mesaj.channel == ctx.channel

            try:
                numara_mesaji = await bot.wait_for('message', check=check, timeout=30)
                secilen_numara = int(numara_mesaji.content)

                if secilen_numara in sarkilar:
                    secilen_sarki_url = sarkilar[secilen_numara]
                    await ctx.invoke(bot.get_command('çal'), arg=secilen_sarki_url)
                else:
                    await ctx.send("Geçerli bir şarkı numarası girin.")
            except ValueError:
                await ctx.send("Geçerli bir sayı girin.")
            except asyncio.TimeoutError:
                await ctx.send("İşlem zaman aşımına uğradı. Lütfen daha hızlı seçim yapın.")
        else:
            await ctx.send("Aradığınız kriterlerle eşleşen bir sonuç bulunamadı.")
    except Exception as e:
        print('Hata:', e)
        await ctx.send("Bir hata oluştu.")
@bot.command()
async def ayril(ctx):
    # Bot sesli kanaldaysa, kanaldan ayrıl
    if ctx.guild.voice_client:
        await ctx.guild.voice_client.disconnect()
        await ctx.send("Kanaldan ayrıldım.")
    else:
        await ctx.send("Zaten bir sesli kanalda değilim.")

bot.run('YOUR_DISCORD_TOKEN')
