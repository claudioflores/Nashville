# -*- coding: utf-8 -*-
"""
Created on Wed Jan  5 22:54:13 2022

@author: cflores
"""
from selenium import webdriver
from bs4 import BeautifulSoup
import pandas as pd
import os
import time


# Returns id's by type
def get_id(x,type):
    start = len('/en/'+type+'/')+1
    end = x.find('/',start)
    return x[start:end]    

# Returns game ids 
def clean_link(x):
    try:
        link = x.find('a')['href']
        start = len('/en/matches')+1
        end = link.find('/',start)
        return link[start:end]
    except:
        pass


# Returns html from link
def get_html(link):
    driver = webdriver.Firefox(executable_path="geckodriver.exe")
    driver.set_page_load_timeout(100)
    driver.get(link)
    time.sleep(2)
    raw_data = driver.page_source
    driver.close()
    soup = BeautifulSoup(raw_data, "lxml") 
    return soup


# Returns game links
def get_game_links(link):    
    soup = get_html(link)  
    soup_links = soup.find_all('td',{'class':'center','data-stat':'score'})
    game_links = [clean_link(x) for x in soup_links if clean_link(x)]
    #game_links = [get_id(x,'matches') for x in soup_links if get_id(x,'matches')]
    game_links = list(set(game_links))
    return game_links


# Returns players table from game
def get_stats_game(tables_game):
    
    home_stats_player,home_stats_team = [],[]
            
    for table in tables_game:
        
        players = table.select('tr[data-row]')
        team_df,game_df = pd.DataFrame(),pd.DataFrame()
        n_players = len(players)
        
        for player in players:
            row = int(player.get('data-row'))    
            player_dic = {}    
            player_stats = player.findAll('td')  
            for i in range(len(player_stats)):
                player_dic[player_stats[i]['data-stat']] = player_stats[i].text
            if row+1<n_players:
               player_dic['player_id'] = player.find('th')['data-append-csv']
               player_dic['name'] = player.find('th')['csk'] 
               player_df = pd.DataFrame([player_dic])
               team_df = team_df.append(player_df)
            else:
                player_df = pd.DataFrame([player_dic])
                game_df = game_df.append(player_df)
                
        home_stats_player.append(team_df.copy())
        home_stats_team.append(game_df.copy())
    
    df1,df2 = home_stats_player[0],home_stats_team[0]
    for k in range(len(home_stats_player)-1):
        cols_to_use = list(home_stats_player[k+1].columns.difference(df1.columns))
        df1 = df1.merge(home_stats_player[k+1][['player_id']+cols_to_use],on=['player_id'])
        df2 = df2.join(home_stats_team[k+1][cols_to_use])
        
    df2.drop(['shirtnumber','nationality','position','age',], axis=1, inplace=True)
    
    return df1, df2


# Returns keepers table from game
def get_stats_keeper(table_keeper):
    
    keeper = table_keeper.select('tr[data-row]')
    player_stats = keeper[0].findAll('td')  
    keeper_dic = {}    
    keeper_dic['player_id'] = keeper[0].find('th')['data-append-csv']
    keeper_dic['name'] = keeper[0].find('th')['csk'] 
    for i in range(len(player_stats)):
        keeper_dic[player_stats[i]['data-stat']] = player_stats[i].text     
    keeper_df = pd.DataFrame([keeper_dic])    
    
    return keeper_df
        

# Returns shots table from game
# handle case when teams takes no shots
def get_stats_shoots(table_shoots):
    
    df = pd.DataFrame()
    shots = table_shoots.select('tr[data-row]')
    
    for shot in shots:
        try:
            shot_dic = {}    
            shot_dic['player_id'] = shot.find('td')['data-append-csv']
            shot_dic['minute'] = shot.find('th').text
            shots_stats = shot.findAll('td')      
            for i in range(len(shots_stats)):
                shot_dic[shots_stats[i]['data-stat']] = shots_stats[i].text
            shot_df = pd.DataFrame([shot_dic])
            df = df.append(shot_df)
        except:
            pass
       
    return df#.iloc[:-1] 


def get_player_tables(html,team_id):
    summary = html.find('table', attrs={'id':'stats_'+team_id+'_summary'})
    passing = html.find('table', attrs={'id':'stats_'+team_id+'_passing'})
    passtypes = html.find('table', attrs={'id':'stats_'+team_id+'_passing_types'})
    defense = html.find('table', attrs={'id':'stats_'+team_id+'_defense'})
    possession = html.find('table', attrs={'id':'stats_'+team_id+'_possession'})
    misc = html.find('table', attrs={'id':'stats_'+team_id+'_misc'})
    return([summary,passing,passtypes,defense,possession,misc])


# Returns game data
def get_game_data(game_id,league,year):
        
    base_link = 'https://fbref.com/en/matches/'
    link = base_link+game_id
    soup = get_html(link)  
    teams = soup.findAll('a',attrs={'itemprop':'name'})
    
    home_id = get_id(teams[0]['href'],'squad')
    home_team = teams[0].string
    away_id = get_id(teams[1]['href'],'squad')
    away_team = teams[1].string
    date = soup.find('span',class_='venuetime')['data-venue-date']
    score = soup.findAll('div',class_='score')
    home_score = int(score[0].text)
    away_score = int(score[1].text)
    if home_score>away_score: result = 'H'
    elif home_score<away_score: result = 'A'
    else: result = 'T'
    cols = ['game_id','date','id_home','team_home','id_away','team_away','score_home','score_away','result']
    values = [[game_id,date,home_id,home_team,away_id,away_team,home_score,away_score,result]]
    df_game = pd.DataFrame(values,columns=cols)
        
    # Players stats    
    tables_home = get_player_tables(soup,home_id) 
    tables_away = get_player_tables(soup,away_id) 
    df_game_players_home, df_game_summary_home = get_stats_game(tables_home)
    df_game_players_away, df_game_summary_away = get_stats_game(tables_away)
    
    df_game_players_home['team_id'] = home_id
    df_game_players_away['team_id'] = away_id
    df_game_players_home['game_id'] = game_id
    df_game_players_away['game_id'] = game_id
    df_game_players_home['team_location'] = 'home'
    df_game_players_away['team_location'] = 'away'
    
    df_game_players = df_game_players_home.append(df_game_players_away)
    
    df_game_summary_home = df_game_summary_home.add_suffix('_home')
    df_game_summary_away = df_game_summary_away.add_suffix('_away')
    
    df_game_summary= df_game_summary_home.merge(df_game_summary_away, left_index=True, right_index=True, suffixes=('_home', '_away'))
    df_game_final = df_game.merge(df_game_summary, left_index=True, right_index=True)
    
    cols_games = list(pd.read_csv('games_columns.csv',header=None)[0].tolist())
    cols_players = list(pd.read_csv('players_columns.csv',header=None)[0].tolist())
    df_game_finalfinal = pd.DataFrame(columns = cols_games)
    df_game_players_final = pd.DataFrame(columns = cols_players)
    df_game_finalfinal = df_game_finalfinal.append(df_game_final)
    df_game_players_final = df_game_players_final.append(df_game_players)    
    
    
    # Keeper stats
    #improve table selection - take into account keeper sub
    #table_keeper_home = soup.find('table', attrs={'id':'keeper_stats_'+home_id})
    tables_keeper = soup.findAll('table', class_='min_width sortable stats_table shade_zero now_sortable')    
    df_keeper_home = get_stats_keeper(tables_keeper[0])
    df_keeper_away = get_stats_keeper(tables_keeper[1])
    
    df_keeper_home['game_id'] = game_id
    df_keeper_away['game_id'] = game_id
    df_keeper_home['team_id'] = home_id
    df_keeper_away['team_id'] = away_id
    df_keeper_home['team_location'] = 'home'
    df_keeper_away['team_location'] = 'away'
    
    df_keepers = df_keeper_home.append(df_keeper_away)
    df_keepers['date'] = date
    
    # Shots stats
    # improve table selection
    # take into account table missing
    tables_shots = soup.findAll('table', class_='stats_table sortable min_width now_sortable')            
    df_shoots_home = get_stats_shoots(tables_shots[1])
    df_shoots_away = get_stats_shoots(tables_shots[2])
    
    df_shoots_home['game_id'] = game_id
    df_shoots_away['game_id'] = game_id
    df_shoots_home['team_id'] = home_id
    df_shoots_away['team_id'] = away_id
    df_shoots_home['team_location'] = 'home'
    df_shoots_away['team_location'] = 'away'
    
    df_shoots = df_shoots_home.append(df_shoots_away)
    df_shoots['date'] = date
    
    # Saving results
    
    path = os.getcwd()
    path2 = path+'\\'+league+'\\Season_'+str(year)
    
    try: 
        os.mkdir(league)
        os.chdir(league)
        os.mkdir('Season_'+str(year))
        os.chdir('Season_'+str(year))
    except: 
        pass
    
    os.chdir(path2)
    
    df_game_players_final.to_csv('players_'+game_id+'.csv', index=False)
    df_game_finalfinal.to_csv('games_'+game_id+'.csv', index=False)
    df_keepers.to_csv('keepers_'+game_id+'.csv', index=False)
    df_shoots.to_csv('shots_'+game_id+'.csv', index=False)
    
    os.chdir(path)
        
# Compiles files from a season into 1
def compile_files(list_files):
    df = pd.DataFrame()
    for file in list_files:
        aux = pd.read_csv(file)
        df = df.append(aux)
    return df  


def summary_stats(df):
    
    df = df.groupby(['game_id']).agg({
        'shots_total':'sum','assisted_shots':'sum','npxg':'sum','xa':'sum','sca':'sum','gca':'sum','through_balls':'sum',
        'pressures':'sum','pressure_regains':'sum',
        'pressures_att_3rd':'sum','pressures_mid_3rd':'sum','pressures_def_3rd':'sum',
        'touches_def_pen_area':'sum','touches_def_3rd':'sum','touches_mid_3rd':'sum','touches_att_3rd':'sum','touches_att_pen_area':'sum',
        'passes_ground':'sum', 'passes_low':'sum', 'passes_high':'sum',
        'passes_long':'sum','passes_completed_long':'sum','passes_medium':'sum','passes_completed_medium':'sum','passes_short':'sum','passes_completed_short':'sum',
        'passes_into_final_third':'sum','passes_into_penalty_area':'sum','crosses_into_penalty_area':'sum','progressive_passes':'sum',
        'progressive_carries':'sum', 'carries_into_final_third':'sum', 'carries_into_penalty_area':'sum',
        'carry_distance':'sum','carry_progressive_distance':'sum',
        'passes_total_distance':'sum','passes_progressive_distance':'sum',
        'aerials_lost':'sum', 'aerials_won':'sum'
        })
    
    df['pressure_effective'] = df['pressure_regains']/df['pressures']
    df['pressures_def_3rd_pct'] = df['pressures_def_3rd']/df['pressures']
    df['pressures_mid_3rd_pct'] = df['pressures_mid_3rd']/df['pressures']
    df['pressures_att_3rd_pct'] = df['pressures_att_3rd']/df['pressures']
    df['touches'] = df['touches_def_pen_area']+df['touches_def_3rd']+df['touches_mid_3rd']+df['touches_att_3rd']+df['touches_att_pen_area'] 
    df['touches_def_pen_area_pct'] = df['touches_def_pen_area']/df['touches']
    df['touches_def_3rd_pct'] = df['touches_def_3rd']/df['touches']
    df['touches_mid_3rd_pct'] = df['touches_mid_3rd']/df['touches']
    df['touches_att_3rd_pct'] = df['touches_att_3rd']/df['touches']
    df['touches_att_pen_area_pct'] = df['touches_att_pen_area']/df['touches']
    df['passes'] = df['passes_ground']+df['passes_low']+df['passes_high']
    df['passes_ground_pct'] = df['passes_ground']/df['passes']
    df['passes_low_pct'] = df['touches_att_pen_area']/df['passes']
    df['passes_high_pct'] = df['passes_high']/df['passes']
    df['passes_long_pct'] = df['passes_long']/df['passes']
    df['passes_medium_pct'] = df['passes_medium']/df['passes']
    df['passes_short_pct'] = df['passes_short']/df['passes']
    df['passes_completed_long_pct'] = df['passes_completed_long']/df['passes_long']
    df['passes_completed_medium_pct'] = df['passes_completed_medium']/df['passes_medium']
    df['passes_completed_short_pct'] = df['passes_completed_short']/df['passes_short']
    df['carry_progressive_distance_ratio'] = df['carry_progressive_distance']/df['carry_distance']
    df['passes_progressive_distance_ratio'] = df['passes_progressive_distance']/df['passes_total_distance']
    df['aerials'] = df['aerials_lost']+df['aerials_won']
    df['aerials_won_pct'] = df['aerials_won']/df['aerials']
    
    
    cols = ['shots_total', 'assisted_shots', 'npxg', 'xa', 'sca', 'gca', 'through_balls',
            'pressures','pressure_effective','pressures_def_3rd_pct','pressures_mid_3rd_pct','pressures_att_3rd_pct',
            'touches_def_pen_area_pct','touches_def_3rd_pct','touches_mid_3rd_pct','touches_att_3rd_pct','touches_att_pen_area_pct',
            'passes_ground_pct','passes_low_pct','passes_high_pct',
            'passes_long_pct','passes_medium_pct','passes_short_pct',
            'passes_completed_long_pct','passes_completed_medium_pct','passes_completed_short_pct',
            'passes_into_final_third','passes_into_penalty_area','crosses_into_penalty_area','progressive_passes',
            'progressive_carries', 'carries_into_final_third', 'carries_into_penalty_area',
            'carry_progressive_distance_ratio','passes_progressive_distance_ratio',
            'aerials_won_pct'
            ]    
    
    return df[cols],cols


def summary_player(df):
    
    df = df.groupby(['player_id','name','team_id']).agg({
        'minutes':'sum',
        'shots_total':'sum','assisted_shots':'sum','npxg':'sum','xa':'sum','sca':'sum','gca':'sum','through_balls':'sum',
        'pressures':'sum','pressure_regains':'sum',
        'pressures_att_3rd':'sum','pressures_mid_3rd':'sum','pressures_def_3rd':'sum',
        'touches_def_pen_area':'sum','touches_def_3rd':'sum','touches_mid_3rd':'sum','touches_att_3rd':'sum','touches_att_pen_area':'sum',
        'passes_ground':'sum', 'passes_low':'sum', 'passes_high':'sum',
        'passes_long':'sum','passes_completed_long':'sum','passes_medium':'sum','passes_completed_medium':'sum','passes_short':'sum','passes_completed_short':'sum',
        'passes_into_final_third':'sum','passes_into_penalty_area':'sum','crosses_into_penalty_area':'sum','progressive_passes':'sum',
        'progressive_carries':'sum', 'carries_into_final_third':'sum', 'carries_into_penalty_area':'sum',
        'carry_distance':'sum','carry_progressive_distance':'sum',
        'passes_total_distance':'sum','passes_progressive_distance':'sum',
        'aerials_lost':'sum', 'aerials_won':'sum'
        })
    
    df['pressure_effective'] = df['pressure_regains']/df['pressures']
    df['pressures_def_3rd_pct'] = df['pressures_def_3rd']/df['pressures']
    df['pressures_mid_3rd_pct'] = df['pressures_mid_3rd']/df['pressures']
    df['pressures_att_3rd_pct'] = df['pressures_att_3rd']/df['pressures']
    df['touches'] = df['touches_def_pen_area']+df['touches_def_3rd']+df['touches_mid_3rd']+df['touches_att_3rd']+df['touches_att_pen_area'] 
    df['touches_def_pen_area_pct'] = df['touches_def_pen_area']/df['touches']
    df['touches_def_3rd_pct'] = df['touches_def_3rd']/df['touches']
    df['touches_mid_3rd_pct'] = df['touches_mid_3rd']/df['touches']
    df['touches_att_3rd_pct'] = df['touches_att_3rd']/df['touches']
    df['touches_att_pen_area_pct'] = df['touches_att_pen_area']/df['touches']
    df['passes'] = df['passes_ground']+df['passes_low']+df['passes_high']
    df['passes_ground_pct'] = df['passes_ground']/df['passes']
    df['passes_low_pct'] = df['touches_att_pen_area']/df['passes']
    df['passes_high_pct'] = df['passes_high']/df['passes']
    df['passes_long_pct'] = df['passes_long']/df['passes']
    df['passes_medium_pct'] = df['passes_medium']/df['passes']
    df['passes_short_pct'] = df['passes_short']/df['passes']
    df['passes_completed_long_pct'] = df['passes_completed_long']/df['passes_long']
    df['passes_completed_medium_pct'] = df['passes_completed_medium']/df['passes_medium']
    df['passes_completed_short_pct'] = df['passes_completed_short']/df['passes_short']
    df['carry_progressive_distance_ratio'] = df['carry_progressive_distance']/df['carry_distance']
    df['passes_progressive_distance_ratio'] = df['passes_progressive_distance']/df['passes_total_distance']
    df['aerials'] = df['aerials_lost']+df['aerials_won']
    df['aerials_won_pct'] = df['aerials_won']/df['aerials']
    
    df['shots_total'] = df['shots_total']/df['minutes']
    df['assisted_shots'] = df['assisted_shots']/df['minutes']
    df['npxg'] = df['npxg']/df['minutes']
    df['xa'] = df['xa']/df['minutes']
    df['sca'] = df['sca']/df['minutes']
    df['gca'] = df['gca']/df['minutes']
    df['through_balls'] = df['through_balls']/df['minutes']
    df['pressures'] = df['pressures']/df['minutes']
    df['progressive_carries'] = df['progressive_carries']/df['minutes']
    df['carries_into_final_third'] = df['carries_into_final_third']/df['minutes']
    df['carries_into_penalty_area'] = df['carries_into_penalty_area']/df['minutes']
    
    cols = ['minutes','shots_total', 'assisted_shots', 'npxg', 'xa', 'sca', 'gca', 'through_balls',
            'pressures','pressure_effective','pressures_def_3rd_pct','pressures_mid_3rd_pct','pressures_att_3rd_pct',
            'touches_def_pen_area_pct','touches_def_3rd_pct','touches_mid_3rd_pct','touches_att_3rd_pct','touches_att_pen_area_pct',
            'passes_ground_pct','passes_low_pct','passes_high_pct',
            'passes_long_pct','passes_medium_pct','passes_short_pct',
            'passes_completed_long_pct','passes_completed_medium_pct','passes_completed_short_pct',
            'passes_into_final_third','passes_into_penalty_area','crosses_into_penalty_area','progressive_passes',
            'progressive_carries', 'carries_into_final_third', 'carries_into_penalty_area',
            'carry_progressive_distance_ratio','passes_progressive_distance_ratio',
            'aerials_won_pct'
            ]    
    
    return df[cols],cols




