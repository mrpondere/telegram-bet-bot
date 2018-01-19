BET BOT
=======

Summary
-------

Una especie de comando donde se vea un ranking de los que mayor win rate tienen
Y una especia de comando /bets
Que salen los partidos (podemos meter los partidos alguien con un comando oculto y por privado hablándole al bot)
y cada uno elige el ganador y tal y luego se mete quien ha ganado y se va actualizando la clasificación

BOT COMMANDS
------------

* /bets -> The available matches to bet on
* /bet -> Bet on a match
* /top10 -> Shows top 10 players
* /top10rate -> Top 10 win rate
* /addmatch -> Add a match to bet on
* /setscore -> Set match score
* /deletematch -> Removes a match


TABLES
------


## Matches

| ID  | TEAM 1    | TEAM 2    | SCORE1 | SCORE2 |
| --- | --------- | --------- | ------ | ------ |
| 1   | NIP       | INMORTALS | 22     | 16     |
| 2   | NAVI      | FNATIC    | 16     | 5      |

## Ranking

| player_id | wins | total | telegram *|
| --------- | ---- | ----- | --------- |
| 141241    | 0    | 2     | Pepito    |
| 312415    | 2    | 2     | Pondere   |

## Bets

| ID  | User      | Match     | WINNER |
| --- | --------- | --------- | ------ |
| 1   | 1451323   | 1         | NIP    |
| 2   | 24124124  | 2         | FNATIC |

> Telegram nick will be used to display the top 10.


Bot Params
----------

lang='es' -> Will change the language of the bot, to add a new language just
edit lang.json files.

admins=[12412421, 4124124] -> Will change the administrators of the bot (to
add matches and delete matches). It must be a list with the id's of the admins
separated by commas.

Instalation
-----------

`pip install requirements.txt`
`python betMODEL.py`

And you will be ready to start it:

`python betBOT.py`
