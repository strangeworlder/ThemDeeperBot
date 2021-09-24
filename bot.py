# bot.py
import os
import random
import pymysql
import discord

from discord.ext import commands
from dotenv import load_dotenv
from discord_slash import SlashCommand, SlashContext

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())

def get_db():
    # database connector
    # TODO: Port port to environmental variable
    db=pymysql.connect(host=os.getenv('MYSQL_HOST'), port=3306, user=os.getenv('MYSQL_USER'), passwd=os.getenv('MYSQL_PASSWORD'), db=os.getenv('MYSQL_DATABASE'))

    return db

def is_integer(n):
    # variation of integer that also checks if a string is an integer string
    try:
        float(n)
    except ValueError:
        return False
    else:
        return float(n).is_integer()

def get_stat_roll(db_this_author, stat):
    # returns the roll array for the user's particular stat if between 0 and 18
    # or a straight d20 roll array if user not in database or value out of range
    db = get_db()
    cur = db.cursor()
    if not check_stats(db_this_author):
        return ['d20']

    if stat == 'phy':
        cur.execute(f"SELECT phy FROM characters WHERE {db_this_author}")
    elif stat == 'ref':
        cur.execute(f"SELECT ref FROM characters WHERE {db_this_author}")
    elif stat == 'sta':
        cur.execute(f"SELECT sta FROM characters WHERE {db_this_author}")
    elif stat == 'kno':
        cur.execute(f"SELECT kno FROM characters WHERE {db_this_author}")
    elif stat == 'ins':
        cur.execute(f"SELECT ins FROM characters WHERE {db_this_author}")
    elif stat == 'pow':
        cur.execute(f"SELECT pow FROM characters WHERE {db_this_author}")
    else:   
        return ['d20']
    myresult = cur.fetchone()
    db.close()

    stat_value = int(myresult[0])
    if stat_value < 10 and stat_value >= 0:
        return ['d20']
    elif stat_value < 15:
        return ['d20', '+', 'd4']
    elif stat_value < 18:
        return ['d20', '+', 'd6']
    elif stat_value < 19:
        return ['d20', '+', 'd8']
    else:
        return ['d20']

def roll(db_this_author, *commands):
    # Returns the result of the roll
    # TODO: multiples and static adds
    str1 = ''
    adv = False
    disadv = False
    roll = ''
    joiner = ''
    rollstring = ''
    total = 0

    cmds = list(commands[0])
    cmds = [get_stat_roll(db_this_author, 'pow') if x=='pow' else get_stat_roll(db_this_author, 'ins') if x=='ins' else get_stat_roll(db_this_author, 'kno') if x=='kno' else get_stat_roll(db_this_author, 'sta') if x=='sta' else get_stat_roll(db_this_author, 'ref') if x=='ref' else get_stat_roll(db_this_author, 'phy') if x=='phy' else [x] for x in cmds]

    flat_list = []
    for sublist in cmds:
        for item in sublist:
            flat_list.append(item)
    cmds = flat_list

    if 'a' in cmds:
        adv = True
        cmds.remove('a')
    if 'adv' in cmds:
        adv = True
        cmds.remove('adv')
    if 'advantage' in cmds:
        adv = True
        cmds.remove('advantage')
    if 'd' in cmds:
        disadv = True
        cmds.remove('d')
    if 'dis' in cmds:
        disadv = True
        cmds.remove('dis')
    if 'disadvantage' in cmds:
        disadv = True
        cmds.remove('disadvantage')
    if disadv == True and adv == True:
        disadv = False
        adv = False

    parse_string = str1.join(cmds)
    dice = parse_string.split('+')

    for die in dice:
        if die[0] == 'd':
            die = '1' + die
        [number_of_dice, number_of_sides] = die.split('d')
        if total == 0 and adv:
            number_of_dice = str(int(number_of_dice)+1)
            roll = f'{number_of_dice}d{number_of_sides}:small_red_triangle:'
        elif total == 0 and disadv:
            number_of_dice = str(int(number_of_dice)+1)
            roll = f'{number_of_dice}d{number_of_sides}:small_red_triangle_down:'
        else:
            roll = f'{joiner}{number_of_dice}d{number_of_sides}'
        joiner = ' + '
        if number_of_sides == '66':
            result = [
                10 * random.choice(range(1, int(6) + 1)) + random.choice(range(1, int(6) + 1))
                for _ in range(int(number_of_dice))
            ]
        else:
            result = [
                random.choice(range(1, int(number_of_sides) + 1))
                for _ in range(int(number_of_dice))
            ]
        if adv:
            total = total + sum(result) - min(result)
        elif disadv:
            total = total + sum(result) - max(result)
        else:
            total = total + sum(result)
        resultstring = ''
        resultjoiner = ''
        for results in result:
            if adv:
                if results == min(result):
                    resultstring = resultstring + resultjoiner + str(results)
                    adv = False
                else:
                    resultstring = resultstring + resultjoiner + '**' + str(results) +'**'
            elif disadv:
                if results == max(result):
                    resultstring = resultstring + resultjoiner + str(results)
                    disadv = False
                else:
                    resultstring = resultstring + resultjoiner + '**' + str(results) +'**'
            else:
                resultstring = resultstring + resultjoiner + '**' + str(results) +'**'
            resultjoiner = ', '
        resultstring = resultstring + ''
        rollstring = rollstring + ' ' + roll + ' [' + resultstring + ']'
    return [rollstring, total]

def check_stats(db_this_author):
    # a check to see if the author has initialized stats in db
    db = get_db()
    cur = db.cursor()
    cur.execute(f"SELECT * FROM characters WHERE {db_this_author}")
    myresult = cur.fetchone()
    db.close()

    if myresult is None or len(myresult) < 1:
        return False
    else:
        return True

def update_stat(stat, args_array, db_this_author):
    # Update a single stat of the author in db.
    # + adds, - subtracts, = sets value
    db = get_db()
    cur = db.cursor()
    args_array.remove(stat)
    args_string = "".join(args_array).replace(' ', '')
    cur.execute(f"SELECT {stat} FROM characters WHERE {db_this_author}")
    stats = cur.fetchone()

    if args_string[0] == '+':
        args_array = list(args_string)
        args_array.remove('+')
        args_string = "".join(args_array)
        if is_integer(args_string):
            args_string = int(args_string)
            if int(stats[0]) + args_string > 18:
                args_string = 18 - int(stats[0])
            cur.execute(f"UPDATE characters SET {stat} = {stat} + {args_string} WHERE {db_this_author}")
            db.commit()

    elif args_string[0] == '-':
        args_array = list(args_string)
        args_array.remove('-')
        args_string = "".join(args_array)
        if is_integer(args_string):
            args_string = int(args_string)
            if int(stats[0]) - args_string < 0:
                args_string = int(stats[0])
            cur.execute(f"UPDATE characters SET {stat} = {stat} - {args_string} WHERE {db_this_author}")
            db.commit()

    elif args_string[0] == '=' or is_integer(args_string):
        args_array = list(args_string)
        if args_array[0] == '=':
            args_array.remove('=')
        args_string = "".join(args_array)
        if is_integer(args_string):
            args_string = int(args_string)
            if args_string < 0:
                args_string = 0
            if args_string > 18:
                args_string = 18
            cur.execute(f"UPDATE characters SET {stat} = {args_string} WHERE {db_this_author}")
            db.commit()
    db.close()


def get_db_this_author(ctx):
    # returns the part of the query that defines the current query maker (server/author)
    # TODO: make sure no bad stuff gets to query string (should be ok, but...)
    return f"server = {ctx.message.guild.id} AND player = {ctx.message.author.id}"
def get_slash_db_this_author(ctx):
    # returns the part of the query that defines the current query maker (server/author)
    # TODO: make sure no bad stuff gets to query string (should be ok, but...)
    return f"server = {ctx.guild_id} AND player = {ctx.author_id}"

@bot.command(name='r', help='Simulates rolling dice.')
async def r(ctx, *args):
    # TODO: Handle response messages from roll here
    db_this_author = get_db_this_author(ctx)
    roll_result = roll(db_this_author, args)
    namestring = ctx.message.author.name
    if ctx.message.author.nick is not None:
        namestring = ctx.message.author.nick
    string = ':game_die: **' + namestring + '** roll:\n' + roll_result[0] + '\n— Total: **' + str(roll_result[1]) + '** —'
    await ctx.send(string)

@bot.command(name='stat', help='View and adjust your stats.')
async def stat(ctx, *args):
    # stat handler — view (no args), initialize in databse ('init') or change (stat name) stats
    db = get_db()
    cur = db.cursor()

    db_this_author = get_db_this_author(ctx)

    if len(args) == 1:
        if args[0] == 'init':
            cur.execute(f"DELETE FROM characters WHERE {db_this_author}")
            db.commit()
            vals = [roll(db_this_author, ['3d6'])[1], roll(db_this_author, ['3d6'])[1], roll(db_this_author, ['3d6'])[1], roll(db_this_author, ['3d6'])[1], roll(db_this_author, ['3d6'])[1], roll(db_this_author, ['3d6'])[1]]
            cur.execute(f"INSERT INTO characters (server, player, phy, ref, sta, kno, ins, pow) VALUES ({ctx.message.guild.id}, {ctx.message.author.id}, {int(vals[0])}, {int(vals[1])}, {int(vals[2])}, {int(vals[3])}, {int(vals[4])}, {int(vals[5])})")            
            db.commit()
        if args[0] == 'uninit':
            cur.execute(f"DELETE FROM characters WHERE {db_this_author}")
            await ctx.send('Stats removed from db')
            db.commit()
            return


    if not check_stats(db_this_author):
        await ctx.send('Stats not yet initialized, please use `!stat init` to do so')
        return

    if len(args) > 1:
        args_array = list(args);
        if args_array[0] == 'phy':
            update_stat('phy', args_array, db_this_author)
        elif args_array[0] == 'ref':
            update_stat('ref', args_array, db_this_author)
        elif args_array[0] == 'sta':
            update_stat('sta', args_array, db_this_author)
        elif args_array[0] == 'kno':
            update_stat('kno', args_array, db_this_author)
        elif args_array[0] == 'ins':
            update_stat('ins', args_array, db_this_author)
        elif args_array[0] == 'pow':
            update_stat('pow', args_array, db_this_author)
        else:
            return

    cur.execute(f"SELECT * FROM characters WHERE {db_this_author}")
    stats = cur.fetchone()
    db.close()
    namestring = ctx.message.author.name
    if ctx.message.author.nick is not None:
        namestring = ctx.message.author.nick
    await ctx.send(f':memo: **{namestring}** stats:\nPhy: **' + str(stats[3]) + '**, Ref: **' + str(stats[4]) + '**, Sta: **' + str(stats[5]) + '**, Kno: **' + str(stats[6]) + '**, Ins: **' + str(stats[7]) + '**, Pow: **' + str(stats[8]) + '**, ')

slash = SlashCommand(bot, sync_commands=True)
guilds = os.getenv('GUILD_IDS').split(',')
for i in range(0, len(guilds)):
    guilds[i] = int(guilds[i])

@slash.slash(name="r", guild_ids=guilds)
async def _r(ctx: SlashContext, dice):
    db_this_author = get_slash_db_this_author(ctx)
    roll_result = roll(db_this_author, dice.split())
    namestring = ctx.author.name
    if ctx.author.nick is not None:
        namestring = ctx.author.nick
    string = ':game_die: **' + namestring + '** roll:\n' + roll_result[0] + '\n— Total: **' + str(roll_result[1]) + '** —'
    await ctx.send(string)

@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="!r and !stat"))
    print("Bot is ready!")

bot.run(TOKEN)
