import discord
import asyncio
from datetime import timedelta, time, datetime
from pymongo import MongoClient
from discord import app_commands
from discord.ext import commands

Bot = commands.Bot(command_prefix="p!", intents=discord.Intents.all(), help_command=None)

#DATABASE

mongo = MongoClient("mongodb://localhost:27017")

db = mongo.role

gezegenColl = db.planets
yapiColl = db.buildings
factionColl = db.factions

#FONKSİYONLAR

async def createEmbed(desc, titlee, footer="", color=discord.Colour.blurple(), thumbnail="https://cdn.discordapp.com/attachments/1385373758268637197/1390386800866099220/logoroleplay.png?ex=6868121d&is=6866c09d&hm=3067e9e92a9b62a8e7e0072a615f4759c62c100d445ba0be2b977eebb394f2f6&", image="https://cdn.discordapp.com/attachments/1385373758268637196/1388270751278174400/image.png?ex=68605f63&is=685f0de3&hm=54bda5e7f6ce13bd0397272f464fb4c7efb56b627d9cc7237e34e87f153104c8&"):
    embed = discord.Embed(
        colour=color,
        description=desc,
        title=titlee
    )

    embed.set_footer(text=footer)
    embed.set_author(name="Parody™ Roleplay")

    embed.set_thumbnail(url=thumbnail)
    embed.set_image(url=image)
    return embed

async def insa_bitir(bina, gezegen):
    print("inşaat bitti")
    gezegenColl.update_one({"channel":gezegen}, {"$push":{"buildings":bina}})
    guild = Bot.get_guild(1385373757572645097)
    channel = guild.get_channel(gezegen)
    embed = await createEmbed(f"**{bina}** yapısı, başarıyla inşa edildi.", "**İnşaat Bitti!**", color=discord.Colour.green())
    await channel.send(embed=embed)

    statlar = [
        "stability", "crime", "resistance", 
        "resource", "food", "tax", "mining", "trade"
    ]

    building = yapiColl.find_one({"name":bina})
    etkiler = {
        stat: building[stat]
        for stat in statlar
        if building.get(stat) is not None
    }

    if etkiler:
        gezegenColl.update_one(
            {"channel": gezegen},
            {"$inc": etkiler}
        )

async def bina_zamanlayici(minute:int, bina, gezegen):
    await Bot.wait_until_ready()
    while not Bot.is_closed():
        print(f"{minute} dakika sonra inşa bitirilecek.")
        await asyncio.sleep(minute * 60)
        await insa_bitir(bina, gezegen)
        break

async def paradagit():
    guild = Bot.get_guild(1385373757572645097)
    gezegenler = gezegenColl.find({})
    devletler = factionColl.find({})
    userColl = db.economy.users
    
    for gezegen in gezegenler:
        income = (gezegen["tax"]+gezegen["mining"]+gezegen["trade"]) - (gezegen["food"]+gezegen["resource"])
        gezegenColl.update_one(gezegen, {"$inc":{"money":income}})

        if gezegen["admin"] == 0:
            print("Gezegen lideri bulunamadı\n" + gezegen["name"])
            return

    for devlet in devletler:
        income = (devlet["tax"]+devlet["mining"]+devlet["trade"]) - (devlet["resource"]+devlet["welfare"]+devlet["mil"])
        factionColl.update_one(devlet, {"$inc":{"money":income}})

        if devlet["ruler"] == 0:
            print("Devlet lideri bulunamadı.")
            return

async def gelir_zamanlayici():
    await Bot.wait_until_ready()
    while not Bot.is_closed():
        now = datetime.now()

        hedef_zaman = datetime.combine(now.date(), time.min)
        if now >= hedef_zaman:
            hedef_zaman += timedelta(days=1)
        bekleme_suresi = (hedef_zaman - now).total_seconds()

        print(f"{bekleme_suresi} saniye sonra para dağıtılacak.")
        await asyncio.sleep(bekleme_suresi)

        await paradagit()


#EVENTLER

@Bot.event
async def on_ready():
    await Bot.loop.create_task(gelir_zamanlayici())
    await Bot.change_presence(status=discord.Status.do_not_disturb, activity=discord.Activity(type=discord.ActivityType.watching, name="Made by Soverine"))
    await Bot.tree.sync(guild=discord.Object(id=1385373757572645097))
    print("Bot hazır!")

#KOMUTLAR

#GEZEGEN KOMUTLARI

@Bot.tree.command(name="gezegen-ekle", description="Rol için gezegen ekler.", guild=discord.Object(id=1385373757572645097))
@app_commands.describe(channel="Gezegenin bulunduğu kanal.", name="Gezegenin ismi.", ruler="Gezegenin bağlı olduğu fraksiyon", 
                       stability="Gezegenin istikrarı", crime="Suç oranı", resistance="İsyan oranı",
                       resource="Kaynak gideri", food="Besin gideri",
                       tax="Vergi geliri", mining="Maden geliri", trade="Ticari gelir",
                       money="Başlangıç parası", desc="Açıklama", image="fotorğaf urlsi")
async def gezegenekle(interaction: discord.Interaction, channel:discord.TextChannel, name:str, ruler:discord.Role, stability:int, crime:int, resistance:int, resource:int, food:int,tax:int,mining:int,trade:int,money:int,desc:str, image:str):
    gezegenColl.insert_one({"channel":channel.id, "name":name, "ruler":ruler.id, 
                            "stability":stability, "crime":crime, "resistance":resistance,
                            "resource":resource, "food":food,
                            "tax":tax, "mining":mining, "trade":trade,
                            "money":money, "description":desc, "image":image,
                            "admin":0, "buildings":[], "stations":[]})
    embed = await createEmbed(desc=desc, titlee=name,image=image)
    await channel.send(embed=embed)

@Bot.tree.command(name="gezegen-yoneticisi-ayarla", description="Rol için gezegen ekler.", guild=discord.Object(id=1385373757572645097))
@app_commands.describe(channel="Gezegen", user="Kullanıcı")
async def gyoneticiayarla(interaction: discord.Interaction, channel:discord.TextChannel, user: discord.Member):
    if mongo.general.users.find_one({"user":user.id}) == None:
        await interaction.response.send_message("Seçtiğiniz kullanıcının kaydı yok.")
    gezegenColl.update_one({"channel":channel.id}, {"$set":{"admin":user.id}})
    await interaction.response.send_message(f"{channel.mention} **gezegeninin yöneticisi, {user.mention} olarak ayarlandı.**")

@Bot.tree.command(name="gezegen-stat", description="Seçtiğiniz gezegenin statlarını gösterir.", guild=discord.Object(id=1385373757572645097))
@app_commands.describe(channel="Gezegen")
async def gezegenstat(interaction: discord.Interaction, channel: discord.TextChannel):
    gezegen = gezegenColl.find_one({"channel":channel.id})
    guild = Bot.get_guild(1385373757572645097)
    role = guild.get_role(gezegen["ruler"])
    desc = f"**Bağlılık:** {role.name}\n**İstikrar:** %{gezegen["stability"]}\n**Suç Oranı:** %{gezegen["crime"]}\n**İsyan Oranı:** %{gezegen["resistance"]}\n\n**Kaynak Giderleri:** {gezegen["resource"]} Kredi\n**Besin Giderleri:** {gezegen["food"]} Kredi\n**Vergi Gelirleri:** {gezegen["tax"]} Kredi\n**Maden Gelirleri:** {gezegen["mining"]} Kredi\n**Ticari Gelirler:** {gezegen["trade"]} Kredi\n**Yönetim Bütçesi:** {gezegen["money"]} Kredi"
    embed = await createEmbed(desc,f"**{gezegen["name"]}**")
    await interaction.response.send_message(embed=embed)

@Bot.tree.command(name="gezegen-para-ekle", description="Seçtiğiniz gezegenin bütçesine para ekler.", guild=discord.Object(id=1385373757572645097))
@app_commands.describe(channel="Gezegen", money="Para miktarı")
async def gezegenparaelkle(interaction: discord.Interaction, channel: discord.TextChannel, money:int):
    gezegenColl.update_one({"channel":channel.id},{"$inc":{"money":money}})
    sonuc = gezegenColl.find_one({"channel":channel.id})
    embed = await createEmbed(f"{sonuc["name"]} gezegeninin bütçesine {money} kredi eklendi. Gezegenin yeni bütçesi: {sonuc["money"]}", "Gezegen Bütçesi Düzenlendi!", color=discord.Colour.green())
    await interaction.response.send_message(embed=embed)

#YAPI KOMUTLARI

@Bot.tree.command(name="yapilar", description="Seçtiğiniz gezegendeki yapıları gösterir.", guild=discord.Object(id=1385373757572645097))
@app_commands.describe(planet="Gezegen kanalı")
async def yapilar(interaction: discord.Interaction, planet: discord.TextChannel):
    gezegen = gezegenColl.find_one({"channel":planet.id})

    desc = f"**{gezegen["name"]} gezegenindeki yapılar:\n\n**"
    for yapi in gezegen["buildings"]:
        desc += f"{yapi}\n"

    embed = await createEmbed(desc, "**Yapı Listesi**")
    await interaction.response.send_message(embed=embed)

@Bot.tree.command(name="bina-ekle", description="Veritabanına bina ekler.", guild=discord.Object(id=1385373757572645097))
@app_commands.describe(name="Bina adı", price="Üretim ücreti", duration="Üretim süresi(dakika)", desc="Açıklama",
                       stability="Gezegen istikrarına etkisi", crime="Suç oranına etkisi", resistance="İsyan oranına etkisi",
                       resource="Kaynak giderine etkisi", food="Besin giderine etkisi",
                       tax="Vergi gelirine etkisi", mining="Maden gelirine etkisi", trade="Ticari gelirine etkisi",)
async def binaekle(interaction: discord.Interaction, name:str, price:int, duration:int, desc:str, stability:int=None, crime:int=None, resistance:int=None,resource:int=None,food:int=None,tax:int=None,mining:int=None,trade:int=None):
    yapiColl.insert_one({"name":name, "price":price, "duration":duration,"description":desc, 
                         "stability":stability, "crime":crime, "resistance":resistance,"resource":resource, "food":food, "tax":tax, "mining":mining, "trade":trade})
    embed = await createEmbed(f"**Yapı İsmi:** {name}\n**Açıklama:** {desc}\n**Ücret:** {price}\n**Yapım Süresi:** {duration}dk", "Yapı Oluşturuldu!", color=discord.Colour.green())
    await interaction.response.send_message(embed=embed)

@Bot.tree.command(name="insa-et", description="Komutu kullandığınız gezegenin yöneticisi olmanız durumunda gezegende bir yapı inşası başlatır.", guild=discord.Object(id=1385373757572645097))
@app_commands.describe(building="Yapı adı")
async def insaet(interaction: discord.Interaction, building:str):
    bina = yapiColl.find_one({"name":building})
    gezegen = gezegenColl.find_one({"channel":interaction.channel_id,"admin":interaction.user.id})
    if gezegen["money"] < bina["price"]:
        await interaction.response.send_message(f"**Bu bina için paranız yetmiyor...\nBina Ücreti: {bina["price"]}**")
        return

    gezegenColl.update_one({"channel": interaction.channel_id}, {"$inc": {"money": -bina["price"]}})
    embed = await createEmbed(f"{bina["name"]} inşaatine başlandı. İnşaat {bina["duration"]}dk sonra sona erecek. Bina ücreti: {bina["price"]}", "**İnşaat Başladı!**")
    await interaction.response.send_message(embed=embed)
    await bina_zamanlayici(bina["duration"], bina["name"], interaction.channel_id)

#FRAKSİYON KOMUTLARI

@Bot.tree.command(name="fraksiyon-ekle", description="Veritabanına girdiğiniz bilgilere göre fraksiyon ekler.", guild=discord.Object(id=1385373757572645097))
@app_commands.describe(faction="Fraksiyon adı",money="Fraksiyon bütçesi", 
                       trade="Ticari gelir", tax="Vergi geliri", mining="Maden geliri",
                       resource="Kaynak giderleri", welfare="Halk yararına giderler",
                       stability="İstikrar seviyesi", warsup="Savaş desteği",
                       size="Minör/Süper Minör/Majör", role="Fraksiyon rolü")
async def fraksiyonekle(interaction: discord.Interaction, faction:str, money:int, 
                        trade:int, tax:int, mining:int,
                        resource:int, welfare:int,
                        stability:int, warsup:int,
                        size:str, role:discord.Role):
    factionColl.insert_one({
        "faction":faction, "money":money,
        "trade":trade, "tax":tax, "mining":mining,
        "resource":resource, "welfare":welfare, "mil":0,
        "stability":stability, "warsup":warsup,
        "size":size, "role":role.id, "military":{},
        "ruler":0
        })
    embed = await createEmbed(f"**Ekonomi\n----------------------\n** Ticari Gelirler: {trade} Kredi\nVergi Gelirleri: {tax} Kredi\nMaden Gelirleri: {mining} Kredi\n\nKaynak Giderleri: {resource} Kredi\nHalk Yararına Giderler: {welfare} Kredi\nAskeri Bakım Giderleri: Ayarlanmadı\n\n**İstatistikler\n----------------------**\nİstikrar Seviyesi: {stability}\nSavaş Desteği: {warsup}\nDevlet Büyüklüğü: {size}\n\n**Askeriye\n----------------------**\nAskeri birlikler ayarlanmadı, lütfen /fraksiyon-askeriye-ayarla komutunu kullanınız.", f"**{faction} Fraksiyonu Oluşturuldu.**")
    await interaction.response.send_message(embed=embed)

@Bot.tree.command(name="fraksiyon-askeriye-ayarla", description="Kayıtlı fraksiyonlardan birinin askeriyesini ayarlar.", guild=discord.Object(id=1385373757572645097))
@app_commands.describe(faction="Fraksiyon adı",
                       dretnot="Dretnot sayısı", bcruiser="Savaş kruvazörü sayısı", sdestroyer="Yıldız destroyeri sayısı", cruiser="Kruvazör sayısı",
                       heavy="Ağır askeri araç sayısı", medium="Orta askeri araç sayısı", light="Hafif askeri araç sayısı",
                       special="Özel kuvvet sayısı", hsoldier="Ağır piyade sayısı", soldier="Piyade sayısı",
                       soldier_cost="Trooper'ların birlik başına maaliyeti")
async def fraksyionaskeriye(interaction:discord.Interaction, faction:str,
                             dretnot:int, bcruiser:int, sdestroyer:int, cruiser:int,
                            heavy:int, medium:int, light:int,
                            special:int, hsoldier:int, soldier:int,
                            soldier_cost:int):
    price = (dretnot*200000000) + (bcruiser*90000000) + (sdestroyer*50000000) + (cruiser*8000000) + (heavy*130000) + (medium*25000) + (light*5000) + (special*2000) + (hsoldier*1000) + (soldier*soldier_cost) 
    factionColl.update_one({"faction":faction}, {"$set":{"military":{"dretnot":dretnot, "bcruiser":bcruiser, "sdestroyer":sdestroyer, "cruiser":cruiser,
                                                                     "heavy": heavy,"medium": medium, "light": light, "special":special, "hsoldier": hsoldier, "soldier":soldier, "soldier_cost":soldier_cost},"mil":price}})
    desc = f"""**__Filo Sayısı:__**
    🛠️ **Dretnotlar**: {dretnot} adet *(x 200.000.000 kredi)*
    🛠️ **Savaş Kruvazörleri**: {bcruiser} adet *(x 90.000.000 kredi)*
    🛠️ **Yıldız Destroyerleri**: {sdestroyer} adet *(x 50.000.000 kredi)*
    🛠️ **Kruvazörler**: {cruiser} adet *(x 8.000.000 kredi)*

    **__Askerî Araç Sayısı:__**
    🚜 **Ağır Araçlar**: {heavy} adet *(x 130.000 kredi)*
    🚛 **Orta Araçlar**: {medium} adet *(x 25.000 kredi)*
    🚙 **Hafif Araçlar**: {light} adet *(x 5.000 kredi)*

    **__Asker Sayısı:__**
    🎯 **Özel Kuvvetler**: {special} asker *(x 2.000 kredi)*
    🪖 **Ağır Piyadeler**: {hsoldier} asker *(x 1.000 kredi)*
    👥 **Piyadeler**: {soldier} asker *(x {soldier_cost} kredi)*

    💸 **Toplam Yıllık Askerî Bakım Gideri**: **{price:,} kredi**
    """
    embed = await createEmbed(desc, titlee=f"**{faction} Askeriyesi Ayarlandı**", color=discord.Colour.green())
    await interaction.response.send_message(embed=embed)

@Bot.tree.command(name="fraksiyon-bilgi", description="Belirtilen fraksiyonun tüm bilgilerini listeler.", guild=discord.Object(id=1385373757572645097))
@app_commands.describe(faction="Bilgileri gösterilecek fraksiyon adı")
async def fraksiyonbilgi(interaction: discord.Interaction, faction: str):
    veri = factionColl.find_one({"faction": faction})
    if not veri:
        await interaction.response.send_message("Bu isimde bir fraksiyon bulunamadı.")
        return

    role_mention = f"<@&{veri['role']}>"
    mil = veri.get("military", {})

    # Askeri veriler
    dretnot = mil.get("dretnot", 0)
    bcruiser = mil.get("bcruiser", 0)
    sdestroyer = mil.get("sdestroyer", 0)
    cruiser = mil.get("cruiser", 0)
    heavy = mil.get("heavy", 0)
    medium = mil.get("medium", 0)
    light = mil.get("light", 0)
    special = mil.get("special", 0)
    hsoldier = mil.get("hsoldier", 0)
    soldier = mil.get("soldier", 0)
    soldier_cost = mil.get("soldier_cost", 0)
    military_cost = veri.get("mil", 0)
    money = veri.get("money", 0)

    # Embed içeriği
    desc = f"""
    **__Fraksiyon Bilgisi__**
    🎖️ **Adı**: {faction}
    🎭 **Rolü**: {role_mention}
    🏷️ **Büyüklük**: {veri['size']}

    **__Ekonomi__**
    **Bütçe**: {money:,} Kredi
    💰 **Ticaret Geliri**: {veri['trade']:,} Kredi
    🏦 **Vergi Geliri**: {veri['tax']:,} Kredi
    ⛏️ **Maden Geliri**: {veri['mining']:,} Kredi
    📦 **Kaynak Giderleri**: {veri['resource']:,} Kredi
    🫂 **Halk Yararına Giderler**: {veri['welfare']:,} Kredi
    🪖 **Askerî Bakım Gideri**: {military_cost:,} Kredi

    **__İstatistikler__**
    📊 **İstikrar**: %{veri['stability']}
    🛡️ **Savaş Desteği**: %{veri['warsup']}

    **__Askerî Güç__**
    🛠️ **Dretnotlar**: {dretnot}
    🛠️ **Savaş Kruvazörleri**: {bcruiser}
    🛠️ **Yıldız Destroyerleri**: {sdestroyer}
    🛠️ **Kruvazörler**: {cruiser:,}

    🚜 **Ağır Araçlar**: {heavy:,}
    🚛 **Orta Araçlar**: {medium:,}
    🚙 **Hafif Araçlar**: {light:,}

    🎯 **Özel Kuvvetler**: {special:,}
    🪖 **Ağır Piyadeler**: {hsoldier:,}
    👥 **Piyadeler**: {soldier:,} (x {soldier_cost:,} Kredi)
    """

    embed = await createEmbed(desc.strip(), titlee=f"**{faction} Fraksiyon Bilgileri**", color=discord.Colour.blurple())
    await interaction.response.send_message(embed=embed)

@Bot.tree.command(name="fraksiyon-stat-ayarla", description="Fraksiyonun statlarını değiştirir.", guild=discord.Object(id=1385373757572645097))
@app_commands.describe(
    faction="Fraksiyon adı", money="Para",
    trade="Ticari gelir", tax="Vergi gelirleri", mining="Maden gelirleri",
    resource="Kaynak giderleri", welfare="Halk yararına giderler",
    stability="İstikrar seviyesi", warsup="Savaş desteği", mil="Askerî giderler"
)
async def fraksiyonstatayarla(
    interaction: discord.Interaction,
    faction: str, money:int = None,
    trade: int = None, tax: int = None, mining: int = None,
    resource: int = None, welfare: int = None,
    stability: int = None, warsup: int = None, mil: int = None
):
    guncelleme = {}
    if trade is not None: guncelleme["trade"] = trade
    if tax is not None: guncelleme["tax"] = tax
    if mining is not None: guncelleme["mining"] = mining
    if resource is not None: guncelleme["resource"] = resource
    if welfare is not None: guncelleme["welfare"] = welfare
    if stability is not None: guncelleme["stability"] = stability
    if warsup is not None: guncelleme["warsup"] = warsup
    if mil is not None: guncelleme["mil"] = mil
    if trade is not None: guncelleme["money"] = money

    if not guncelleme:
        await interaction.response.send_message("⚠️ En az bir stat değeri girmelisin.", ephemeral=True)
        return
    result = factionColl.update_one({"faction": faction}, {"$set": guncelleme})
    if result.matched_count == 0:
        await interaction.response.send_message("❌ Böyle bir fraksiyon bulunamadı.", ephemeral=True)
        return
    desc = "\n".join([f"📌 `{key}` => **{value}**" for key, value in guncelleme.items()])
    embed = await createEmbed(desc, titlee=f"{faction} statları güncellendi", color=discord.Colour.green())
    await interaction.response.send_message(embed=embed)


@Bot.tree.command(name="fraksiyon-lider-ayarla", description="Fraksiyonun statlarını değiştirir.", guild=discord.Object(id=1385373757572645097))
@app_commands.describe(faction="Fraksiyon adı", user="Kullanıcı")
async def liderayarla(interaction:discord.Interaction, faction:str, user:discord.Member):
    factionColl.update_one({"faction":faction}, {"$set":{"ruler":user.id}})
    await interaction.response.send_message(f"**{faction} fraksiyonunun lideri, {user.mention}  olarak ayarlandı.**")




Bot.run("BOT_TOKEN")