#!/usr/bin/env python

from requests import get
from requests.exceptions import RequestException
from contextlib import closing
from bs4 import BeautifulSoup
import re
import copy
import pprint
import statistics

def main():
    run='test'
    url = 'https://www.tennis-warehouse.com/stringcontent.html'
    base_url = 'https://www.tennis-warehouse.com'

    match_variables = ['Match_Date', 'League', 
            'Team1', 'Team2', 'Court', 
            'Team1_P1', 'Team1_P2', 'Team2_P1', 'Team2_P2',
            'Win_Team', 'Team1_Games', 'Team2_Games', 'Delta_Pct_Games',
            'Team1_P1_IR', 'Team1_P2_IR', 'Team2_P1_IR', 'Team2_P2_IR', 'Team1_Avg_IR', 'Team2_Avg_IR',
            'Team1_P1_MR', 'Team1_P2_MR', 'Team2_P1_MR', 'Team2_P2_MR', 'Team1_Avg_MR', 'Team2_Avg_MR',
            'Delta_Team_IR', 'Delta_Team_MR']


    if run=='test':
        url="https://www.tennisrecord.com/adult/matchhistory.aspx?year=2020&playername=Elizabeth%20Gerlach&lt=0"
        matches = get_matches(url, match_variables)
        print(matches)


    if run=='all':
        db = {}
        fail = []
        index = 1
        req = get(url)
        soup = BeautifulSoup(req.text, "html.parser")
        brand_links = soup.find_all('ul', {'class':'lnav_section'})
        for bl in brand_links:
            for link in bl.select('li'):
                if 'String' in link.text.strip().split()[-1]:
                    url2 = base_url + link.find('a')['href']
                    brand = get(url2)
                    soup_brand = BeautifulSoup(brand.text, "html.parser")
                    review_links = soup_brand.find_all("a",{'class':'review'})
                    for rl in review_links:
                        url3 = base_url + rl['href']
                        print(url3)
                        try:
                            review = get_vars(base_url, url3, variables)
                            if not check_dups(review, db):
                                db[index] = review
                                index = index + 1
                            else:
                                pass
                        except:
                            fail.append(url3)
                            pass
        
        
        if len(fail)>0:
            print("\nFAILED URLS:")
            for url in fail:
                print(url)
        else:
            print("\nNO FAILED URLS")

        with open("strings.tsv", "w") as f:
            print('\t'.join(variables), file = f)
            for k,v in db.items():
                vals=list(db[k].values())
                vals = ['None' if v is None else v for v in vals]
                print('\t'.join(vals), file = f)

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

def get_matches(url, match_variables):
    """
    Pull match variables for a player year
    """
    raw_html = simple_get(url)
    html = BeautifulSoup(raw_html, 'html.parser')

    match_div = html.findAll('div', {'class':'container496'})
    match_html = match_div[1]
    
    match_list = match_html.text.rstrip().split('\n')
    match_list = (x.rstrip() for x in match_list)
    match_list = [x for x in match_list if x]
   
    if len(match_list)==10:
        match = get_match(html, match_html, match_variables, 'S')
    elif len(match_list)==11:
        match = get_match(html, match_html, match_variables, 'D')

def get_match(html, match_html, match_variables, match_format):
    match = dict.fromkeys(match_variables)

    #Parse match data
    match_list = match_html.text.rstrip().split('\n')
    match_list = (x.rstrip() for x in match_list)
    match_list = [x for x in match_list if x]
    
    #Get root player name
    name_links=html.findAll('a', {'class':'link'})

    #Get basic match data
    match['Match_Date'] = match_list[0]
    match['Court'] = match_list[1]
    match['League'] = match_list[2]
    
    #Get team and player names
    match = get_team_player(name_links, match_list, match_format, match)

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

    pprint.pprint(match)
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
        match['Team1_Avg_MR'] = float(match['Team1_P1_MR'])
        match['Team2_Avg_MR'] = float(match['Team2_P1_MR'])
        match['Delta_Team_MR'] = match['Team1_Avg_MR'] - match['Team2_Avg_MR']    
    if match_format=="D":
        match['Team1_Avg_MR'] = statistics.mean([float(match['Team1_P1_MR']), float(match['Team1_P2_MR'])])
        match['Team2_Avg_MR'] = statistics.mean([float(match['Team2_P1_MR']), float(match['Team2_P2_MR'])])
        match['Delta_Team_MR'] = match['Team1_Avg_MR'] - match['Team2_Avg_MR']    


    return(match)

def get_team_player(name_links, match_list, match_format, match):
    #Winners assigned to team 1 regardless of root player
    if match_list[4]=="W":
        #Get team names
        match['Team1'] = match_list[3]
        match['Team2'] = match_list[5]
        match['Win_Team'] = match_list[3]

        #Get player names
        match['Team1_P1'] = name_links[1].text.strip()
        if match_format=="S":
            match['Team2_P1'] = re.match(r'.*(?=\s\()', match_list[7])[0]
        if match_format=="D":
            match['Team1_P2'] = re.split('\(|\)',match_list[6])[0].strip()
            match['Team2_P1'] = re.split('\(|\)',match_list[8])[0].strip()
            match['Team2_P2'] = re.split('\(|\)',match_list[8])[2].strip()
    
    if match_list[4]=="L":
        #Get team names
        match['Team1'] = match_list[5]
        match['Team2'] = match_list[3]
        match['Win_Team'] = match_list[5]
   
        match['Team2_P1'] = name_links[1].text.strip()
        #Get player names
        if match_format=="S":
            match['Team1_P1'] = re.match(r'.*(?=\s\()', match_list[7])[0]
        if match_format=="D":
            match['Team2_P2'] = re.match(r'.*(?=\s\()', match_list[6])[0].strip()
            match['Team1_P1'] = re.split('\(|\)',match_list[8])[0].strip()
            match['Team1_P2'] = re.split('\(|\)',match_list[8])[2].strip()

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
    
    if len(sets)==2:
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
        
    match['Delta_Pct_Games'] = round(abs((score1/(score1+score2))-(score2/(score1+score2))), 4)

    return(match)

def get_match_IR(match_url, match, match_format):
    raw_html = simple_get(match_url)
    html = BeautifulSoup(raw_html, 'html.parser')

    match_div = html.findAll('div', {'class':'container496'})
    match_index= {'S1':2, 'S2':3, 'D1':4, 'D2':5, 'D3':6}
    
    name_list=[]
    if match_format=='S':
        name_list = [match['Team1_P1'], match['Team2_P1']]
    if match_format=='D':
        name_list = [match['Team1_P1'], match['Team1_P2'], match['Team2_P1'], match['Team2_P2']]
    
    names_IR = list(dict.fromkeys(re.findall(r"(?=(" + '|'.join(name_list) + r"|\(\d\.\d+\)" + r"))", str(match_div[match_index[match['Court']]]))))
    
    if match_format=='S':
        names_IR[2], names_IR[3] = names_IR[3], names_IR[2]
    if match_format=='D':
        names_IR[4], names_IR[5], names_IR[6], names_IR[7] = names_IR[5], names_IR[4], names_IR[7], names_IR[6]

    for x in ['Team1_P1','Team1_P2','Team2_P1','Team2_P2']:
        for index,y in enumerate(names_IR):
            if match[x]==y:
                match[x+'_IR'] = names_IR[index+1].replace('(','').replace(')','')
    
    if match_format=="S":
        match['Team1_Avg_IR'] = float(match['Team1_P1_IR'])
        match['Team2_Avg_IR'] = float(match['Team2_P1_IR'])
        match['Delta_Team_IR'] = match['Team1_Avg_IR'] - match['Team2_Avg_IR']    
    if match_format=="D":
        match['Team1_Avg_IR'] = statistics.mean([float(match['Team1_P1_IR']), float(match['Team1_P2_IR'])])
        match['Team2_Avg_IR'] = statistics.mean([float(match['Team2_P1_IR']), float(match['Team2_P2_IR'])])
        match['Delta_Team_IR'] = match['Team1_Avg_IR'] - match['Team2_Avg_IR']    

    return(match)      



def check_dups(review, db):
    """
    Check if there is a duplicate row in dict already (excluding price and url)
    """

    if len(db)>0:
        tmp_review = copy.deepcopy(review)
        del tmp_review['Price']
        del tmp_review['URL']

        tmp_db = copy.deepcopy(db)
        for index,string_dict in tmp_db.items():
            del string_dict['Price']
            del string_dict['URL']
        
        if tmp_review in tmp_db.values():
            return True
        else:
            return False
    else:
        return False

if __name__ == "__main__":
    main()
