# -*- coding: utf-8 -*-
"""
Created on Wed Jan  5 23:00:28 2022

@author: cflores
"""

from utils import get_game_links, get_game_data

url = 'https://fbref.com/en/comps/22/schedule/Major-League-Soccer-Scores-and-Fixtures'
league = 'MLS'
season = 2021

game_links = get_game_links(url)

for link in game_links:
    try: 
        get_game_data(link,league,season)
        print('processed',link)
    except: 
        print('failed',link)

#%%

missing = ['dd643123','3c349b23','72ff090e','cb95a073','284b0a7a']
    
for link in missing:
    try: 
        get_game_data(link,league,season)
        print('processed',link)
    except: 
        print('failed',link)    