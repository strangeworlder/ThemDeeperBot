# bot.py
import os
import random
import numpy as np

import pymysql

from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

bot = commands.Bot(command_prefix='!')

def get_db():
    db=pymysql.connect(host=os.getenv('MYSQL_HOST'), port=3306, user=os.getenv('MYSQL_USER'), passwd=os.getenv('MYSQL_PASSWORD'), db=os.getenv('MYSQL_DATABASE'))

    return db


def get_stat(userstring, stat):
    db = get_db()
    cur = db.cursor()
    if not check_stats(userstring):
        return ['d20']

    if stat == 'phy':
        cur.execute(f"SELECT phy FROM characters {userstring}")
    elif stat == 'ref':
        cur.execute(f"SELECT ref FROM characters {userstring}")
    elif stat == 'sta':
        cur.execute(f"SELECT sta FROM characters {userstring}")
    elif stat == 'kno':
        cur.execute(f"SELECT kno FROM characters {userstring}")
    elif stat == 'ins':
        cur.execute(f"SELECT ins FROM characters {userstring}")
    elif stat == 'pow':
        cur.execute(f"SELECT pow FROM characters {userstring}")
    else:   
        return ['d20']
    myresult = cur.fetchone()
    pow = int(myresult[0])
    if pow < 7:
        return ['d20', 'd']
    elif pow < 11:
        return ['d20']
    elif pow < 15:
        return ['d20', '+', 'd4']
    elif pow < 18:
        return ['d20', '+', 'd6']
    elif pow < 19:
        return ['d20', '+', 'd8']
    else:
        return ['d20']

def roll(user, userstring, *commands):
    str1 = ''
    adv = False
    disadv = False
    cmds = list(commands[0])
    cmds = [get_stat(userstring, 'pow') if x=='pow' else get_stat(userstring, 'ins') if x=='ins' else get_stat(userstring, 'kno') if x=='kno' else get_stat(userstring, 'sta') if x=='sta' else get_stat(userstring, 'ref') if x=='ref' else get_stat(userstring, 'phy') if x=='phy' else [x] for x in cmds]
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
    return '*' + user + '*: ' + rollstring + '\n— Total: **' + str(total) + '** —'

def check_stats(userstring):
    db = get_db()
    cur = db.cursor()
    cur.execute(f"SELECT * FROM characters {userstring}")
    myresult = cur.fetchone()

    if myresult is None or len(myresult) < 1:
        return False
    else:
        return True


@bot.command(name='r', help='Simulates rolling dice.')
async def r(ctx, *args):
    userstring = f"WHERE server = {ctx.message.guild.id} AND player = {ctx.message.author.id}"

    await ctx.send(roll(ctx.message.author.name, userstring, args))

@bot.command(name='stat', help='View and adjust your stats.')
async def stat(ctx, *args):
    db = get_db()
    cur = db.cursor()

    userstring = f"WHERE server = {ctx.message.guild.id} AND player = {ctx.message.author.id}"

    if len(args) == 1:
        if args[0] == 'init':
            cur.execute(f"DELETE FROM characters {userstring}")
            db.commit()
            cur.execute(f"INSERT INTO characters (server, player, phy, ref, sta, kno, ins, pow) VALUES ({ctx.message.guild.id}, {ctx.message.author.id}, 10, 10, 10, 10, 10, 10)")            
            db.commit()

    if not check_stats(userstring):
        await ctx.send('Stats not yet initialized, please use `!stat init` to do so')
        return


    if len(args) > 1 and args[0] == 'phy':
        arrgay = list(args);
        arrgay.remove('phy');
        arrgay = "".join(arrgay).replace(' ', '')
        if arrgay[0] == '+':
            arrgay = list(arrgay)
            arrgay.remove('+')
            arrgay = int("".join(arrgay))
            print(f"update characters set phy = phy + {arrgay} {userstring}")
            cur.execute(f"update characters set phy = phy + {arrgay} {userstring}")
        elif arrgay[0] == '-':
            arrgay = list(arrgay)
            arrgay.remove('-')
            arrgay = int("".join(arrgay))
            print(f"update characters set phy = phy - {arrgay} {userstring}")
            cur.execute(f"update characters set phy = phy - {arrgay} {userstring}")
        elif arrgay[0] == '=' or int(arrgay[0]) > 0:
            arrgay = list(arrgay)
            if arrgay[0] == '=':
                arrgay.remove('=')
            arrgay = int("".join(arrgay))
            print(f"update characters set phy = {arrgay} {userstring}")
            cur.execute(f"update characters set phy = {arrgay} {userstring}")
        db.commit()

    elif len(args) > 1 and args[0] == 'ref':
        arrgay = list(args);
        arrgay.remove('ref');
        arrgay = "".join(arrgay).replace(' ', '')
        if arrgay[0] == '+':
            arrgay = list(arrgay)
            arrgay.remove('+')
            arrgay = int("".join(arrgay))
            print(f"update characters set ref = ref + {arrgay} {userstring}")
            cur.execute(f"update characters set ref = ref + {arrgay} {userstring}")
        elif arrgay[0] == '-':
            arrgay = list(arrgay)
            arrgay.remove('-')
            arrgay = int("".join(arrgay))
            print(f"update characters set ref = ref - {arrgay} {userstring}")
            cur.execute(f"update characters set ref = ref - {arrgay} {userstring}")
        elif arrgay[0] == '=' or int(arrgay[0]) > 0:
            arrgay = list(arrgay)
            if arrgay[0] == '=':
                arrgay.remove('=')
            arrgay = int("".join(arrgay))
            print(f"update characters set ref = {arrgay} {userstring}")
            cur.execute(f"update characters set ref = {arrgay} {userstring}")
        db.commit()

    elif len(args) > 1 and args[0] == 'sta':
        arrgay = list(args);
        arrgay.remove('sta');
        arrgay = "".join(arrgay).replace(' ', '')
        if arrgay[0] == '+':
            arrgay = list(arrgay)
            arrgay.remove('+')
            arrgay = int("".join(arrgay))
            print(f"update characters set sta = sta + {arrgay} {userstring}")
            cur.execute(f"update characters set sta = sta + {arrgay} {userstring}")
        elif arrgay[0] == '-':
            arrgay = list(arrgay)
            arrgay.remove('-')
            arrgay = int("".join(arrgay))
            print(f"update characters set sta = sta - {arrgay} {userstring}")
            cur.execute(f"update characters set sta = sta - {arrgay} {userstring}")
        elif arrgay[0] == '=' or int(arrgay[0]) > 0:
            arrgay = list(arrgay)
            if arrgay[0] == '=':
                arrgay.remove('=')
            arrgay = int("".join(arrgay))
            print(f"update characters set sta = {arrgay} {userstring}")
            cur.execute(f"update characters set sta = {arrgay} {userstring}")
        db.commit()

    elif len(args) > 1 and args[0] == 'kno':
        arrgay = list(args);
        arrgay.remove('kno');
        arrgay = "".join(arrgay).replace(' ', '')
        if arrgay[0] == '+':
            arrgay = list(arrgay)
            arrgay.remove('+')
            arrgay = int("".join(arrgay))
            print(f"update characters set kno = kno + {arrgay} {userstring}")
            cur.execute(f"update characters set kno = kno + {arrgay} {userstring}")
        elif arrgay[0] == '-':
            arrgay = list(arrgay)
            arrgay.remove('-')
            arrgay = int("".join(arrgay))
            print(f"update characters set kno = kno - {arrgay} {userstring}")
            cur.execute(f"update characters set kno = kno - {arrgay} {userstring}")
        elif arrgay[0] == '=' or int(arrgay[0]) > 0:
            arrgay = list(arrgay)
            if arrgay[0] == '=':
                arrgay.remove('=')
            arrgay = int("".join(arrgay))
            print(f"update characters set kno = {arrgay} {userstring}")
            cur.execute(f"update characters set kno = {arrgay} {userstring}")
        db.commit()

    elif len(args) > 1 and args[0] == 'ins':
        arrgay = list(args);
        arrgay.remove('ins');
        arrgay = "".join(arrgay).replace(' ', '')
        if arrgay[0] == '+':
            arrgay = list(arrgay)
            arrgay.remove('+')
            arrgay = int("".join(arrgay))
            print(f"update characters set ins = ins + {arrgay} {userstring}")
            cur.execute(f"update characters set ins = ins + {arrgay} {userstring}")
        elif arrgay[0] == '-':
            arrgay = list(arrgay)
            arrgay.remove('-')
            arrgay = int("".join(arrgay))
            print(f"update characters set ins = ins - {arrgay} {userstring}")
            cur.execute(f"update characters set ins = ins - {arrgay} {userstring}")
        elif arrgay[0] == '=' or int(arrgay[0]) > 0:
            arrgay = list(arrgay)
            if arrgay[0] == '=':
                arrgay.remove('=')
            arrgay = int("".join(arrgay))
            print(f"update characters set ins = {arrgay} {userstring}")
            cur.execute(f"update characters set ins = {arrgay} {userstring}")
        db.commit()

    elif len(args) > 1 and args[0] == 'pow':
        arrgay = list(args);
        arrgay.remove('pow');
        arrgay = "".join(arrgay).replace(' ', '')
        if arrgay[0] == '+':
            arrgay = list(arrgay)
            arrgay.remove('+')
            arrgay = int("".join(arrgay))
            print(f"update characters set pow = pow + {arrgay} {userstring}")
            cur.execute(f"update characters set pow = pow + {arrgay} {userstring}")
        elif arrgay[0] == '-':
            arrgay = list(arrgay)
            arrgay.remove('-')
            arrgay = int("".join(arrgay))
            print(f"update characters set pow = pow - {arrgay} {userstring}")
            cur.execute(f"update characters set pow = pow - {arrgay} {userstring}")
        elif arrgay[0] == '=' or int(arrgay[0]) > 0:
            arrgay = list(arrgay)
            if arrgay[0] == '=':
                arrgay.remove('=')
            arrgay = int("".join(arrgay))
            print(f"update characters set pow = {arrgay} {userstring}")
            cur.execute(f"update characters set pow = {arrgay} {userstring}")
        db.commit()


    #cur.execute(f"insert into characters (server, player, phy, ref, sta, kno, ins, pow) VALUES ({ctx.message.guild.id}, {ctx.message.author.id}, 7, 9, 12, 14, 16, 18)")

    #mydb.commit()
    cur.execute(f"SELECT * FROM characters {userstring}")
    stats = cur.fetchone()

    await ctx.send('Stats:\nPhy: **' + str(stats[3]) + '**, Ref: **' + str(stats[4]) + '**, Sta: **' + str(stats[5]) + '**, Kno: **' + str(stats[6]) + '**, Ins: **' + str(stats[7]) + '**, Pow: **' + str(stats[8]) + '**, ')

bot.run(TOKEN)
