#!/usr/bin/env python

from requests import get
from requests.exceptions import RequestException
from contextlib import closing
from bs4 import BeautifulSoup
import re
import copy
import pprint

def main():
    run='test'
    url = 'https://www.tennis-warehouse.com/stringcontent.html'
    base_url = 'https://www.tennis-warehouse.com'

    match_variables = ['Match_Date', 'League', 
            'Team1', 'Team2', 'Court', 
            'Team1_P1', 'Team1_P2', 'Team2_P1', 'Team2_P2',
            'Win_Team', 'Win_Games', 'Lose_Games', 'Delta_Pct_Games',
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
"""
Press ENTER or type command to continue
<div class="container496">
<table style="margin:auto; width:100%; font-size:12px;">
<tr style="height:50px; color:#7a7a7a; background-color:#f9f9f9; border-bottom:1px solid #ddd;">
<th class="padding10" style="text-align:left;">1/11/2020</th>
<th style="text-align:center;">S1</th>
<th class="padding10" style="text-align:right;"><a class="link" href="/adult/league.aspx?flightname=4.0 Women&amp;year=2020&amp;s=234">Adult 18+<br/>4.0</a></th>
</tr>
<tr style="border-bottom:1px solid #ddd;">
<td padding10"="" style="text-align:left; class="><a class="link" href="/adult/teamprofile.aspx?teamname=McMullen Hansen&amp;year=2020">McMullen Hansen<br/>Florida</a></td>
<td style="text-align:center;">W</td>
<td padding10"="" style="text-align:right; class="><a class="link" href="/adult/teamprofile.aspx?teamname=Vinoy Sparks&amp;year=2020">Vinoy Sparks<br/>Florida</a></td>
</tr>
<tr style="border-bottom:1px solid #ddd;">
<td class="padding10" style="text-align:left;">
</td>
<td style="text-align:center;"><a class="link" href="/adult/matchresults.aspx?year=2020&amp;mid=50467">7-6, 1-6, 1-0</a></td>
<td class="padding10" style="text-align:right;">
<a class="link" href="/adult/matchhistory.aspx?playername=Truc Dang&amp;year=2020">Truc Dang</a> (3.82)
                                        
                                </td>
</tr>
<tr>
<td class="padding10" style="text-align:left;">Match: 3.75</td>
<td></td>
<td class="padding10" style="text-align:right;">Rating: 3.84</td>
</tr>
</table>
</div>
None
"""


"""
Press ENTER or type command to continue



1/11/2020
S1
Adult 18+4.0


McMullen HansenFlorida
W
Vinoy SparksFlorida




7-6, 1-6, 1-0

Truc Dang (3.82)
                                        
                                


Match: 3.75

Rating: 3.84



None
"""

def get_matches(url, match_variables):
    """
    Pull match variables for a player year
    """
    raw_html = simple_get(url)
    html = BeautifulSoup(raw_html, 'html.parser')

    match_div = html.findAll('div', {'class':'container496'})
    match_html = match_div[1]
    match = dict.fromkeys(match_variables)
    
    match_list = match_html.text.rstrip().split('\n')
    match_list = (x.rstrip() for x in match_list)
    match_list = [x for x in match_list if x]
   
    #get player name
    name_links=html.findAll('a', {'class':'link'})
    
    match['Match_Date'] = match_list[0]
    match['Court'] = match_list[1]
    match['League'] = match_list[2]
    print(len(match_list))
    if match_list[4]=="W":
        match['Team1'] = match_list[3]
        match['Team2'] = match_list[5]
        match['Win_Team'] = match_list[3]
        match['Team1_P1'] = name_links[1].text
        match['Team2_P1'] = re.match(r'.*(?=\s\()', match_list[7])[0]
        match['Team1_P1_MR'] = re.match(r'Match:\s(.*)', match_list[8])[1]
    elif match_list[4]=="L":
        match['Team1'] = match_list[5]
        match['Team2'] = match_list[3]
        match['Win_Team'] = match_list[5]
        match['Team2_P1'] = name_links[1].text
        match['Team1_P1'] = re.match(r'.*(?=\s\()', match_list[7])[0]
        match['Team2_P1_MR'] = re.match(r'Match:\s(.*)', match_list[8])[1]

    #Break down score into games
    score1, score2 = 0,0
    for set_score in match_list[6].split(', '):
        score1 += int(set_score.split('-')[0])
        score2 += int(set_score.split('-')[1])
    
    match['Win_Games'] = max(score1, score2)
    match['Lose_Games'] = min(score1, score2)
    match['Delta_Pct_Games'] = round(abs((score1/(score1+score2))-(score2/(score1+score2))), 4)

    pprint.pprint(match)
#    for table in match_div:
        #Single match level



def get_vars(base_url, url, review_vars):
    """
    Pull review variabes from review webpage table.
    """
    raw_html = simple_get(url)
    html = BeautifulSoup(raw_html, 'html.parser')
    review = dict.fromkeys(review_vars)
  
    #NAME
    review['Name'] = re.sub(r" String.*?Review" , "",html.find('h1').text)

    #PRICE
    if html.find('div', {'id':'pricebox'}):
        review['Price'] = html.find('div', {'id':'pricebox'}).find('h1').text
    if html.find('span', {'class':'price'}):
        review['Price'] = html.find('span', {'class':'price'}).text.replace('Price: ', '')
    
    #REVIEW VARIABLES
    if html.find('div', {'class':'score_box'}):
        for tr in html.find('div', {'class':'score_box'}).select('tr'):
            fields = tr.text.strip().split('\n')
            if fields[0] in review_vars:
                review[fields[0]] = fields[1]
            if fields[0] in ['Touch','Feel']:
                review['Touch/Feel'] = fields[1]
    if html.find('div', {'class':'review_scores'}):
        for tr in html.find('div', {'class':'review_scores'}).select('tr'):
            fields = tr.text.strip().split('\n')
            if fields[0] in review_vars:
                review[fields[0]] = fields[1]
            if fields[0] in ['Touch','Feel']:
                review['Touch/Feel'] = fields[1]

    #URL
    if html.find('div', {'id':'pricebox'}):
        review['URL'] = base_url + html.find('div', {'id':'pricebox'}).find('a')['href']
    if html.find('div', {'class':'review_btns'}):
        review['URL'] = html.find('a', {'class':'button'})['href']
    
    return(review)

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
