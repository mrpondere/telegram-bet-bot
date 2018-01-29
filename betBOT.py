#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import unicodedata

import sys
import ast
import datetime

from telebot import TeleBot, types
from emoji import emojize
from betMODEL import Match, Ranking, Bet, User, get_matches, get_bets, \
     get_users, get_ranking, add, update, delete, get_session
from betLANG import gettext, change_lang


token = os.environ.get('betBOT')

_ = gettext

if not token:
    sys.exit(_('Add an enviroment variable $betBOT with your token.'))

if sys.argv[1] and 'lang=' in sys.argv[1]:
    lang = sys.argv[1].split('=')[1]
    change_lang(lang)

if sys.argv[2] and 'admins=' in sys.argv[2]:
    administrators = ast.literal_eval(sys.argv[2][7:])


bot = TeleBot(token)
userStep = {}
knownUsers = []
to_add = {}
to_winner = {}
to_bet = {}
commands = {
    'help': _('Gives you information about the available commands'),
    'bet': _('Add a bet in a match'),
    'mybets': _('Show my active bets'),
    'bets': _('Show active matches'),
    'mybets': _('Show your bet stats'),
    'history': _('Show match result history'),
    'top10': _('Shows the top 10 players with wins and totale'),
    'top10rate': _('Shows the top10 players ordered by win percentage'),
    'notify': _('Notify when a match is added.'),
    'addmatch': _('Add a Match to bet on'),
    'deletematch': _('Remove a previously added match'),
    'setscore': _('Sets the score of an ended match.'),
}


def get_user_step(uid):
    if uid in userStep:
        return userStep[uid]


@bot.message_handler(commands=['bet'])
def do_bet(message):
    if message.chat.id != message.from_user.id:
        bot.send_message(message.chat.id,
            _('This command can not be used on group chats.'))
        return
    get_user(message)
    chat_id = message.chat.id
    query = get_matches()
    matches = query.filter(Match.score1 == None).filter(
        Match.start_date > datetime.datetime.now()).all()
    query = get_bets()
    user_bets = query.filter(Bet.player_id == message.from_user.id).all()
    markup = types.ReplyKeyboardMarkup(row_width=len(matches))
    to_bet = 0
    for m in matches:
        skip = 0
        for b in user_bets:
            if b.match == m.id:
                skip = 1
                break
        if skip == 1:
            continue
        else:
            to_bet += 1
        markup.add(
            str(m.id) + ' - ' + m.team1 + ' - ' + m.team2)
    if(not matches or not to_bet):
        bot.send_message(message.chat.id,
            _('No matches available (Or you already bet on all).'))
        return
    markup.add(_('Cancel'))
    bot.send_message(chat_id, _('Choose a match:'), reply_markup=markup)
    userStep[message.from_user.id] = 51


@bot.message_handler(func=lambda
    message: get_user_step(message.from_user.id) == 51)
def do_bet_winner(message):
    chat_id = message.chat.id
    mid = message.text.split(' ')
    query = get_matches()
    try:
        match = query.filter(Match.id == int(mid[0])).one()
        to_bet[message.from_user.id] = mid
        markup = types.ReplyKeyboardMarkup(row_width=2)
        markup.add(match.team1)
        markup.add(match.team2)
        bot.send_message(chat_id, _('Choose a winner:'), reply_markup=markup)
        userStep[message.from_user.id] = 52
    except ValueError:
        markup = types.ReplyKeyboardHide()
        bot.send_message(message.chat.id, _('Action cancelled.'),
            reply_markup=markup)


@bot.message_handler(func=lambda
    message: get_user_step(message.from_user.id) == 52)
def set_match_winner_db(message):
    userStep[message.from_user.id] = None
    chat_id = message.chat.id
    markup = types.ReplyKeyboardHide()
    mid = to_bet[message.from_user.id]
    query = get_bets()
    # TODO Add unique constraint on sql match and return error if already bet
    already_bet = query.filter(
        Bet.player_id == message.from_user.id).filter(
            Bet.match == mid[0]).first()
    if already_bet:
        bot.send_message(chat_id, _('You have already bet on this match.'),
            reply_markup=markup)
        return
    new_bet = Bet(player_id=message.from_user.id, match=mid[0],
        bet=message.text)
    add(new_bet)
    bot.send_message(chat_id, _('Bet correctly done.'), reply_markup=markup)
    userStep[message.from_user.id] = None


@bot.message_handler(commands=['bets'])
def list_bets(message):
    query = get_matches()
    matches = query.filter(Match.score1 == None).all()
    text = ''
    query = get_bets()
    for m in matches:
        bets = query.filter(Bet.match == m.id).all()
        date = m.start_date.strftime('%d-%m-%Y')
        hour = m.start_date.strftime('%H:%M')
        bets1 = 0
        bets2 = 0
        for b in bets:
            if b.bet == m.team1:
                bets1 += 1
            elif b.bet == m.team2:
                bets2 += 1
        odd1 = 0
        odd2 = 0
        if bets1 or bets2:
            odd1 = bets1 * 100 / (bets1 + bets2)
            odd2 = bets2 * 100 / (bets1 + bets2)
        text += (emoji(':calendar:') + date + ' ' + emoji(':clock1:') + hour
            + ' ' + emoji(' :fast_forward:') + ' *' + m.team1 + '* '
            + str(odd1) + '%' + ' ' + emoji(':vs:') + ' ' + str(odd2) + '% *'
            + m.team2 + '*\n')
    if(not matches):
        bot.send_message(message.chat.id, _('No matches available.'))
    else:
        bot.send_message(message.chat.id, text, parse_mode='markdown')


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    cid = message.chat.id
    query = get_users()
    user = query.filter(User.player_id == message.from_user.id).first()
    help_text = _('Talk me in private to get the command list.')
    if user:
        cid = message.from_user.id
        help_text = _('The following commands are available:') + '\n'
        for key in commands:
            help_text += "/" + key + ": "
            help_text += commands[key] + "\n"
    bot.send_message(cid, help_text)


@bot.message_handler(commands=['addmatch'])
def add_match(message):
    chat_id = message.chat.id
    if message.from_user.id not in administrators:
        bot.send_message(message.chat.id, _('You can not use this command.'))
        return
    if chat_id != message.from_user.id:
        bot.send_message(message.chat.id,
            _('This command can not be used on group chats.'))
        return
    markup = types.ForceReply(selective=False)
    bot.send_message(chat_id, _('Team A name:'), reply_markup=markup)
    to_add[message.from_user.id] = {}
    userStep[message.from_user.id] = 21


@bot.message_handler(func=lambda
    message: get_user_step(message.from_user.id) == 21)
def msg_add_match_team1(message):
    markup = types.ForceReply(selective=False)
    to_add[message.from_user.id]['Team1'] = message.text
    bot.send_message(message.chat.id, _('Team B name:'), reply_markup=markup)
    userStep[message.from_user.id] = 22


@bot.message_handler(func=lambda
    message: get_user_step(message.from_user.id) == 22)
def msg_add_match_team2(message):
    to_add[message.from_user.id]['Team2'] = message.text
    markup = types.ReplyKeyboardMarkup(row_width=3)
    buttons = []
    for i in range(0, 6):
        date = datetime.datetime.today() + datetime.timedelta(days=i)
        buttons.append(date.strftime("%d-%m-%Y"))
    markup.add(buttons[0], buttons[1], buttons[2])
    markup.add(buttons[3], buttons[4], buttons[5])
    bot.send_message(message.chat.id, _('Match date:'), reply_markup=markup)
    userStep[message.from_user.id] = 23


@bot.message_handler(func=lambda
    message: get_user_step(message.from_user.id) == 23)
def msg_add_match_date(message):
    chat_id = message.chat.id
    markup = types.ReplyKeyboardHide()
    bot.send_message(chat_id, _('Date set correctly.'), reply_markup=markup)
    markup = types.ForceReply(selective=False)
    to_add[message.from_user.id]['date'] = message.text
    bot.send_message(message.chat.id, _('Match hour:'), reply_markup=markup)
    userStep[message.from_user.id] = 24


@bot.message_handler(func=lambda
    message: get_user_step(message.from_user.id) == 24)
def msg_add_match_hour(message):
    to_add[message.from_user.id]['hour'] = message.text
    add_match_db(message)


def add_match_db(message):
    teams = to_add[message.from_user.id]
    date = teams['date'] + ' ' + teams['hour']
    date_time = datetime.datetime.strptime(date, '%d-%m-%Y %H:%M')
    new_match = Match(team1=teams['Team1'], team2=teams['Team2'],
        start_date=date_time)
    add(new_match)
    bot.send_message(message.chat.id, _('Added correctly.'))
    # Notify
    query = get_users()
    notify = query.filter(User.notify == 1).all()
    notify = [1346477]
    for u in notify:
        try:
            bot.send_message(u.player_id,
                _('New match added - %(1)s %(vs)s %(2)s')
                % {'1': teams['Team1'], 'vs': emoji(':vs:'),
                    '2': teams['Team2']})
        except Exception:
            # Set notify to 0 if error (because user stopped bot /stop)
            user = query.filter(User.player_id == message.from_user.id).first()
            user.notify = 0
            update()
    userStep[message.from_user.id] = None


@bot.message_handler(commands=['setscore'])
def set_winner(message):
    chat_id = message.chat.id
    if message.from_user.id not in administrators:
        bot.send_message(message.chat.id, _('You can not use this command.'))
        return
    if chat_id != message.from_user.id:
        bot.send_message(message.chat.id,
            _('This command can not be used on group chats.'))
        return
    query = get_matches()
    matches = query.filter(Match.score1 == None).filter(
        Match.score1 == None).all()
    if not matches:
        bot.send_message(message.chat.id, _('No matches available.'))
        return
    markup = types.ReplyKeyboardMarkup(row_width=len(matches))
    for m in matches:
        markup.add(
            str(m.id) + ' - ' + m.team1 + ' - ' + m.team2)
    markup.add(_('Cancel'))
    bot.send_message(chat_id, _("Choose a match:"), reply_markup=markup)
    userStep[message.from_user.id] = 31


@bot.message_handler(func=lambda
    message: get_user_step(message.from_user.id) == 31)
def confirm_match_choose(message):
    if(message.text == 'cancel' or message.text == 'Cancel'):
        markup = types.ReplyKeyboardHide()
        bot.send_message(message.chat.id, _('Action cancelled.'),
            reply_markup=markup)
        userStep[message.from_user.id] = None
        return
    chat_id = message.chat.id
    markup = types.ReplyKeyboardHide()
    bot.send_message(chat_id, _('Match selected correctly.'),
        reply_markup=markup)
    mid = message.text.split(' ')
    query = get_matches()
    match = query.filter(Match.id == int(mid[0])).one()
    to_winner[message.from_user.id] = {
        'id': match.id,
        'team1': match.team1,
        'team2': match.team2
    }
    markup = types.ForceReply(selective=False)
    bot.send_message(chat_id, match.team1 + ' ' + _('Score:'),
        reply_markup=markup)
    userStep[message.from_user.id] = 32


@bot.message_handler(func=lambda
    message: get_user_step(message.from_user.id) == 32)
def second_score(message):
    chat_id = message.chat.id
    markup = types.ForceReply(selective=False)
    to_winner[message.from_user.id]['score1'] = message.text
    team2 = to_winner[message.from_user.id]['team2']
    bot.send_message(chat_id, team2 + ' ' + _("Score:"), reply_markup=markup)
    userStep[message.from_user.id] = 33


@bot.message_handler(func=lambda
    message: get_user_step(message.from_user.id) == 33)
def set_bet_db(message):
    chat_id = message.chat.id
    markup = types.ReplyKeyboardHide()
    bot.send_message(chat_id, _('Winner correctly selected.'),
        reply_markup=markup)
    query = get_matches()
    match = query.filter(
        Match.id == to_winner[message.from_user.id]['id']).first()
    match.score1 = to_winner[message.from_user.id]['score1']
    match.score2 = message.text

    update()
    query = get_bets()
    bets = query.filter(
        Bet.match == to_winner[message.from_user.id]['id']).all()
    for b in bets:
        query = get_ranking()
        ranking = query.filter(
            Ranking.player_id == b.player_id).first()
        if not ranking:
            ranking = Ranking(player_id=b.player_id)
            add(ranking)
        ranking.total += 1
        winner = ('team1' if int(message.text) <
            int(to_winner[message.from_user.id]['score1']) else 'team2')
        if to_winner[message.from_user.id][winner] == b.bet:
            ranking.wins += 1
        update()
    userStep[message.from_user.id] = None


@bot.message_handler(commands=['deletematch'])
def del_match(message):
    chat_id = message.chat.id

    if message.from_user.id not in administrators:
        bot.send_message(message.chat.id, _('You can not use this command.'))
        return
    if chat_id != message.from_user.id:
        bot.send_message(message.chat.id,
            _('This command can not be used on group chats.'))
        return
    query = get_matches()
    matches = query.filter(Match.score1 == None).all()
    markup = types.ReplyKeyboardMarkup(row_width=len(matches))
    for m in matches:
        markup.add(
            str(m.id) + ' ' + m.team1 + ' ' + m.team2)
    if(not matches):
        bot.send_message(message.chat.id, _('No matches available.'))
        return
    markup.add(_('Cancel'))
    bot.send_message(chat_id, _("Choose a match:"), reply_markup=markup)
    userStep[message.from_user.id] = 41


@bot.message_handler(func=lambda
    message: get_user_step(message.from_user.id) == 41)
def del_match_db(message):
    chat_id = message.chat.id
    markup = types.ReplyKeyboardHide()
    match = message.text.split(' ')
    try:
        response = _("Match correctly deleted.")
        query = get_matches()
        query.filter(Match.id == int(match[0])).delete()
        delete(Match, Match.id == int(match[0]))
    except ValueError:
        response = _("Action canceled")
    bot.send_message(chat_id, response, reply_markup=markup)
    userStep[message.from_user.id] = None


@bot.message_handler(commands=['top10'])
def top_10(message):
    chat_id = message.chat.id
    query = get_ranking()
    rankings = (query.order_by(Ranking.wins.desc())
        .order_by(Ranking.total.desc()).all())
    text = _('No user with any resolved bet.')
    if rankings:
        text = (emoji(':trophy:') + ' ' + _('TOP 10 WINS') + ' '
            + emoji(':trophy:') + '\n')
        text += '-----------------\n'

    query = get_users()
    count = 0
    for ra in rankings:
        if count == 10:
            break
        count += 1
        username = query.filter(
            User.player_id == ra.player_id).first()
        textu = '<pre>'
        textu += username.telegram.encode('UTF-8')
        textu += ' ' * (20 - len(textu)) + ' '
        textu += '</pre>'
        # text += '{0: <15}'.format(username.telegram)
        textu += emoji(':trophy:') + ' ' + str(ra.wins)
        textu += emoji(':video_game:') + ' ' + str(ra.total) + '\n'
        text += textu
    bot.send_message(chat_id, text, parse_mode="html")


@bot.message_handler(commands=['top10rate'])
def top_10_rate(message):
    chat_id = message.chat.id
    query = get_ranking()
    session = get_session()
    rankings = session.execute(
        'select id, player_id, (wins * 100 / total) as percentage, total'
        ' from ranking group by player_id, percentage, total, id '
        'having total > (select max(total) from ranking) / 2 '
        'order by percentage desc limit 10').fetchall()
    text = _('No user with any resolved bet.')

    if rankings:
        text = '🏆 TOP 10 WIN RATE 🏆 \n' if rankings else ''
        text += '═══════════════════\n'

    query = get_users()
    for ra in rankings:
        username = query.filter(
            User.player_id == ra[1]).first()
        # textu = '{0: <15}'.format(username.telegram)
        textu = '<pre>'
        textu += username.telegram.encode('UTF-8')
        textu += ' ' * (20 - len(textu)) + ' '
        textu += '</pre>'
        textu += emoji(':game_die:').encode('UTF-8')
        textu += ' ' + str(ra[2]) + '% \n'
        text += textu
    bot.send_message(chat_id, text, parse_mode="html")


@bot.message_handler(commands=['mestats'])
def mestats(message):
    chat_id = message.chat.id
    query = get_ranking()
    ra = query.filter(Ranking.player_id == message.from_user.id).first()
    query = get_users()
    username = query.filter(
        User.player_id == message.from_user.id).first()
    text = _('You do not have any resolved bet yet.')
    if username and username.telegram:
        text = username.telegram.encode('UTF-8') + ' \n'
        text += emoji(':trophy:') + ' ' + str(ra.wins) + ' \n'
        text += emoji(':1234:') + ' ' + str(ra.total) + ' \n'
        text += (emoji(':chart_with_upwards_trend:') + ' '
            + str(ra.wins * 100 / ra.total) + '%')
    bot.send_message(chat_id, text)


@bot.message_handler(commands=['mybets'])
def mybets(message):
    query = get_bets()
    bets = query.filter(Bet.player_id == message.from_user.id).all()
    text = ''
    query = get_matches()
    for b in bets:
        m = query.filter(Match.id == b.match).first()
        if m and (m.start_date > datetime.datetime.now() or m.score1 == None):
            text += (m.team1 + ' ' + emoji(':vs:') + ' ' + m.team2 + ' - '
                + emoji(':video_game:') + ' <b>' + b.bet + '</b>\n')
    if(not bets or not text):
        bot.send_message(message.chat.id, _('No bets available.'))
    else:
        bot.send_message(message.chat.id, text, parse_mode='html')


@bot.message_handler(commands=['history'])
def history(message):
    query = get_matches()
    matches = query.filter(Match.start_date
        > datetime.datetime.now() - datetime.timedelta(days=5)).filter(
            Match.score1 != None).all()
    text = ''
    count = 0
    for m in matches:
        if count == 10:
            return
        count += 1
        winner = 'TBD'
        score1 = str(m.score1) + ' ' if m.score1 or m.score1 == 0 else ''
        score2 = str(m.score2) + ' ' if m.score2 or m.score1 == 0 else ''
        if m.score2 or m.score2 == 0 and m.score1 or m.score1 == 0:
            winner = (m.team1 if m.score2 < m.score1 else m.team2)
        text += ('<b> ' + score1 + '</b> ' + m.team1 + ' ' + emoji(':vs:')
            + ' <b>' + score2 + '</b> ' + ' ' + m.team2 + ' - '
            + emoji(':trophy:') + ' <b>' + winner + '</b>\n')
    if(not matches):
        bot.send_message(message.chat.id, _('No bets available.'))
    else:
        bot.send_message(message.chat.id, text, parse_mode='html')


@bot.message_handler(commands=['notify'])
def notify(message):
    chat_id = message.chat.id
    if chat_id != message.from_user.id:
        bot.send_message(message.chat.id,
            _('This command can not be used on group chats.'))
        return
    chat_id = message.chat.id
    query = get_users()
    user = query.filter(User.player_id == message.from_user.id).first()
    if user.notify:
        user.notify = 0
        bot.send_message(chat_id, _('You will no longer be notified.'))
    else:
        user.notify = 1
        bot.send_message(chat_id,
            _('You will be notified when a match is added.'))
    update()


def get_user(message):
    player_id = message.from_user.id
    query = get_users()
    user = query.filter(User.player_id == player_id).first()
    if user and user.telegram != message.from_user.first_name:
        user.telegram = unicodedata.normalize(
            'NFC', message.from_user.first_name).encode('ascii', 'ignore')
        update()
    if not user:
        user = User(player_id=message.from_user.id,
            telegram=message.from_user.username)
        add(user)


@bot.message_handler(commands=['test'])
def test(message):
    print message.from_user.first_name, message.from_user.last_name


def emoji(code):
    return emojize(code, use_aliases=True)


bot.polling()
