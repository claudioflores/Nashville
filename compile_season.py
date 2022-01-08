# -*- coding: utf-8 -*-
"""
Created on Fri Jan  7 15:06:28 2022

@author: cflores
"""
import os
from utils import compile_files

league = 'MLS'
season = 2021

path = os.getcwd()+'\\'+league
path2 = league+'\\Season_'+str(season)
os.chdir(path2)

list_files = os.listdir()
list_files_games = [x for x in list_files if ('.csv'.lower() in x.lower())&('games_'.lower() in x.lower())]
list_files_players = [x for x in list_files if ('.csv'.lower() in x.lower())&('players_'.lower() in x.lower())]
list_files_keepers = [x for x in list_files if ('.csv'.lower() in x.lower())&('keepers_'.lower() in x.lower())]
list_files_shots = [x for x in list_files if ('.csv'.lower() in x.lower())&('shots_'.lower() in x.lower())]

df_games = compile_files(list_files_games)
df_players = compile_files(list_files_players)
df_keepers = compile_files(list_files_keepers)
df_shots = compile_files(list_files_shots)

os.chdir(path)
df_games.to_csv('games_'+str(season)+'.csv',index=False)
df_players.to_csv('players_'+str(season)+'.csv',index=False)
df_keepers.to_csv('keepers_'+str(season)+'.csv',index=False)
df_shots.to_csv('shots_'+str(season)+'.csv',index=False)

