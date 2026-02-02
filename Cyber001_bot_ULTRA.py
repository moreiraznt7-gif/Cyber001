# Cyber001 BOT - SINGLE FILE (SQLite)
# BOT PROFISSIONAL COMPLETO
# Tudo em embed | Prefixo c1!
# SEM painel web | SEM criação automática de cargos base
# Donos configurados

import discord
from discord.ext import commands, tasks
import aiosqlite
import random
import time
import asyncio

TOKEN = "MTQxMjc3Mzc0NjQ2MDE5NjkyNQ.GyJVOH.A2bzsCMQFBsgMz5PjcE7aGfSxIxFHX2QsSRN9o"
OPENAI_KEY = "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"

OWNERS = [1140075729191698524, 665248108351062087]

LOG_CHANNELS = {
    "moderacao": None,
    "antiraid": None,
    "antispam": None,
    "economia": None,
    "warns": None,
    "geral": None
}

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="c1!", intents=intents)

# ================= DATABASE =================
async def init_db():
    async with aiosqlite.connect("bot.db") as db:
        await db.execute("CREATE TABLE IF NOT EXISTS economy (user INTEGER PRIMARY KEY, money INTEGER)")
        await db.execute("CREATE TABLE IF NOT EXISTS warns (user INTEGER PRIMARY KEY, warns INTEGER)")
        await db.execute("CREATE TABLE IF NOT EXISTS xp (user INTEGER PRIMARY KEY, xp INTEGER, level INTEGER)")
        await db.execute("CREATE TABLE IF NOT EXISTS shop (item TEXT, price INTEGER)")
        await db.commit()

# ================= LOG SYSTEM =================
async def send_log(guild, category, embed):
    channel_id = LOG_CHANNELS.get(category)
    if channel_id:
        channel = guild.get_channel(channel_id)
        if channel:
            await channel.send(embed=embed)

# ================= READY =================
@bot.event
async def on_ready():
    await init_db()
    await bot.tree.sync()
    anti_raid_join.start()
    print(f"🔥 Cyber001 ligado como {bot.user}")

# ================= WARNS / PUNIÇÕES =================
async def add_warn(member, reason):
    async with aiosqlite.connect("bot.db") as db:
        await db.execute("INSERT OR IGNORE INTO warns VALUES (?,0)", (member.id,))
        await db.execute("UPDATE warns SET warns = warns + 1 WHERE user = ?", (member.id,))
        cur = await db.execute("SELECT warns FROM warns WHERE user = ?", (member.id,))
        warns = (await cur.fetchone())[0]
        await db.commit()

    embed = discord.Embed(
        title="⚠️ Advertência",
        description=f"{member.mention} recebeu um warn.
Motivo: {reason}
Total: {warns}",
        color=discord.Color.orange()
    )
    await send_log(member.guild, "warns", embed)

    if warns == 3:
        await member.timeout(discord.utils.utcnow() + discord.timedelta(minutes=10))
    elif warns == 5:
        await member.kick(reason="5 advertências")
    elif warns >= 7:
        await member.ban(reason="7 advertências")

# ================= ANTI-SPAM =================
user_messages = {}

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    now = time.time()
    msgs = user_messages.setdefault(message.author.id, [])
    msgs.append(now)
    user_messages[message.author.id] = [t for t in msgs if now - t < 5]

    if len(user_messages[message.author.id]) > 6:
        await message.delete()
        await add_warn(message.author, "Spam/Flood")

        embed = discord.Embed(
            title="🛡️ Anti-Spam",
            description=f"{message.author} flood detectado",
            color=discord.Color.red()
        )
        await send_log(message.guild, "antispam", embed)

    await bot.process_commands(message)

# ================= ANTI-RAID JOIN =================
join_cache = []

@bot.event
async def on_member_join(member):
    join_cache.append(time.time())
    join_cache[:] = [t for t in join_cache if time.time() - t < 10]

    if len(join_cache) >= 6:
        await member.guild.edit(verification_level=discord.VerificationLevel.high)

        embed = discord.Embed(
            title="🚨 Anti-Raid",
            description="Entrada massiva detectada. Proteção ativada.",
            color=discord.Color.red()
        )
        await send_log(member.guild, "antiraid", embed)

# ================= VERIFICAÇÃO =================
@bot.command()
async def verificar(ctx):
    role = discord.utils.get(ctx.guild.roles, name="✅ Membro Verificado")
    if role:
        await ctx.author.add_roles(role)
        embed = discord.Embed(
            title="🔐 Verificação",
            description="Você foi verificado com sucesso!",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

# ================= MODERAÇÃO =================
@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, membro: discord.Member, *, motivo="Não informado"):
    await membro.ban(reason=motivo)
    embed = discord.Embed(
        title="🔨 Ban",
        description=f"{membro} banido.
Motivo: {motivo}",
        color=discord.Color.dark_red()
    )
    await ctx.send(embed=embed)
    await send_log(ctx.guild, "moderacao", embed)

# ================= ECONOMIA =================
@bot.command()
async def saldo(ctx):
    async with aiosqlite.connect("bot.db") as db:
        cur = await db.execute("SELECT money FROM economy WHERE user = ?", (ctx.author.id,))
        row = await cur.fetchone()
        money = row[0] if row else 0
    await ctx.send(embed=discord.Embed(
        title="💰 Saldo",
        description=f"{money} moedas"
    ))

@bot.command()
async def roubar(ctx):
    valor = random.randint(10, 40)
    async with aiosqlite.connect("bot.db") as db:
        await db.execute("INSERT OR IGNORE INTO economy VALUES (?,0)", (ctx.author.id,))
        await db.execute("UPDATE economy SET money = money + ? WHERE user = ?", (valor, ctx.author.id))
        await db.commit()
    embed = discord.Embed(
        title="🍦 Caminhão de Sorvete",
        description=f"Você roubou **{valor} moedas**",
        color=discord.Color.blue()
    )
    await ctx.send(embed=embed)
    await send_log(ctx.guild, "economia", embed)

@bot.command()
async def ranking(ctx):
    async with aiosqlite.connect("bot.db") as db:
        cur = await db.execute("SELECT user, money FROM economy ORDER BY money DESC LIMIT 10")
        rows = await cur.fetchall()

    desc = ""
    for i, (u, m) in enumerate(rows, start=1):
        desc += f"{i}. <@{u}> — {m} moedas
"

    await ctx.send(embed=discord.Embed(
        title="🏆 Ranking de Riqueza",
        description=desc or "Sem dados"
    ))

# ================= XP =================
@bot.event
async def on_message_edit(before, after):
    if after.author.bot:
        return

    async with aiosqlite.connect("bot.db") as db:
        await db.execute("INSERT OR IGNORE INTO xp VALUES (?,0,1)", (after.author.id,))
        await db.execute("UPDATE xp SET xp = xp + 5 WHERE user = ?", (after.author.id,))
        await db.commit()

# ================= TICKETS =================
@bot.command()
async def ticket(ctx):
    overwrites = {
        ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
        ctx.author: discord.PermissionOverwrite(read_messages=True)
    }
    channel = await ctx.guild.create_text_channel(
        f"ticket-{ctx.author.name}", overwrites=overwrites
    )
    await channel.send(embed=discord.Embed(
        title="🎫 Ticket aberto",
        description="Explique seu problema."
    ))

# ================= IA =================
@bot.command()
async def ia(ctx, *, pergunta):
    await ctx.send(embed=discord.Embed(
        title="🧠 IA Cyber001",
        description="Sou a IA do Cyber001. Direta, firme e focada em organização, segurança e estratégia."
    ))

bot.run(TOKEN)
