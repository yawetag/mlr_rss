import discord
import pandas as pd
import datetime
import re
import requests
import time
from user_config import *

API_URL = 'https://www.rslashfakebaseball.com/api/players'
SHEET = '1mwwPvV8FTXpjoUC4M11ttUydyLnBl2CKbwnufrtCqy0'
TAB = 'Player%20List'

def mlr_discord():
    '''Gets Discord snowflake numbers for MLR players.'''
    response = requests.get(API_URL)
    raw_data = response.json()
    discord_ids = {item['playerName']:item['discordID'] for item in raw_data}
    
    return discord_ids

def mlr_players():
    '''Gets MLR team for MLR players.'''
    response = requests.get(API_URL)
    raw_data = response.json()
    mlr_teams = {item['playerName']:item['Team'] for item in raw_data}
    
    return mlr_teams

def milr_players():
    '''Gets MiLR team for MLR players.'''
    url = f'https://docs.google.com/spreadsheets/d/{SHEET}/gviz/tq?tqx=out:csv&sheet={TAB}'
    milr_teams = pd.read_csv(url)
    milr_teams = milr_teams[['Name', 'MiLR Team']]
    milr_teams = milr_teams.set_index('Name').to_dict()['MiLR Team']
    
    return milr_teams

def parse_comments(snowflakes, mlr, milr):
    '''Goes through each new comment and checks if it needs to be posted.'''
    for comment in reddit.subreddit('fakebaseball').stream.comments(skip_existing = True):

        # Go through each of the rss_feeds and see if the comment belongs
        for r in rss_feeds:
            if r['search'].lower() in comment.link_title.lower():

                # If that particular team does not want the results post with the flavor text, skip it
                if not r['results'] and comment.author == 'FakeBaseball_Umpire' and 'Pitch:' in comment.body and 'Swing:' in comment.body and 'Diff:' in comment.body:
                    continue

                # Otherwise, send the comment in an embed
                embed = discord.Embed(title = comment.link_title, url = comment.link_url, description = comment.body, color = discord.Color(value = int(r['hexcode'], 16)))
                embed.set_author(name = comment.author, url = f'https://www.reddit.com/user/{comment.author}/', icon_url = 'https://cdn.discordapp.com/attachments/734950735418228756/911121370207911957/reddit.png')
                embed.set_thumbnail(url = comment.author.icon_img)
                embed.set_footer(text = f'Comment posted to r/{comment.subreddit} at {datetime.datetime.fromtimestamp(comment.created_utc)} Eastern')
                image_urls = re.findall(r'(?:http\:|https\:)?\/\/.*\.(?:png|jpg|jpeg|gif|mp4)', comment.body)

                if len(image_urls) > 0:
                    embed.set_image(url=image_urls[0])

                # If the post is a result, then set atbat_text to blank, so we don't ping the batter again
                if comment.author == 'FakeBaseball_Umpire' and 'Pitch:' in comment.body and 'Swing:' in comment.body and 'Diff:' in comment.body:
                    atbat_text = ''
                
                # Otherwise, if the feed wants to ping the current batter, do so
                elif r['ping']:
                    txt = comment.body
                    curr_batter = txt[txt.find('[')+1:txt.find('](/u/')]

                    # if curr_batter matches 
                    try:
                        if curr_batter not in ping_exclude and mlr[curr_batter] == r['abbrev'] or milr[curr_batter] == r['abbrev']:
                            snowflake = snowflakes[curr_batter]
                            atbat_text = f'<@{snowflake}> '
                        else:                                   # If not, just post the batter's name
                            atbat_text = f'{curr_batter} '
                        atbat_text += f'is up! The timer ends <t:{int(comment.created_utc + (12 * 60 * 60))}:R> (<t:{int(comment.created_utc + (12 * 60 * 60))}:F> in your local time).'

                    # If curr_batter doesn't match any of the users, just leave it blank
                    except:
                        atbat_text = ''

                # If the team doesn't want to show at-bat text, just leave it blank
                else:
                    atbat_text = ''

                # Send the webhook
                r['webhook'].send(atbat_text, embed=embed)
    
    # Pause to allow other leagues a chance
    time.sleep(0.1)