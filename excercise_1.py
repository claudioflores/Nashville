# -*- coding: utf-8 -*-
"""
Created on Fri Jan  7 20:45:57 2022

@author: cflores
"""

'''
Exercisq 1

It’s Tuesday night, November 23rd, 2021 - Nashville SC has just defeated Orlando City SC 3-1 in the first round of the Playoffs. 
The team has training tomorrow to prepare for the upcoming match on Sunday vs. Philadelphia Union. 
The Head Coach has asked you for the following: 
    
1. Review of match vs. Orlando City SC What tactical trends for Nashville SC were evidenced by data? Include both positive and critical insights. 
2. Opposition report for next match vs. Philadelphia Union What data-supported insights can you provide to aid in preparation for the opponent? 
    Include both team and individual player insights. 
3. Set-piece report for next match vs. Philadelphia Union What are some statistical trends for the opponent’s set piece behavior?
'''

#%%

import pandas as pd
from utils import summary_stats,summary_player

#%%

league = 'MLS'
season = 2021
path = league+'\\'

df_games = pd.read_csv(path+'games_'+str(season)+'.csv')
df_players = pd.read_csv(path+'players_'+str(season)+'.csv')
df_keepers = pd.read_csv(path+'keepers_'+str(season)+'.csv')
df_shots = pd.read_csv(path+'shots_'+str(season)+'.csv')

#%%
df_games['date'] = df_games['date'].apply(pd.to_datetime)
df_players['date'] = df_players.merge(df_games[['game_id','date']],on='game_id')['date']


#%% Part 1 - Tactical trends game agains Orlando City

nashville_id = df_games[df_games['team_home'].str.contains('Nashville',na=False)][['team_home','id_home']].drop_duplicates()['id_home'].iloc[0]
orlando_id = df_games[df_games['team_home'].str.contains('Orlando',na=False)][['team_home','id_home']].drop_duplicates()['id_home'].iloc[0]
game_id = df_games[(df_games['id_home']==nashville_id)&(df_games['date']=='2021-11-23')]['game_id'].iloc[0]

previous_games = df_players[(df_players['team_id']==nashville_id)&(df_players['date']<'2021-11-23')]
current_game = df_players[(df_players['game_id']==game_id)&(df_players['team_location']=='home')]

summary_season,cols_summary = summary_stats(previous_games)
summary_season['analysis'] = 1
mean = summary_season.groupby(['analysis'])[cols_summary].agg('mean').reset_index().T
std = summary_season.groupby(['analysis'])[cols_summary].agg('std').reset_index().T

summary_game,cols_summary = summary_stats(current_game)
summary_game['analysis'] = 1
game = summary_game.groupby(['analysis'])[cols_summary].agg('mean').reset_index().T

final = pd.concat([mean, std,game], axis=1)
final.columns = ['mean','std','game']
final['dif'] = final['game']-final['mean']
final['ratio'] = final['dif']/final['std']

print(final.sort_values('ratio',ascending=True).head(10)[['mean','std','ratio','game']])
print(final.sort_values('ratio',ascending=False).head(20)[['mean','std','ratio','game']])


#%% Part 2 - Philadelphia Assesment

#%%Team
philadelphia_id = df_games[df_games['team_home'].str.contains('Philadelphia',na=False)][['team_home','id_home']].drop_duplicates()['id_home'].iloc[0]
philadelphia_season = df_players[(df_players['team_id']==philadelphia_id)&(df_players['date']<='2021-11-23')]
summary_phily,cols_summary = summary_stats(philadelphia_season)
summary_phily['analysis'] = 1
summary_phily_final = summary_phily.groupby(['analysis'])[cols_summary].agg('mean').reset_index().T

mls_season = df_players[(df_players['team_id']!=philadelphia_id)&(df_players['team_id']!=nashville_id)&(df_players['date']<='2021-11-23')]
summary_mls,cols_summary = summary_stats(mls_season)
summary_mls['analysis'] = 1
mls_season_final = summary_mls.groupby(['analysis'])[cols_summary].agg('mean').reset_index().T

phily_comparison = pd.concat([summary_phily_final, mls_season_final], axis=1)
phily_comparison.columns = ['Philadelphia','MLS']
phily_comparison['MLS2'] = phily_comparison['MLS']/2 #some of these metrics have to be divided by 2, didn't have enought time

phily_comparison.columns = ['Philadelpia','MLS','MLS2']
phily_comparison['dif']= phily_comparison['Philadelpia']-phily_comparison['MLS']
phily_comparison['perc']= phily_comparison['dif']/phily_comparison['MLS']
phily_comparison['dif2']= phily_comparison['Philadelpia']-phily_comparison['MLS2']
phily_comparison['perc2']= phily_comparison['dif2']/phily_comparison['MLS2']

print(phily_comparison[['Philadelpia','MLS','dif','perc']].sort_values('perc',ascending=True).head(20))
print(phily_comparison[['Philadelpia','MLS','dif','perc']].sort_values('perc',ascending=False).head(20))

print(phily_comparison[['Philadelpia','MLS2','dif2','perc2']].sort_values('perc2',ascending=True).head(20))
print(phily_comparison[['Philadelpia','MLS2','dif2','perc2']].sort_values('perc2',ascending=False).head(20))

#%%Players
mls_season2 = df_players[df_players['date']<='2021-11-23']

mls_players,cols_summary = summary_player(mls_season2)
mls_players = mls_players[mls_players['minutes']>=900]
cols_percentile = []

for col in cols_summary:
    col_perc = 'percentile_'+col
    cols_percentile.append(col_perc)
    mls_players[col_perc] = mls_players[col].rank(pct=True) 

mls_players = mls_players.reset_index()
phily_players = mls_players[mls_players.team_id==philadelphia_id]

for col in cols_percentile:
    if ('_pct' not in col)&('percentile_minutes'!=col): 
        aux = phily_players[phily_players[col]>0.95]
        if len(aux)>0:
            print(col,aux[['name',col]],'\n')

    
#%% Part 3 - Philadelphia Set Pieces

##Aerial Duels            
print(phily_players[['name','aerials_won_pct','percentile_aerials_won_pct']].sort_values('aerials_won_pct',ascending=False))

#%%
phily_shots = df_shots[(df_shots['team_id']==philadelphia_id)&((df_shots['notes']=='Free kick')|(df_shots['notes']=='Free kick, Deflected')|(df_shots['sca_1_type']=='Pass (Dead)')|(df_shots['sca_2_type']=='Pass (Dead)'))]
phily_shots['goal'] = [1 if x == 'Goal' else 0 for x in phily_shots['outcome']]

n_setpieces = len(phily_shots)

shots_ongoal = phily_shots[(phily_shots['notes']=='Free kick')|(phily_shots['notes']=='Free kick, Deflected')]
shots_assisted1 = phily_shots[(phily_shots['sca_1_type']=='Pass (Dead)')]
shots_assisted2 = phily_shots[(phily_shots['sca_2_type']=='Pass (Dead)')]
aux1 = shots_assisted1[['player','goal','distance','body_part','notes','sca_1_player']]
aux2 = shots_assisted2[['player','goal','distance','body_part','notes','sca_2_player']]
aux1.columns = ['player','goal','distance','body_part','notes','sca_player']
aux2.columns = ['player','goal','distance','body_part','notes','sca_player']
shots_assisted = aux1.append(aux2)

#%% Main shooters
print(shots_assisted.groupby('sca_player').size(),'\n')
print(shots_ongoal.groupby('player').agg({'goal':['count','sum']}),'\n')
print(shots_ongoal[['player','distance','goal']].sort_values('player'))

#%% Goals after set piece assist - doesn't include not connected

print(shots_assisted.groupby(['player']).agg({'goal':['count','sum']}),'\n')
print(len(shots_assisted),shots_assisted['goal'].sum(),round(len(shots_assisted)/shots_assisted['goal'].sum(),1))

#%% Corners

phily_corners = philadelphia_season.groupby('team_id').agg({'corner_kicks':'sum','corner_kicks_in':'sum','corner_kicks_out':'sum','corner_kicks_straight':'sum'}).reset_index()
print(phily_corners[['corner_kicks','corner_kicks_in','corner_kicks_out','corner_kicks_straight']])


