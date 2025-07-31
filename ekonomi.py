import discord
import asyncio
from datetime import datetime, time, timedelta
from pymongo import MongoClient
from discord import app_commands
from discord.ext import commands

Bot = commands.Bot(command_prefix="p!", intents=discord.Intents.all(), help_command=None)

storeEmbeds = []

#FONKSİYONLAR

async def createEmbed(desc, titlee, footer="", color=discord.Colour.dark_blue(), image="https://cdn.discordapp.com/attachments/1385373758268637196/1388270751278174400/image.png?ex=68605f63&is=685f0de3&hm=54bda5e7f6ce13bd0397272f464fb4c7efb56b627d9cc7237e34e87f153104c8&"):
    embed = discord.Embed(
        colour=color,
        description=desc,
        title=titlee
    )

    embed.set_footer(text=footer)
    embed.set_author(name="Parody™ Ekonomi Botu")

    embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1385373758268637196/1388267238477271201/ekonomiembedlogo.png?ex=68605c1e&is=685f0a9e&hm=c2dfcbb1fbc16c6be6cb90e38d21250a23f712d0d3d81cd56614b78d7843f9ff&")
    embed.set_image(url=image)
    return embed

#DATABASE

mongo = MongoClient("mongodb://localhost:27017")

ecodb = mongo.economy

storeColl = ecodb.store
roleColl = ecodb.roles
userColl = ecodb.users

for item in storeColl.find({}):
    embed = asyncio.run(createEmbed(f"**Eşya: **{item["name"]}\n**Fiyat: **{item["price"]}<:kredi:1388274331741851830>\n**Açıklama: **{item["description"]}", "**Mağaza**"))
    storeEmbeds.append(embed)

#EVENTLER

async def maasdagit():
    guild = Bot.get_guild(1385373757572645097)
    roles = roleColl.find({})

    if guild is None:
        print("Guild bulunamadı!")
        return

    if roles is None:
        print("roller bulunamadı")
        return
    
    for rol in roles:
        role = guild.get_role(int(rol["role_id"]))

        if role == None:
            print("Rol bulunamadı\n" + rol["role_id"])
            return

        for member in role.members:
            userColl.update_one({"user_id":str(member.id)}, {"$inc":{"salary":rol["salary"]}}, upsert=True)

async def maas_zamanlayici():
    await Bot.wait_until_ready()
    while not Bot.is_closed():
        now = datetime.now()

        hedef_zaman = datetime.combine(now.date(), time.min)
        if now >= hedef_zaman:
            hedef_zaman += timedelta(days=1)
        bekleme_suresi = (hedef_zaman - now).total_seconds()

        print(f"{bekleme_suresi} saniye sonra maaş dağıtılacak.")
        await asyncio.sleep(bekleme_suresi)

        await maasdagit()

@Bot.event
async def on_ready():
    Bot.loop.create_task(maas_zamanlayici())
    await Bot.change_presence(status=discord.Status.do_not_disturb, activity=discord.Activity(type=discord.ActivityType.watching, name="Made by Soverine"))
    await Bot.tree.sync(guild=discord.Object(id=1385373757572645097))
    print("Bot hazır!")

#KOMUTLAR

#VIEW OBJELERİ

class StoreView(discord.ui.View):
    index = 0

    def __init__(self):
        super().__init__()

    @discord.ui.button(label="Geri", style=discord.ButtonStyle.primary)
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        
        self.index -= 1
        if self.index<0:
            self.index = len(storeEmbeds)-1

        await interaction.edit_original_response(embed=storeEmbeds[self.index], view=self)

    @discord.ui.button(label="İleri", style=discord.ButtonStyle.primary)
    async def forward_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        
        self.index += 1
        if self.index == len(storeEmbeds):
            self.index = 0

        await interaction.edit_original_response(embed=storeEmbeds[self.index], view=self)

#YETKİLİ KOMUTLARI

@Bot.tree.command(name="maaş-ekle", description="Seçilen rol için günlük maaş ekler.", guild=discord.Object(id=1385373757572645097))
@app_commands.describe(rol="Maaş eklenecel rol", maas="Günlük maaş miktarı")
async def maasekle(interaction: discord.Interaction, rol: discord.Role, maas:int):
    if not interaction.user.guild_permissions.manage_roles:
        return
    
    if roleColl.find_one({"role_id":str(rol.id)}) == None:
        roleColl.insert_one({"role_id":str(rol.id), "salary":maas})
    else:
        roleColl.update_one({"role_id":str(rol.id)}, {"$set":{"salary":maas}}, upsert=True)

    await interaction.response.send_message(f"{rol.name} rolüne günlük **{maas}** <:kredi:1388274331741851830> maaş tanımlandı.")

@Bot.tree.command(name="para-ekle", description="Seçilen kullanıcıya para ekler.", guild=discord.Object(id=1385373757572645097))
@app_commands.describe(user="Para eklenecek kullanıcı", amount="Eklenecek para miktarı")
async def paraekle(interaction: discord.Interaction, user:discord.User, amount:int):
    if not interaction.user.guild_permissions.manage_roles:
        return
    
    if user == None:
        return
    
    if userColl.find_one({"user_id":str(user.id)}) == None:
        userColl.insert_one({"user_id":str(user.id), "salary":amount,"inventory":[]})
    else:
        kullanici = userColl.find_one({"user_id":str(user.id)})
        userColl.update_one({"user_id":str(user.id)}, {"$set":{"salary":kullanici["salary"]+amount}}, upsert=True)

    embed = await createEmbed(f"{user.display_name} kullanıcısına **{amount}**<:kredi:1388274331741851830> eklendi.", "**Kredi Eklendi!**")

    await interaction.response.send_message(embed=embed)

@Bot.tree.command(name="para-sil", description="Seçilen kullanıcıdan para siler.", guild=discord.Object(id=1385373757572645097))
@app_commands.describe(user="Parası silinecek kullanıcı", amount="Silinecek paranın miktarı")
async def parasil(interaction: discord.Interaction, user:discord.User, amount:int):
    if not interaction.user.guild_permissions.manage_roles:
        return
    
    userColl.update_one({"user_id":str(user.id)}, {"$inc":{"salary":-amount}})

    embed = await createEmbed(f"{user.display_name} kullanıcısından {amount}<:kredi:1388274331741851830> eksiltildi.", "**Para Silindi!**", color=discord.Colour.yellow())
    await interaction.response.send_message(embed=embed)

@Bot.tree.command(name="eşya-ekle", description="Mağazaya eşya ekler.", guild=discord.Object(id=1385373757572645097))
@app_commands.describe(name="Eşyanın adı", price="Eşyanın fiyatı", description="Eşyanın açıklaması")
async def esyaekle(interaction: discord.Interaction, name:str, price:int, description:str = ""):
    if not interaction.user.guild_permissions.manage_roles:
        return
    
    head = "**Eşya Eklendi!**"

    if storeColl.find_one({"name":name}) == None:
        storeColl.insert_one({"name":name, "price":price, "description":description})
    else:
        if description == "":
            description = storeColl.find_one({"name":name})["description"]
        storeColl.update_one({"name":name}, {"$set":{"price":price},"$set":{"description":description}}, upsert=True)
        head = "**Eşya Güncellendi!**"

    embed = await createEmbed(f"**İsim: **{name}\n\n**Fiyat: **{price}\n\n**Açıklama: **{description}", head)
    storeEmbed = await createEmbed(f"**Eşya: **{name}\n**Fiyat: ** {price}<:kredi:1388274331741851830>\n**Açıklama: **{description}", "**Mağaza**")
    storeEmbeds.append(storeEmbed)
    await interaction.response.send_message(embed=embed)

#ÜYE KOMUTLARI

@Bot.tree.command(name="bakiye", description="Bir kullanıcının bakiyesini gösterir.", guild=discord.Object(id=1385373757572645097))
@app_commands.describe(user="Bakiyesi gösterilecek kullanıcı")
async def bakiye(interaction: discord.Interaction, user:discord.User = None):
    if user == None:
        user = interaction.user

    balance = ""

    if userColl.find_one({"user_id":str(user.id)}) == None:
        return
    else:
        balance = str(userColl.find_one({"user_id":str(user.id)})["salary"])

    embed = await createEmbed(f"{user.mention} kullanıcısının bakiyesi **" + balance + "**<:kredi:1388274331741851830>", f"**{user.display_name} Bakiye**")
    await interaction.response.send_message(embed=embed)

async def paraver():
    pass

@Bot.tree.command(name="mağaza", description="Satıştaki eşyaları gösterir.", guild=discord.Object(id=1385373757572645097))
@app_commands.describe()
async def magaza(interaction: discord.Interaction):
    await interaction.response.send_message(embed=storeEmbeds[0], view=StoreView())

@Bot.tree.command(name="satın-al", description="Marketten eşya satın almanızı sağlar.", guild=discord.Object(id=1385373757572645097))
@app_commands.describe(name="Satın alınacak eşyanın adı")
async def satinal(interaction: discord.Interaction, name: str):
    embed = None
    for item in storeColl.find({}):
        if item["name"].lower() == name.lower():
            user = userColl.find_one({"user_id":str(interaction.user.id)})
            balance = user["salary"]
            if balance<item["price"]:
                embed = await createEmbed(f"{item["name"]} eşyasının fiyatı {str(item["price"])}<:kredi:1388274331741851830>, sizin güncel bakiyeniz ise {str(balance)}<:kredi:1388274331741851830>. Bu eşyayı alabilmeniz için {str(item["price"]-balance)}<:kredi:1388274331741851830>  ihtiyacınız var.", "**Yetersiz Bakiye!**")
            else:
                userColl.update_one({"user_id":user["user_id"]}, {"$set":{"salary":balance-item["price"]}, "$push":{"inventory":item["name"]}})
                embed = await createEmbed(f"{item["name"]} eşyasını satın aldını! Güncel bakiyeniz {str(balance-item["price"])}<:kredi:1388274331741851830>. ", "**Eşya Satın Alındı!**", color = discord.Colour.green())
            break
        else:
            embed = await createEmbed(f"{name} adında bir eşya bulamadım. Lütfen eşya adını doğru girdiğinden emin ol. /mağaza komutuyla eşya isimlerini görüntüleyebilirsin.", "**Eşya Bulunamadı!**", color = discord.Colour.red())
    await interaction.response.send_message(embed=embed)

@Bot.tree.command(name="envanter", description="Envanterinizi gösterir.", guild=discord.Object(id=1385373757572645097))
@app_commands.describe()
async def envanter(interaction: discord.Interaction):
    user = userColl.find_one({"user_id": str(interaction.user.id)})
    desc = ""

    if user is None:
        desc += "Envanterinizde herhangi bir eşya bulunamadı."
    else:
        inventory = user.get("inventory", [])

    if len(inventory) == 0:
        desc += "Envanterinizde herhangi bir eşya bulunamadı."
    else:
        i = 0
        for item in inventory:
            i+=1
            desc += f"{i}. {item}\n"

    embed = await createEmbed(desc, "**Envanter**")
    await interaction.response.send_message(embed = embed)

Bot.run("BOT_TOKEN")