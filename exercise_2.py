# -*- coding: utf-8 -*-
"""
Created on Sat Jan  8 03:01:09 2022

@author: cflores
"""


'''
Exercise 2 

Fast forward to the 2022 MLS season, and the opening of the summer transfer window 
– Nashville SC is looking to bring in a reinforcement on the flanks. With a fluid system between 5-3-2 and 4-2-3-1, 
the team is looking for a versatile player that can play a variety of positions on the right and/or left side. 
The General Manager has asked you for the following: 
    1. Identify a shortlist of 5 players in MLS that fit the requested profile: 
        a versatile winger with attacking and defending 1v1 abilities, effective crossing in open play and set pieces, 
        and consistent fitness levels. 
    2. What are the key data points that suggest each player fits the profile? Where do they rank relative to other players? 
    3. What are the gaps in the player’s abilities/behaviors that need consideration? How confident are you in your analysis? 
    4. What are other considerations in the player’s profile? How will they fit in the current Nashville SC squad?
'''

#%%


import pandas as pd
from utils import summary_player

#%%

league = 'MLS'
season = 2021
path = league+'\\'

df_players = pd.read_csv(path+'players_'+str(season)+'.csv')
df_shots = pd.read_csv(path+'shots_'+str(season)+'.csv')
df_games = pd.read_csv(path+'games_'+str(season)+'.csv')

#%% Flank positions

all_positions = list(df_players['position'].unique())
flank_positions = []

for position in all_positions:
    if any(n in position for n in ['LB','WB','LW','RW']):
        flank_positions.append(position)
        
df_players = df_players[df_players.position.isin(flank_positions)]  
df_shots = df_shots[df_shots.player_id.isin(df_players.player_id)]  
 
#%% Players Summary

cols_agg = list(df_players)
remove_list = ['shirtnumber','nationality','position','age','name','player_id','game_id','team_id','team_location']
for col in remove_list: cols_agg.remove(col)
player_summary = df_players.groupby(['player_id','name','team_id'])[cols_agg].agg('sum').reset_index()

player_summary['dribbles_completed_pct'] = player_summary['dribbles_completed']/player_summary['dribbles']
player_summary['passes_pct_long'] = player_summary['passes_completed_long']/player_summary['passes_long']
player_summary['dribble_tackles_pct'] = player_summary['dribble_tackles']/player_summary['dribbles_vs']
player_summary['pressure_regain_pct'] = player_summary['pressure_regains']/player_summary['pressures']

player_summary['tackles_won_pct'] = player_summary['tackles_won']/player_summary['tackles']
player_summary['passes_weak_foot_pct'] = [min(l,r)/(l+r) if l+r>0 else None for l,r in zip(player_summary['passes_left_foot'],player_summary['passes_right_foot'])] 
player_summary['passes_weak_foot_pct_ratio'] = 0.5 + player_summary['passes_weak_foot_pct']

#%% Player Set Pieces

df_shots['goal'] = [1 if x == 'Goal' else 0 for x in df_shots['outcome']]
shots_ongoal = df_shots[(df_shots['notes']=='Free kick')|(df_shots['notes']=='Free kick, Deflected')]
shots_assisted1 = df_shots[(df_shots['sca_1_type']=='Pass (Dead)')]
shots_assisted2 = df_shots[(df_shots['sca_2_type']=='Pass (Dead)')]
aux1 = shots_assisted1[['player_id','player','goal','distance','body_part','notes','sca_1_player']]
aux2 = shots_assisted2[['player_id','player','goal','distance','body_part','notes','sca_2_player']]
aux1.columns = ['player_id','player','goal','distance','body_part','notes','sca_player']
aux2.columns = ['player_id','player','goal','distance','body_part','notes','sca_player']
shots_assisted = aux1.append(aux2)

freekick_goals = shots_ongoal.groupby(['player_id','player']).agg({'goal':['count','sum']}).reset_index()
freekick_goals.columns = ['player_id','player','attempts','goals']
freekick_pass = shots_assisted.groupby(['player_id','player']).agg({'goal':['count','sum']}).reset_index()
freekick_pass.columns = ['player_id','player','attempts','goals']
                          
#%% Percentile for every stat

cols_percentile = []
for col in cols_agg+['tackles_won_pct','passes_weak_foot_pct_ratio']:
    col_perc = 'percentile_'+col
    cols_percentile.append(col_perc)
    player_summary[col_perc] = player_summary[col].rank(pct=True) 
    
set_pieces = freekick_goals[['player_id','player','goals']].merge(freekick_pass[['player_id','player','goals']],on=['player_id','player'],how='outer')
set_pieces = set_pieces.fillna(0)
cols_percentile2 = []
for col in ['goals_x','goals_y']:
    col_perc = 'percentile_'+col
    cols_percentile2.append(col_perc)
    set_pieces[col_perc] = set_pieces[col].rank(pct=True) 


#%% Relevant skills

#%% attacking
list_metric = ['crosses_into_penalty_area','crosses','passes_pct_long','dribbles_completed','dribbles']
aux_list = ['percentile_'+x for x in list_metric]
player_summary['attack'] = player_summary[aux_list].sum(axis=1)/len(aux_list)

print(player_summary[['name','attack']].sort_values('attack',ascending=False))

#%% defending

list_metric = ['pressure_regains','pressure_regain_pct','tackles_won','tackles_won_pct','dribble_tackles','dribble_tackles_pct', 'ball_recoveries']
aux_list = ['percentile_'+x for x in list_metric]
player_summary['defense'] = player_summary[aux_list].sum(axis=1)/len(aux_list)

print(player_summary[['name','defense']].sort_values('defense',ascending=False))

#%% fitness

list_metric = ['carry_distance','carry_progressive_distance']
aux_list = ['percentile_'+x for x in list_metric]
player_summary['fitness'] = player_summary[aux_list].sum(axis=1)/len(aux_list)

print(player_summary[['name','fitness']].sort_values('fitness',ascending=False))


#%% versatile

list_metric = ['passes_weak_foot_pct_ratio']
aux_list = ['percentile_'+x for x in list_metric]
player_summary['versatile'] = player_summary[aux_list].sum(axis=1)/len(aux_list)

print(player_summary[['name','versatile']].sort_values('versatile',ascending=False))


#%% set pieces

list_metric = ['goals_x','goals_y']
aux_list = ['percentile_'+x for x in list_metric]
set_pieces['setpieces'] = set_pieces[aux_list].sum(axis=1)/len(aux_list)

print(set_pieces[['player','setpieces']].sort_values('setpieces',ascending=False))

df_final = player_summary.merge(set_pieces[['player_id','setpieces']],on=['player_id'],how='left')
df_final = df_final.fillna(0)

#%% Final Score

teams = df_games[['id_home','team_home']].drop_duplicates()
df_finalfinal = df_final.merge(teams,left_on='team_id', right_on='id_home',how='left')

df_finalfinal['Score'] = 0.3*df_final['attack']+0.3*df_final['defense']+0.2*df_final['fitness']+0.1*df_final['versatile']+0.1*df_final['setpieces']

print(df_finalfinal[['name','team_home','attack','defense','fitness','versatile','setpieces','Score']].sort_values('Score',ascending=False).head(5))

df_finalfinal[['name','team_home','attack','defense','fitness','versatile','setpieces','Score']].sort_values('Score',ascending=False).head(5).to_csv('top5_flank.csv',index=False)


