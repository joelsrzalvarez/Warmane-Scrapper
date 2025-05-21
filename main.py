import discord
from discord import app_commands
from discord.ext import commands
import requests
import xml.etree.ElementTree as ET
import os
from dotenv import load_dotenv
import time
from keep_alive import keep_alive  # si estás usando Replit

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

REINOS_VALIDOS = ["Icecrown", "Blackrock", "Lordaeron"]
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

intents = discord.Intents.default()
intents.message_content = True

client = commands.Bot(command_prefix="!", intents=intents)

@client.event
async def on_ready():
    await client.tree.sync()
    print(f"✅ Bot conectado como {client.user}")

def obtener_icono(item_id):
    xml_url = f"https://www.wowhead.com/item={item_id}&xml"
    try:
        response = requests.get(xml_url, headers=HEADERS, timeout=5)
        if response.status_code == 200:
            root = ET.fromstring(response.text)
            icon_tag = root.find(".//icon")
            if icon_tag is not None:
                return f"https://wow.zamimg.com/images/wow/icons/large/{icon_tag.text}.jpg"
    except:
        pass
    return None

def obtener_datos_personaje(usuario, reino):
    url = f"https://armory.warmane.com/api/character/{usuario}/{reino}/summary"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None

@client.tree.command(name="status", description="Ver información general del personaje")
@app_commands.describe(usuario="Nombre del personaje", reino="Reino: Icecrown, Blackrock o Lordaeron")
async def status(interaction: discord.Interaction, usuario: str, reino: str):
    reino = reino.capitalize()
    if reino not in REINOS_VALIDOS:
        await interaction.response.send_message(f"❌ Reino inválido. Usa: {', '.join(REINOS_VALIDOS)}", ephemeral=True)
        return

    data = obtener_datos_personaje(usuario, reino)
    if not data:
        await interaction.response.send_message("❌ Personaje no encontrado.")
        return

    embed = discord.Embed(title=f"Status de {usuario} ({reino})", color=discord.Color.blue())
    embed.add_field(name="Clase", value=data['class'], inline=True)
    embed.add_field(name="Raza", value=data['race'], inline=True)
    embed.add_field(name="Nivel", value=data['level'], inline=True)
    embed.add_field(name="Facción", value=data['faction'], inline=True)
    embed.add_field(name="Online", value="✅ Sí" if data['online'] else "❌ No", inline=True)
    embed.add_field(name="Logros", value=data['achievementpoints'], inline=True)
    embed.add_field(name="Gremio", value=data['guild'] or "Sin gremio", inline=False)

    profesiones = data.get('professions', [])
    if profesiones:
        lista = ", ".join([f"{p['name']} ({p['skill']})" for p in profesiones])
        embed.add_field(name="Profesiones", value=lista, inline=False)
    else:
        embed.add_field(name="Profesiones", value="Ninguna", inline=False)

    await interaction.response.send_message(embed=embed)

@client.tree.command(name="info", description="Ver equipo del personaje")
@app_commands.describe(usuario="Nombre del personaje", reino="Reino: Icecrown, Blackrock o Lordaeron")
async def info(interaction: discord.Interaction, usuario: str, reino: str):
    reino = reino.capitalize()
    if reino not in REINOS_VALIDOS:
        await interaction.response.send_message(f"❌ Reino inválido. Usa: {', '.join(REINOS_VALIDOS)}", ephemeral=True)
        return

    data = obtener_datos_personaje(usuario, reino)
    if not data or not data.get("equipment"):
        await interaction.response.send_message("❌ No se pudo obtener el equipo del personaje.")
        return

    equipo = data["equipment"]
    embed = discord.Embed(title=f"Equipo de {usuario} ({reino})", color=discord.Color.dark_gold())

    for pieza in equipo:
        nombre = pieza.get("name")
        item_id = pieza.get("item")
        if not nombre or not item_id:
            continue
        icono = obtener_icono(item_id)
        if icono:
            embed.add_field(name=nombre, value=f"[Icono]({icono})", inline=True)
        else:
            embed.add_field(name=nombre, value="(sin icono)", inline=True)
        time.sleep(0.5)

    await interaction.response.send_message(embed=embed)

keep_alive()  # solo si usas Replit
client.run(TOKEN)
