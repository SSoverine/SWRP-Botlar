import discord
from pymongo import MongoClient
from discord import app_commands
from discord.ext import commands

#FONKSİYONLAR

async def createEmbed(desc, titlee, footer="", color=discord.Colour.dark_blue(), thumbnail="https://cdn.discordapp.com/attachments/1385373758268637196/1388540290188578896/genebot_logo.png?ex=68615a6b&is=686008eb&hm=c18ce222d1681b8c71afa4997ceedb479576efb085ac8eceaf0ee83a47711e47&", image="https://cdn.discordapp.com/attachments/1385373758268637196/1388270751278174400/image.png?ex=68605f63&is=685f0de3&hm=54bda5e7f6ce13bd0397272f464fb4c7efb56b627d9cc7237e34e87f153104c8&"):
    embed = discord.Embed(
        colour=color,
        description=desc,
        title=titlee
    )

    embed.set_footer(text=footer)
    embed.set_author(name="Parody™ Genel")

    embed.set_thumbnail(url=thumbnail)
    embed.set_image(url=image)
    return embed

mongo = MongoClient("mongodb://localhost:27017")

db = mongo.general
kayitColl = db.users
ecoColl = mongo.economy.users

Bot = commands.Bot(command_prefix="p!", intents=discord.Intents.all(), help_command=None)

auto_roles = []

#EVENTLER

@Bot.event
async def on_ready():
    global auto_roles

    await Bot.change_presence(status=discord.Status.do_not_disturb, activity=discord.Activity(type=discord.ActivityType.watching, name="Made by Soverine"))
    await Bot.tree.sync(guild=discord.Object(id=1385373757572645097))
    print("Bot hazır!")
    server = Bot.get_guild(1385373757572645097)
    auto_roles = [server.get_role(1385373757689958524), server.get_role(1385373757769650191), server.get_role(1385373757643690102), server.get_role(1389308667894960340), server.get_role(1385373757618651192), server.get_role(1385373757618651188)]


@Bot.event
async def on_member_join(member:discord.Member):
    embed = await createEmbed(f"{member.mention} Star Wars Parody™ Roleplay sunucusuna hoşgeldiniz!", "Bir Gemi Yaklaştı!", footer="Star Wars Parody™ Roleplay", thumbnail=None, image="https://cdn.discordapp.com/attachments/1385373758268637196/1388542027767087256/hiperuzay.gif?ex=68615c09&is=68600a89&hm=837b9ca8876b477153cfb69b4933d774a58bf107a3bebf274a08986cb581c6b9&")
    
    server = Bot.get_guild(1385373757572645097)
    channel = server.get_channel(1385373758268637202)    
    
    for role in auto_roles:
        await member.add_roles(role)
    
    await channel.send(embed=embed)

#KOMUTLAR

@Bot.tree.command(name="embed", description="Embed gönderir.", guild=discord.Object(id=1385373757572645097))
@app_commands.describe(desc="açıklama", title="başlık", footer="footer", thumbnail="Thumbnail urlsi", image="Fotoğraf urlsi")
async def embedgonder(interaction:discord.Interaction, desc:str, title:str, thumbnail:str, footer:str=None, image:str=None):
    if not interaction.user.guild_permissions.manage_roles:
        return
    embed = await createEmbed(desc=desc, titlee=title, footer=footer, thumbnail=thumbnail, image=image)
    await interaction.channel.send(embed=embed)

@Bot.tree.command(name="yasakla", description="Seçilen kullanıcıyı sunucudan yasaklar.", guild=discord.Object(id=1385373757572645097))
@app_commands.describe(user="Yasaklanacak kullanıcı", sebep="Banlanma sebebi (İsteğe bağlı)")
async def yasakla(interaction: discord.Interaction, user:discord.Member, sebep:str = "Sebep belirtilmedi."):
    if not interaction.user.guild_permissions.ban_members:
        await interaction.response.send_message("❌ Bu komutu kullanmak için `Üyeleri Yasakla` yetkisine sahip olmalısın.") 
    if user == interaction.user:
        await interaction.response.send_message("❌ Kendini yasaklayamazsın.", ephemeral=True)
        return
    if user.top_role >= interaction.user.top_role and interaction.user != interaction.guild.owner:
        await interaction.response.send_message("❌ Bu kullanıcıyı yasaklamak için rolün yeterli değil.", ephemeral=True)
        return
    
    await user.ban(reason=sebep)
    await interaction.response.send_message(f"✅ {user.mention} kullanıcısı yasaklandı.\n📄 Sebep: `{sebep}`")

@Bot.tree.command(name="yasaklama-kaldır", description="Seçilen kullanıcının yasaklanmasını kaldırır.", guild=discord.Object(id=1385373757572645097))
@app_commands.describe(id="Yasaklanması kaldırılacak kullanıcı (ID)")
async def yasakla(interaction: discord.Interaction, id:str):
    if not interaction.user.guild_permissions.ban_members:
        await interaction.response.send_message("❌ Bu komutu kullanmak için `Üyeleri Yasakla` yetkisine sahip olmalısın.")

    user = await Bot.fetch_user(int(id))

    await interaction.guild.unban(user)
    await interaction.response.send_message(f"✅ {user.mention} kullanıcısının yasağı kaldırıldı.")

@Bot.tree.command(name="stat-ayarla", description="Seçilen kullanıcının statlarını ayarlar.", guild=discord.Object(id=1385373757572645097))
@app_commands.describe(user="Kullanıcı",
                       uzay="Kullanıcının uzay savaşı komuta statı", 
                       kara="Kullanıcının kara savaşı komuta statı", 
                       hava="Kullanıcının hava savaşı komuta statı", 
                       pilotluk="Kullanıcının pilotluk statı", 
                       gizlilik="Kullanıcının gizlilik statı", 
                       dayaniklilik="Kullanıcının dayanıklık statı", 
                       nisan="Kullanıcının nişan alma statı", 
                       guc="Kullanıcının güce yatkınlık statı", 
                       muhendis="Kullanıcının mühendislik statı", 
                       hiz="Kullanıcının hız statı")
async def statayarla(interaction: discord.Interaction, user:discord.Member, uzay:discord.Role, kara:discord.Role, hava:discord.Role, pilotluk:discord.Role, gizlilik:discord.Role, dayaniklilik:discord.Role, nisan:discord.Role, guc:discord.Role, muhendis:discord.Role, hiz:discord.Role):
    if not interaction.user.guild_permissions.manage_roles:
        return
    await user.add_roles(uzay,kara,hava,pilotluk,gizlilik,dayaniklilik,nisan,guc,muhendis,hiz)
    embed = await createEmbed(f"{user.mention} kullanıcısının statları ayarlandı.", "Statlar Ayarlandı!", color=discord.Colour.green())
    await interaction.channel.send(embed = embed)

@Bot.tree.command(name="force-bilgi", description="Seçilen bir kullanıcının güç yetenekleri hakkında bilgi verir.", guild=discord.Object(id=1385373757572645097))
@app_commands.describe(user="Kullanıcı")
async def forcebilgi(interaction: discord.Interaction, user:discord.Member = None):
    if user == None:
        user = interaction.user
    desc = f"{user.mention} kullanıcısının güç yetenekleri:"
    
    forces = kayitColl.find_one({"user":user.id})["force"]
    for force in forces:
        desc += f"\n**{force}**"

    embed = await createEmbed(desc, "Güç Yetenekleri!", color=discord.Colour.green())
    await interaction.response.send_message(embed=embed)

@Bot.tree.command(name="force-reset", description="Seçilen kullanıcının kullanabildiği güç yeteneklerini resetler.", guild=discord.Object(id=1385373757572645097))
@app_commands.describe(user="Uygulanılacak kullanıcı")
async def forcereset(interaction: discord.Interaction, user:discord.Member):
    if not interaction.user.guild_permissions.manage_roles:
        return
    kayitColl.update_one({"user":user.id},{"$set":{"force":[]}})

@Bot.tree.command(name="force-ekle", description="Seçilen kullanıcının kullanabildiği güç yeteneklerini ayarlar. Her forcedan sonra , koyunuz.", guild=discord.Object(id=1385373757572645097))
@app_commands.describe(user="Uygulanılacak kullanıcı", forces="Güç yetenekleri")
async def forceayarla(interaction: discord.Interaction, user:discord.Member, forces:str):
    if not interaction.user.guild_permissions.manage_roles:
        return
     
    for force in forces.split(","):
        kayitColl.update_one({"user":user.id}, {"$push":{"force":force}})

    desc = f"{user.mention} kullanıcısının güç yetenekleri ayarlandı. İşte kullanıcının güç yetenekleri:"
    for force in forces.split(","):
        desc += f"\n**{force}**"

    embed = await createEmbed(desc, "Güç Yetenekleri Ayarlandı!", color=discord.Colour.green())
    await interaction.channel.send(embed=embed)

@Bot.tree.command(name="kayıt-sil", description="Seçilen kullanıcının kaydını silerek kayıtsıza atar.", guild=discord.Object(id=1385373757572645097))
@app_commands.describe(user="Kaydı silinecek kullanıcı.")
async def kayitsil(interaction: discord.Interaction, user:discord.Member):
    if not interaction.user.guild_permissions.manage_roles:
        return
    kayitColl.delete_one({"user":user.id})
    await interaction.channel.send(f"{user.mention} **kullanıcısının kaydı silindi.**")
    for role in user.roles:
        try:
            await user.remove_roles(role)
        except discord.NotFound:
            print(f"Rol bulunamadı veya silinmiş: {role}")
        except discord.Forbidden:
            print(f"Yetkim yok: {role}")
        except Exception as e:
            print(f"Diğer hata ({role}): {e}")
    i = 0
    for role in auto_roles:
        i+=1
        if role != None:
            await user.add_roles(role)
        else:
            print(i)

@Bot.tree.command(name="kayıt", description="Seçilen kullanıcıyı kayıt ederek rollerini verir.", guild=discord.Object(id=1385373757572645097))
@app_commands.describe(user="Kayıt edilen kullanıcı.", character="Karakter adı", hizip1="Kullanıcının bağlılığı.", hizip2="Kullanıcının başka bir bağlılığı varsa o rolü etiketleyiniz.(Zorunlu Değil)",
                       mevki1="Kullanıcının mevkisi", mevki2="Kullanıcının ikincil bir mevkisi varsa.(Örneğin, jedi ve general. Zorunlu değildir.)",
                        medeni="Evli/Bekar", irk="Irk", hikaye="fanon için")
async def kayit(interaction: discord.Interaction, user:discord.Member, character:str, hizip1:discord.Role, mevki1:discord.Role, medeni:discord.Role, irk:discord.Role, cinsiyet:discord.Role, mevki2:discord.Role=None, hizip2:discord.Role = None, hikaye:str=None):
    if not interaction.user.guild_permissions.manage_roles:
        return
    ecoColl.insert_one({"user_id":str(user.id), "salary":0,"inventory":[]})
    if hikaye==None:
        kayitColl.insert_one({"user":user.id,"character":character,"force":[]})
    else:
        kayitColl.insert_one({"user":user.id, "character":character,"force":[], "story":hikaye})

    embed = await createEmbed(f"{user.mention} kullanıcısı başarıyla kayıt edildi.", "Kayıt Yapıldı!", color=discord.Colour.green())
    await interaction.channel.send(embed=embed)

    await user.edit(nick=character)
    kayitli = interaction.guild.get_role(1385373757618651190)
    kayitsiz = interaction.guild.get_role(1385373757618651188)

    await user.add_roles(hizip1, mevki1, medeni, irk, cinsiyet, kayitli)
    if hizip2 != None:
        await user.add_roles(hizip2)

    if mevki2 != None:
        await user.add_roles(mevki2)

    await user.remove_roles(kayitsiz)

    await user.send("Kaydınz kabul edilmiştir. İyi eğlenceler!")


Bot.run("BOT_TOKEN")