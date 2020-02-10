#!/usr/bin/env python

from requests import get
from requests.exceptions import RequestException
from contextlib import closing
from bs4 import BeautifulSoup
import re
import copy
import pprint
import statistics
from html import escape
import argparse
import sys

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('-l', action="store_true")
    parser.add_argument('-t', action="store_true")
    parser.add_argument('-p', action="store_true")
    parser.add_argument('-y', action="store_true")
    parser.add_argument('-m', action="store", type=str, help="Match date m/d/y")
    parser.add_argument("url", type=str, help="URL")
    args = parser.parse_args()
    
    url = args.url

    run=""
    db={}
    fails = []
    dups = []
    if args.l:
        run="league"
    if args.t:
        run="team"
    if args.p:
        run="player"
    if args.y:
        run="player_year"
    if args.m:
        run="match"
        match_date = args.m

    match_variables = ['Match_Date', 'League', 
            'Team1', 'Team2', 'Court', 
            'Team1_P1', 'Team1_P2', 'Team2_P1', 'Team2_P2',
            'Win_Team', 'Team1_Games', 'Team2_Games', 'Delta_Pct_Games',
            'Team1_P1_IR', 'Team1_P2_IR', 'Team2_P1_IR', 'Team2_P2_IR', 'Team1_Avg_IR', 'Team2_Avg_IR',
            'Team1_P1_MR', 'Team1_P2_MR', 'Team2_P1_MR', 'Team2_P2_MR', 'Team1_Avg_MR', 'Team2_Avg_MR',
            'Delta_Team_IR', 'Delta_Team_MR']

    if run=='league':
        league_url=url
        league = get(league_url)
        league_html = BeautifulSoup(league.text, "html.parser")
    
        tds = league_html.findAll('td')
        output_name = tds[2].text.replace(" ", "_") + ".tsv"

        #For team in league
        team_links = league_html.findAll('a', {'class':'link'})
        for link in team_links:
            if "teamprofile" in link['href']:
                team_url = "https://www.tennisrecord.com" + link['href']
                team = get(team_url)
                team_html = BeautifulSoup(team.text, "html.parser")
                #For player on team
                player_links = team_html.findAll('a', {'class':'link'})
                for player_link in player_links:
                    if "playername" in player_link['href']:
                        player_url = "https://www.tennisrecord.com" + player_link['href']
                        player = get(player_url)
                        player_html = BeautifulSoup(player.text, "html.parser")
                        year_links = player_html.findAll('a', {'class':'link'})
                        for year_link in year_links:
                            if ("matchhistory" in year_link['href'] and "mt=" not in year_link['href'] and "Current Match History" not in year_link.text):
                                year_link = year_link['href'].replace('<','&lt')
                                player_year_url = "https://www.tennisrecord.com" + year_link
                                db = get_player_year_matches(player_year_url, match_variables, db)
    
    if run=="team":
        team_url=url
        team = get(team_url)
        team_html = BeautifulSoup(team.text, "html.parser")
        
        tds = team_html.findAll('td')
        output_name = tds[3].text.replace(" ", "_") + ".tsv"

        #For player on team
        player_links = team_html.findAll('a', {'class':'link'})
        for player_link in player_links:
            if "playername" in player_link['href']:
                    player_url = "https://www.tennisrecord.com" + player_link['href']
                    player = get(player_url)
                    player_html = BeautifulSoup(player.text, "html.parser")
                    year_links = player_html.findAll('a', {'class':'link'})
                    for year_link in year_links:
                        if ("matchhistory" in year_link['href'] and "mt=" not in year_link['href'] and "Current Match History" not in year_link.text):
                            year_link = year_link['href'].replace('<','&lt')
                            player_year_url = "https://www.tennisrecord.com" + year_link
                            db = get_player_year_matches(player_year_url, match_variables, db)
    
    if run=="player":
        player_url = url
        player = get(player_url)
        player_html = BeautifulSoup(player.text, "html.parser")
        
        tds = player_html.findAll('td')
        output_name = tds[2].text.split("(")[0].strip().replace(" ", "_") + ".tsv"

        year_links = player_html.findAll('a', {'class':'link'})
        for year_link in year_links:
            if ("matchhistory" in year_link['href'] and "mt=" not in year_link['href'] and "Current Match History" not in year_link.text):
                year_link = year_link['href'].replace('<','&lt')
                player_year_url = "https://www.tennisrecord.com" + year_link
                db = get_player_year_matches(player_year_url, match_variables, db)
    
    if run=="player_year":
        player_year_url = url
        player = get(player_year_url)
        player_year_html = BeautifulSoup(player.text, "html.parser")
        
        tds = player_year_html.findAll('td')
        year = re.search(r'year=(\d+)', player_year_url)[1]
        output_name = tds[2].text.split("(")[0].strip().replace(" ", "_") + "_" + str(year) + ".tsv"

        db = get_player_year_matches(player_year_url, match_variables, db)

    if run=="match":
        player_year_url = url

        raw_html = simple_get(player_year_url)
        html = BeautifulSoup(raw_html, 'html.parser')
        
        tds = html.findAll('td')
        output_name = tds[2].text.split("(")[0].strip().replace(" ", "_") + "_" + match_date.replace("/", "-") + ".tsv"
        
        match_div = html.findAll('div', {'class':'container496'})
        for match_html in match_div:
            match_list = match_html.text.rstrip().split('\n')
            match_list = (x.rstrip() for x in match_list)
            match_list = [x for x in match_list if x]
            
            match={}

            if match_list[0]==match_date:
                if len(match_list)==10:
                    try:
                        match = get_match(html, match_html, match_variables, 'S')
                    except:
                        print("Match failed")
                        fails.append(match_list)
                        fails.append(url)
                        pass
                elif len(match_list)==11:
                    try:
                        match = get_match(html, match_html, match_variables, 'D')
                    except:
                        print("Match failed")
                        fails.append(match_list)
                        fails.append(url)
                        pass
                if check_dups(match,db)==False:
                    db[len(db)+1] = match
                else:
                    print("Duplicate match found")
                    dups.append(match_list)
                    dups.append(player_year_url)

    print("\n" + str(len(db)) + " match(es) in database")
    
    #Write output file
    if len(db)>0:
        with open(output_name, "w") as f:
            print('\t'.join(match_variables), file = f)
            for k,v in db.items():
                vals=list(db[k].values())
                vals = ['None' if v is None else v for v in vals]
                vals = [str(x) for x in vals]
                print('\t'.join(vals), file = f)
        print("Output written to: " + output_name)
    else:
        print("No matches written to file")

    if len(fails)>0:
        fail_count = int(len(fails)/2)
        print("Failed match count: " + str(fail_count))
        with open("fails.tsv", "w") as f:
            for item in fails:
                print(item, file=f)
    else:
        print("No failed matches")
    
    if len(dups)>0:
        dup_count = int(len(dups)/2)
        print("Duplicate match count: " + str(dup_count))
        with open("dups.tsv", "w") as f:
            for item in dups:
                print(item, file=f)
    else:
        print("No duplicates found")


def simple_get(url):
    """
    Attempts to get the content at `url` by making an HTTP GET request.
    If the content-type of response is some kind of HTML/XML, return the
    text content, otherwise return None.
    """
    try:
        with closing(get(url, stream=True)) as resp:
            if is_good_response(resp):
                return resp.content
            else:
                return None

    except RequestException as e:
        log_error('Error during requests to {0} : {1}'.format(url, str(e)))
        return None


def is_good_response(resp):
    """
    Returns True if the response seems to be HTML, False otherwise.
    """
    content_type = resp.headers['Content-Type'].lower()
    return (resp.status_code == 200 
            and content_type is not None 
            and content_type.find('html') > -1)


def log_error(e):
    """
    It is always a good idea to log errors. 
    This function just prints them, but you can
    make it do anything.
    """
    print(e)

def get_player_year_matches(url, match_variables, db):
    """
    Pull match variables for a player year
    """
    raw_html = simple_get(url)
    html = BeautifulSoup(raw_html, 'html.parser')

    match_div = html.findAll('div', {'class':'container496'})
    for match_html in match_div:
        match_list = match_html.text.rstrip().split('\n')
        match_list = (x.rstrip() for x in match_list)
        match_list = [x for x in match_list if x]
   
        if len(match_list)==10:
            try:
                match = get_match(html, match_html, match_variables, 'S')
            except:
                print("Match failed")
                pass
        elif len(match_list)==11:
            try:
                match = get_match(html, match_html, match_variables, 'D')
            except:
                print("Match failed")
                pass
        try:
            if check_dups(match,db)==False:
                db[len(db)+1] = match
        except:
            pass

    return(db)

def get_match(html, match_html, match_variables, match_format):
    match = dict.fromkeys(match_variables)
    
    #Parse match data
    match_list = match_html.text.rstrip().split('\n')
    match_list = (x.rstrip() for x in match_list)
    match_list = [x for x in match_list if x]
 
    print(match_list)

    #Get root player name
    name_links=html.findAll('a', {'class':'link'})

    #Get basic match data
    match['Match_Date'] = match_list[0]
    match['Court'] = match_list[1]
    match['League'] = match_list[2]
    
    #Get team and player names
    match = get_team_player(match_html, name_links, match_list, match_format, match)

    #Get score
    match = get_score(match_list, match, match_format)

    #Grab link to match detail page and grab player IRs
    links=match_html.findAll('a', {'class':'link'})
    for link in links:
        if "matchresults" in link['href']:
            match_url = "https://www.tennisrecord.com" + link['href']            
            match = get_match_IR(match_url, match, match_format)

    #Get player MRs
    match = get_match_MR(match_html, match_list, match_format, match)
    return(match)

def get_match_MR(match_html, match_list, match_format, match):
    #Get root player MR
    if match_list[4]=="W":
        if match_format=="S":
            match["Team1_P1_MR"] = match_list[8].replace("Match: ","")
        if match_format=="D":
            match["Team1_P1_MR"] = match_list[9].replace("Match: ","")
    if match_list[4]=="L":
        if match_format=="S":
            match["Team2_P1_MR"] = match_list[8].replace("Match: ","")
        if match_format=="D":
            match["Team2_P1_MR"] = match_list[9].replace("Match: ","")
  
    #Grab link to player match history page and grab player MR
    links=match_html.findAll('a', {'class':'link'})
    for link in links:
        if "matchhistory" in link['href']:
            player_url = "https://www.tennisrecord.com" + link['href']            
            player_raw_html = simple_get(player_url)
            player_html = BeautifulSoup(player_raw_html, 'html.parser')
            match_div = player_html.findAll('div', {'class':'container496'})
            for m in match_div:
                match_list2 = m.text.rstrip().split('\n')
                match_list2 = (x.rstrip() for x in match_list2)
                match_list2 = [x for x in match_list2 if x]
                
                #Filter match by date, court, league, and teams
                if (match['Match_Date']==match_list2[0] and 
                    match['Court']==match_list2[1] and
                    match['League']==match_list[2] and
                    ((match['Team1']==match_list[3] and match['Team2']==match_list[5]) or
                    (match['Team1']==match_list[5] and match['Team2']==match_list[3]))):
                        #Get root player name
                        name_links=player_html.findAll('a', {'class':'link'})
                        root_player = name_links[1].text.strip()
                        if match_format=="S":
                            mr = match_list2[8].replace("Match: ","")
                        if match_format=="D":
                            mr = match_list2[9].replace("Match: ","")
                        for x in ['Team1_P1','Team1_P2','Team2_P1','Team2_P2']:
                            if match[x]==root_player:
                                 match[x+'_MR'] = mr
   
    if match_format=="S":
        try:
            match['Team1_Avg_MR'] = float(match['Team1_P1_MR'])
            match['Team2_Avg_MR'] = float(match['Team2_P1_MR'])
            match['Delta_Team_MR'] = match['Team1_Avg_MR'] - match['Team2_Avg_MR']
        except (KeyboardInterrupt,  SystemExit):
            raise
        except:
            pass
    if match_format=="D":
        try:
            match['Team1_Avg_MR'] = statistics.mean([float(match['Team1_P1_MR']), float(match['Team1_P2_MR'])])
            match['Team2_Avg_MR'] = statistics.mean([float(match['Team2_P1_MR']), float(match['Team2_P2_MR'])])
            match['Delta_Team_MR'] = match['Team1_Avg_MR'] - match['Team2_Avg_MR']    
        except (KeyboardInterrupt,  SystemExit):
            raise
        except:
            pass
    return(match)

def get_team_player(match_html, name_links, match_list, match_format, match):
    names = re.findall(r'playername=([^&]+)', str(match_html))
    
    #Winners assigned to team 1 regardless of root player
    if match_list[4]=="W":
        #Get team names
        match['Team1'] = match_list[3]
        match['Team2'] = match_list[5]
        match['Win_Team'] = match_list[3]
        
        match['Team1_P1'] = name_links[1].text.strip()
        if match_format=="S":
            if match_list[7]=="Default":
                match['Team2_P1'] = "Default"
            else:
                match['Team2_P1'] = names[0]
        if match_format=="D":
            if match_list[8]=="Default":
                match['Team2_P1'] = "Default"
                match['Team2_P2']="Default"
            else:
                match['Team1_P2'] = names[0]
                match['Team2_P1'] = names[1]
                match['Team2_P2'] = names[2]

    if match_list[4]=="L":
        #Get team names
        match['Team1'] = match_list[5]
        match['Team2'] = match_list[3]
        match['Win_Team'] = match_list[5]
   
        match['Team2_P1'] = name_links[1].text.strip()
        if match_format=="S":
            match['Team1_P1'] = names[0]
        if match_format=="D":
            match['Team2_P2'] = names[0]
            match['Team1_P1'] = names[1]
            match['Team1_P2'] = names[2]
    
    return(match)

def get_score(match_list, match, match_format):

    #Break down score into games
    score1, score2, sets = 0,0,[]
    if match_format=='S':
        sets = match_list[6].split(', ')
    if match_format=='D':
        sets = match_list[7].split(', ')
    for set_score in sets:
        score1 += int(set_score.split('-')[0])
        score2 += int(set_score.split('-')[1])
    
    if len(sets)<=2:
        match['Team1_Games'] = max(score1, score2)
        match['Team2_Games'] = min(score1, score2)
    if len(sets)==3:   
        tiebreak = sets[2].split('-')
        if tiebreak[0]=="1":
            match['Team1_Games'] = score1
            match['Team2_Games'] = score2
        if tiebreak[1]=="1":
            match['Team1_Games'] = score2
            match['Team2_Games'] = score1
        
    match['Delta_Pct_Games']=(match['Team1_Games']/(match['Team1_Games']+ match['Team2_Games']))-(match['Team2_Games']/(match['Team1_Games']+ match['Team2_Games']))

    return(match)

def get_match_IR(match_url, match, match_format):
    raw_html = simple_get(match_url)
    html = BeautifulSoup(raw_html, 'html.parser')

    match_div = html.findAll('div', {'class':'container496'})
    match_index={}
    if len(match_div)==5:
        match_index= {'D1':2, 'D2':3, 'D3':4}
    if len(match_div)==7:
        match_index= {'S1':2, 'S2':3, 'D1':4, 'D2':5, 'D3':6}
    
    name_list=[]
    if match_format=='S':
        name_list = [match['Team1_P1'], match['Team2_P1']]
    if match_format=='D':
        name_list = [match['Team1_P1'], match['Team1_P2'], match['Team2_P1'], match['Team2_P2']]
    
    try:
        names_IR = re.findall(r"(?=(" + '|'.join(name_list) + r"|\(\d\.\d+\)" + r"|\(-----\)" + r"))", str(match_div[match_index[match['Court'][0:2]]]))
        if match_format=='S':
            del names_IR[5]
            del names_IR[0]
            names_IR[2], names_IR[3] = names_IR[3], names_IR[2]
        if match_format=='D':
            del names_IR[11]
            del names_IR[8]
            del names_IR[3]
            del names_IR[0]
            names_IR[4], names_IR[5], names_IR[6], names_IR[7] = names_IR[5], names_IR[4], names_IR[7], names_IR[6]
        
        for x in ['Team1_P1','Team1_P2','Team2_P1','Team2_P2']:
            for index,y in enumerate(names_IR):
                if match[x]==y:
                    match[x+'_IR'] = names_IR[index+1].replace('(','').replace(')','')
        
        if match_format=="S":
            try:
                match['Team1_Avg_IR'] = float(match['Team1_P1_IR'])
                match['Team2_Avg_IR'] = float(match['Team2_P1_IR'])
                match['Delta_Team_IR'] = match['Team1_Avg_IR'] - match['Team2_Avg_IR']    
            except (KeyboardInterrupt,  SystemExit):
                raise
            except:
                pass
        if match_format=="D":
            try:
                match['Team1_Avg_IR'] = statistics.mean([float(match['Team1_P1_IR']), float(match['Team1_P2_IR'])])
                match['Team2_Avg_IR'] = statistics.mean([float(match['Team2_P1_IR']), float(match['Team2_P2_IR'])])
                match['Delta_Team_IR'] = match['Team1_Avg_IR'] - match['Team2_Avg_IR']    
            except (KeyboardInterrupt,  SystemExit):
                raise
            except:
                pass
    
    except (KeyboardInterrupt,  SystemExit):
        raise
    except:
        pass
    return(match)      



def check_dups(match, db):
    """
    Check if there is a duplicate row in dict already (excluding price and url)
    """

    if len(db)>0:
        tmp_match = copy.deepcopy(match)
        for key, value in match.items():
            if ("Team1_P" in key or "Team2_P" in key):
                del tmp_match[key]

        tmp_db = copy.deepcopy(db)
        for index,string_dict in db.items():
            for key, value in string_dict.items():
                if ("Team1_P" in key or "Team2_P" in key):
                    del tmp_db[index][key]
                
        
        if tmp_match in tmp_db.values():
            return True
        else:
            return False
    else:
        return False

if __name__ == "__main__":
    main()
