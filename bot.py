import discord
from discord.ext import commands
from discord import app_commands, ui
import json
import os

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

CONFIG_FILE = "config.json"

def ucitaj_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"autorole_id": None, "prijave_kanal": None, "bugovi_kanal": None, "prijedlozi_kanal": None}

def spremi_config(data):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

config = ucitaj_config()

@bot.event
async def on_ready():
    print(f"==========================================")
    print(f"Bot {bot.user} je spreman i aktivan za Visual Community!")
    print(f"==========================================")
    try:
        synced = await bot.tree.sync()
        print(f"Uspješno sinkronizirano {len(synced)} Slash (/) komandi.")
    except Exception as e:
        print(f"Greška pri sinkronizaciji slash komandi: {e}")

# ==========================================
# 1. AUTOMATSKE ULOGE
# ==========================================
@bot.event
async def on_member_join(member):
    if config.get("autorole_id"):
        role = member.guild.get_role(config["autorole_id"])
        if role:
            try:
                await member.add_roles(role)
            except Exception as e:
                print(f"Greška pri dodavanju uloge: {e}")

@bot.command(name="postavi_autorole")
@commands.has_permissions(administrator=True)
async def postavi_autorole_cmd(ctx, uloga: discord.Role):
    config["autorole_id"] = uloga.id
    spremi_config(config)
    await ctx.send(f"✅ Automatska uloga postavljena na: {uloga.mention}")

# ==========================================
# 2. PODEŠAVANJE KANALA
# ==========================================
@bot.command(name="postavi_kanal")
@commands.has_permissions(administrator=True)
async def postavi_kanal_cmd(ctx, vrsta: str, kanal: discord.TextChannel):
    vrsta = vrsta.lower()
    if vrsta in ["prijave", "staff"]:
        config["prijave_kanal"] = kanal.id
        k_ime = "Prijave za Staff"
    elif vrsta in ["bug", "bugovi"]:
        config["bugovi_kanal"] = kanal.id
        k_ime = "Prijave Bugova"
    elif vrsta in ["prijedlog", "prijedlozi"]:
        config["prijedlozi_kanal"] = kanal.id
        k_ime = "Prijedlozi"
    else:
        await ctx.send("❌ Nepoznata vrsta! Koristi: prijave, bugovi ili prijedlozi.")
        return

    spremi_config(config)
    await ctx.send(f"✅ Kanal za *{k_ime}* postavljen na {kanal.mention}")

# ==========================================
# 3. UREĐIVANJE I SLANJE PORUKA
# ==========================================
@bot.command(name="posalji")
@commands.has_permissions(administrator=True)
async def posalji_cmd(ctx, kanal: discord.TextChannel, *, poruka: str):
    if "|" in poruka:
        naslov, tekst = poruka.split("|", 1)
    else:
        naslov = "Visual Community Obavijest"
        tekst = poruka

    embed = discord.Embed(title=naslov.strip(), description=tekst.strip(), color=discord.Color.blue())
    embed.set_footer(text="Visual Community Management")
    await kanal.send(embed=embed)
    await ctx.send(f"✅ Obavijest poslata u {kanal.mention}")

@bot.command(name="editporuka")
@commands.has_permissions(administrator=True)
async def editporuka_cmd(ctx, kanal: discord.TextChannel, message_id: int, *, novi_sadrzaj: str):
    try:
        msg = await kanal.fetch_message(message_id)
        if msg.author != bot.user:
            await ctx.send("❌ Mogu uređivati samo poruke koje je poslao ovaj bot!")
            return

        if "|" in novi_sadrzaj:
            naslov, tekst = novi_sadrzaj.split("|", 1)
        else:
            naslov = "Visual Community Obavijest"
            tekst = novi_sadrzaj

        embed = discord.Embed(title=naslov.strip(), description=tekst.strip(), color=discord.Color.blue())
        embed.set_footer(text="Visual Community Management (Ažurirano)")

        await msg.edit(embed=embed)
        await ctx.send("✅ Poruka uspješno izmijenjena!")
    except Exception as e:
        await ctx.send(f"❌ Greška pri uređivanju poruke: {e}")

# ==========================================
# 4. CENOVNIK & UPDATE
# ==========================================
@bot.command(name="cenovnik")
async def cenovnik_cmd(ctx):
    embed = discord.Embed(
        title="💳 Visual Community • Cjenik Usluga & VIP Paketa",
        description="Aktualne cijene VIP pogodnosti i donacija na serveru:",
        color=discord.Color.gold()
    )
    embed.add_field(name="⭐ VIP Bronze", value="• Cijena: 5€ / 10 KM\n• Custom skin, VIP chat, 1.5x zarada", inline=False)
    embed.add_field(name="⭐⭐ VIP Silver", value="• Cijena: 10€ / 20 KM\n• Unikatno vozilo, 2x zarada, VIP garaza", inline=False)
    embed.add_field(name="⭐⭐⭐ VIP Gold", value="• Cijena: 15€ / 30 KM\n• Custom kuca, 3x zarada, Unikatni Tag", inline=False)
    embed.add_field(name="💰 Novac / Donacije", value="• 1.000.000$ = 3€\n• 5.000.000$ = 10€", inline=False)
    embed.set_footer(text="Za kupovinu se obratite Upravi servera.")
    await ctx.send(embed=embed)

@bot.command(name="update")
@commands.has_permissions(administrator=True)
async def update_cmd(ctx, verzija: str, *, detalji: str):
    embed = discord.Embed(
        title=f"🚀 Visual Community • Update {verzija}",
        description=detalji,
        color=discord.Color.green()
    )
    embed.set_footer(text="Visual Community Development Team")
    await ctx.send(embed=embed)

# ==========================================
# 5. FORME ZA KONKURSE, BUGOVE I PRIJEDLOGE (MODALS)
# ==========================================
class KonkursModal(ui.Modal, title="Prijava za Staff (Admin/Helper)"):
    pozicija = ui.TextInput(label="Pozicija", placeholder="Npr. Helper ili Admin", required=True)
    ic_ime = ui.TextInput(label="Ime_Prezime (u igri)", placeholder="Npr. Marko_Markovic", required=True)
    godine = ui.TextInput(label="Godine", placeholder="Npr. 17", required=True, max_length=2)
    iskustvo = ui.TextInput(label="Iskustvo", style=discord.TextStyle.paragraph, required=True)
    zasto_ti = ui.TextInput(label="Zašto baš ti?", style=discord.TextStyle.paragraph, required=True)

    async def on_submit(self, interaction: discord.Interaction):
        kanal_id = config.get("prijave_kanal")
        if not kanal_id:
            await interaction.response.send_message("Kanal za prijave nije podešen! Postavite ga preko !postavi_kanal prijave #kanal.", ephemeral=True)
            return
        kanal = interaction.guild.get_channel(kanal_id)

        embed = discord.Embed(title=f"📥 PRIJAVA ZA STAFF • {self.pozicija.value}", color=discord.Color.blue())
        embed.add_field(name="Korisnik", value=interaction.user.mention, inline=True)
        embed.add_field(name="IC Ime", value=self.ic_ime.value, inline=True)
        embed.add_field(name="Godine", value=self.godine.value, inline=True)
        embed.add_field(name="Iskustvo", value=self.iskustvo.value, inline=False)
        embed.add_field(name="Zašto on?", value=self.zasto_ti.value, inline=False)

        await kanal.send(embed=embed)
        await interaction.response.send_message("Vaša prijava je uspješno poslana!", ephemeral=True)

@bot.tree.command(name="konkurs", description="Otvara formu za prijavu za Staff")
async def konkurs_slash(interaction: discord.Interaction):
    await interaction.response.send_modal(KonkursModal())

class BugModal(ui.Modal, title="Prijava Buga / Greške"):
    naziv = ui.TextInput(label="Kratak opis buga", placeholder="Npr. Ne radi komanda /portfolio", required=True)
    detalji = ui.TextInput(label="Detaljan opis", style=discord.TextStyle.paragraph, required=True)

    async def on_submit(self, interaction: discord.Interaction):
        kanal_id = config.get("bugovi_kanal")
        if not kanal_id:
            await interaction.response.send_message("Kanal za bugove nije podešen!", ephemeral=True)
            return
        kanal = interaction.guild.get_channel(kanal_id)

        embed = discord.Embed(title=f"🐛 BUG: {self.naziv.value}", description=self.detalji.value, color=discord.Color.red())
        embed.add_field(name="Prijavio", value=interaction.user.mention)
        msg = await kanal.send(embed=embed)
        await msg.add_reaction("🔴")
        await interaction.response.send_message("Hvala na prijavi buga!", ephemeral=True)

@bot.tree.command(name="bug", description="Prijavi bug ili grešku na serveru")
async def bug_slash(interaction: discord.Interaction):
    await interaction.response.send_modal(BugModal())

class PrijedlogModal(ui.Modal, title="Novi Prijedlog"):
    naslov = ui.TextInput(label="Naslov prijedloga", placeholder="Npr. Novi posao: Dostavljač", required=True)
    opis = ui.TextInput(label="Opis prijedloga", style=discord.TextStyle.paragraph, required=True)

    async def on_submit(self, interaction: discord.Interaction):
        kanal_id = config.get("prijedlozi_kanal")
        if not kanal_id:
            await interaction.response.send_message("Kanal za prijedloge nije podešen!", ephemeral=True)
            return
        kanal = interaction.guild.get_channel(kanal_id)

        embed = discord.Embed(title=f"💡 PRIJEDLOG: {self.naslov.value}", description=self.opis.value, color=discord.Color.purple())
        embed.add_field(name="Predložio", value=interaction.user.mention)
        msg = await kanal.send(embed=embed)
        await msg.add_reaction("👍")
        await msg.add_reaction("👎")
        await interaction.response.send_message("Vaš prijedlog je objavljen!", ephemeral=True)

@bot.tree.command(name="prijedlog", description="Predložite ideju za server")
async def prijedlog_slash(interaction: discord.Interaction):
    await interaction.response.send_modal(PrijedlogModal())

# ==========================================
# 6. MODERACIJA
# ==========================================
@bot.command(name="clear")
@commands.has_permissions(manage_messages=True)
async def clear_cmd(ctx, broj: int):
    await ctx.channel.purge(limit=broj + 1)
    await ctx.send(f"🧹 Obrisano {broj} poruka.", delete_after=5)

# POKRETANJE BOTA
bot.run("MTQwNDI5MDMyMTQyNDA1NjM1MQ.GZd5s3.2wzTF_mjSo5siujMhhsv3g0HNOx2Pst8C7L04A")