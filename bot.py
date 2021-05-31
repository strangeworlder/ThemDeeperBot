# bot.py
import os
import random
import pymysql

from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

bot = commands.Bot(command_prefix='!')

def get_db():
    # database connector
    # TODO: Port to environmental variable
    db=pymysql.connect(host=os.getenv('MYSQL_HOST'), port=3306, user=os.getenv('MYSQL_USER'), passwd=os.getenv('MYSQL_PASSWORD'), db=os.getenv('MYSQL_DATABASE'))

    return db


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
    stat_value = int(myresult[0])
    if stat_value < 7 and stat_value >= 0:
        return ['d20', 'd']
    elif stat_value < 11:
        return ['d20']
    elif stat_value < 15:
        return ['d20', '+', 'd4']
    elif stat_value < 18:
        return ['d20', '+', 'd6']
    elif stat_value < 19:
        return ['d20', '+', 'd8']
    else:
        return ['d20']

def roll(user, db_this_author, *commands):
    # Returns the result of the roll
    # TODO: Return an array of values, handle the printing outside this function
    str1 = ''
    adv = False
    disadv = False
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
    roll = ''
    joiner = ''
    rollstring = ''
    total = 0
    for die in dice:
        if die[0] == 'd':
            die = '1' + die
        [number_of_dice, number_of_sides] = die.split('d')
        if total == 0 and adv:
            number_of_dice = str(int(number_of_dice)+1)
            roll = f'{number_of_dice}d{number_of_sides}(adv)'
        elif total == 0 and disadv:
            number_of_dice = str(int(number_of_dice)+1)
            roll = f'{number_of_dice}d{number_of_sides}(dis)'
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
    return '*' + user + '* roll: ' + rollstring + '\n— Total: **' + str(total) + '** —'

def check_stats(db_this_author):
    # a check to see if the author has initialized stats in db
    db = get_db()
    cur = db.cursor()
    cur.execute(f"SELECT * FROM characters WHERE {db_this_author}")
    myresult = cur.fetchone()

    if myresult is None or len(myresult) < 1:
        return False
    else:
        return True

def update_stat(stat, args_array, db_this_author):
    # Update a single stat of the author in db.
    # + adds, - subtracts, = sets value
    # TODO: Max and min values
    db = get_db()
    cur = db.cursor()
    args_array.remove(stat)
    args_string = "".join(args_array).replace(' ', '')
    cur.execute(f"SELECT {stat} FROM characters WHERE {db_this_author}")
    stats = cur.fetchone()
    if args_string[0] == '+':
        args_array = list(args_string)
        args_array.remove('+')
        args_string = int("".join(args_array))
        if int(stats[0]) + args_string > 18:
            args_string = 18 - int(stats[0])
        cur.execute(f"UPDATE characters SET {stat} = {stat} + {args_string} WHERE {db_this_author}")
    elif args_string[0] == '-':
        args_array = list(args_string)
        args_array.remove('-')
        args_string = int("".join(args_array))
        if int(stats[0]) - args_string < 0:
            args_string = int(stats[0])
        cur.execute(f"UPDATE characters SET {stat} = {stat} - {args_string} WHERE {db_this_author}")
    elif args_string[0] == '=' or int(args_string[0]) > 0:
        args_array = list(args_string)
        if args_array[0] == '=':
            args_array.remove('=')
        args_string = int("".join(args_array))
        if args_string < 0:
            args_string = 0
        if args_string > 18:
            args_string = 18
        cur.execute(f"UPDATE characters SET {stat} = {args_string} WHERE {db_this_author}")
    db.commit()

def get_db_this_author(ctx):
    # returns the part of the query that defines the current query maker (server/author)
    # TODO: make sure no bad stuff gets to query string (should be ok, but...)
    return f"server = {ctx.message.guild.id} AND player = {ctx.message.author.id}"

@bot.command(name='r', help='Simulates rolling dice.')
async def r(ctx, *args):
    # TODO: Handle response messages from roll here
    db_this_author = get_db_this_author(ctx)

    await ctx.send(roll(ctx.message.author.name, db_this_author, args))

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
            cur.execute(f"INSERT INTO characters (server, player, phy, ref, sta, kno, ins, pow) VALUES ({ctx.message.guild.id}, {ctx.message.author.id}, 10, 10, 10, 10, 10, 10)")            
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

    cur.execute(f"SELECT * FROM characters WHERE {db_this_author}")
    stats = cur.fetchone()

    await ctx.send(f'*{ctx.message.author.name}* stats:\nPhy: **' + str(stats[3]) + '**, Ref: **' + str(stats[4]) + '**, Sta: **' + str(stats[5]) + '**, Kno: **' + str(stats[6]) + '**, Ins: **' + str(stats[7]) + '**, Pow: **' + str(stats[8]) + '**, ')

bot.run(TOKEN)
