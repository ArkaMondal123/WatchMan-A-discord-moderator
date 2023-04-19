import os
import discord
import pymongo

client = pymongo.MongoClient(f"mongodb+srv://Martianbot:{password}@clustermartianbot.erq2f.mongodb.net/MartianBot?retryWrites=true&w=majority")
db = client['ModBot']
collection = db["UserData"]
col_bz_wrds = db["BuzzWords"]
col_channel = db["channel data"]

class sidefuncs:
    def lwr_case(input_li : list):
        return [string.lower() for string in input_li]
    def retrieve_bz_wrds():
        return eval(col_bz_wrds.find_one()["li"])
    def delete_bz_wrds(del_li):
        li = eval(col_bz_wrds.find_one()["li"])
        for i in sidefuncs.lwr_case(del_li):
            li.remove(i)
        col_bz_wrds.delete_one({'_id' : 'buzz'})
        col_bz_wrds.insert_one({'_id' : 'buzz', 'li' : str(li)})
    def check_for_bz(msg_list):
        for i in msg_list:
            if i in eval(col_bz_wrds.find_one()["li"]):
                return [True, set(eval(col_bz_wrds.find_one()["li"])) - set(msg_list)]
            else:
                continue
        return [False]
    def add_offense(msgid, message : discord.Message):
        try:
            li = collection.find({ "_id": message.author.id})[0]["offenses"] + [[message.id, f"https://discord.com/channels/{message.guild.id}/{message.channel.id}/{message.id}", message.content, msgid]]
            collection.update_one({ "_id": message.author.id}, {"$set" : {"offenses" : li}})
        except Exception:
            collection.insert_one({"_id" : message.author.id, "offenses" : [[message.id, f"https://discord.com/channels/{message.guild.id}/{message.channel.id}/{message.id}", message.content, msgid]]})

    def remove_offense(msgid, userid):
        li = collection.find({"_id" : int(userid)})[0]["offenses"]
        for i in li:
            if msgid in i:
                li.remove(i)
                if len(li) != 0:
                    collection.update_one({ "_id": int(userid)}, {"$set" : {"offenses" : li}})
                else:
                    collection.delete_one({"_id" : int(userid)})
                return True
            else:
                continue
        return False
    def retrieve_list():
        return collection.find({}, {"_id" : 1, "offenses" : 1})


class MyClient(discord.Client):
    async def on_ready(self):
        print('Logged in as {0}!'.format(self.user))

    async def on_message(self, message):
        if message.author == self.user:
            return
        elif message.content in [".reqlist", ".dismiss", ".buzzwords"] and message.channel.id == col_channel.find_one()["channelid"]:
            if message.content == ".reqlist":
                data_retrieved = list(sidefuncs.retrieve_list())
                embed = discord.Embed(title = "Top Offenders", color = message.author.color)
                def sorter(x):
                    return len(x["offenses"])
                data_retrieved = sorted(data_retrieved, key = sorter, reverse=True)
                for i in data_retrieved:
                    send_list = ""
                    for x in i["offenses"]:
                        send_list = send_list + "Message: " + x[2] + "\n" + "    Link: (" + x[1] + ")" + "\n \n"
                    user = await self.fetch_user(i["_id"])
                    embed.add_field(name = user , value = send_list, inline = False)
                embed.set_thumbnail(url = 'https://cdn.discordapp.com/attachments/948166853405073411/970730144786419772/dcbot.jpg')
                await message.channel.send(embed = embed)

            if message.content == ".buzzwords":
                li = eval(col_bz_wrds.find_one()["li"])
                str_to_send = ""
                for i in li:
                    str_to_send = str_to_send + i + "\n"
                embed = discord.Embed(color = message.author.color)
                embed.add_field(name = "Buzzwords:", value = str_to_send)
                embed.set_thumbnail(url = 'https://cdn.discordapp.com/attachments/948166853405073411/970730144786419772/dcbot.jpg')
                await message.channel.send(embed = embed)
            if message.content == ".dismiss":
                try:
                    message_rep = await message.channel.fetch_message(message.reference.message_id)
                except:
                    await message.channel.send("```error: no message replied to```")
                    return

                embed = message_rep.embeds[0]
                x = sidefuncs.remove_offense(message_rep.id, embed.to_dict()["fields"][0]["value"].split(" ")[-1][1:-1])
                if x:
                    await message_rep.channel.send("```dismissed```")
                else:
                    await message_rep.channel.send("```an error occured```")

        elif message.content.startswith(".deletebuzzwords") and message.channel.id == col_channel.find_one()["channelid"]:
            sidefuncs.delete_bz_wrds(sidefuncs.lwr_case(message.content.split(" ")[1:]))
            await message.channel.send("```Deleted```")

        elif message.content == ".setchannel":
            try:
                col_channel.insert_one({"_id" : message.guild.id, "channelid" : message.channel.id})
            except:
                col_channel.update_one({"_id" : message.guild.id}, {"$set" : {"channelid" : message.channel.id}})
            await message.channel.send(f"WatchMan Channel set as <#{message.channel.id}>")

        elif message.content.startswith(".buzzword") and message.channel.id == col_channel.find_one()["channelid"]:
            li = eval(col_bz_wrds.find_one()["li"]) + sidefuncs.lwr_case(message.content.split(" ")[1:])
            col_bz_wrds.delete_one({'_id' : 'buzz'})
            col_bz_wrds.insert_one({'_id' : 'buzz', 'li' : str(li)})
            await message.channel.send(f"BuzzWords appended")
        else:
            if sidefuncs.check_for_bz(sidefuncs.lwr_case(message.content.split(" ")))[0]:
                try:
                    channel = await self.fetch_channel(col_channel.find_one()["channelid"])
                    embed = discord.Embed(title = "Buzz", color = message.author.color)
                    embed.add_field(name = "Author", value = f"{message.author} ({message.author.id})", inline = True)
                    embed.add_field(name = "Message:", value = message.content, inline = False)
                    embed.add_field(name = "Message Link:", value = f"https://discord.com/channels/{message.guild.id}/{message.channel.id}/{message.id}", inline = False)
                    embed.set_footer(text = "To dismiss, reply to this message with '.dismiss'")
                    embed.set_thumbnail(url = 'https://cdn.discordapp.com/attachments/948166853405073411/970730144786419772/dcbot.jpg')
                    msg = await channel.send(embed = embed)
                except:
                    pass
                sidefuncs.add_offense(msg.id, message)

client = MyClient()
client.run(os.environ['TOKEN'])
