"""
This sample demonstrates a simple skill built with the Amazon Alexa Skills Kit.
The Intent Schema, Custom Slots, and Sample Utterances for this skill, as well
as testing instructions are located at http://amzn.to/1LzFrj6

For additional samples, visit the Alexa Skills Kit Getting Started guide at
http://amzn.to/1LGWsLG
"""

from __future__ import print_function
import subprocess
import API_Key
import json
import boto3
from botocore.exceptions import ClientError
import string
import requests
from bs4 import BeautifulSoup

TABLE_NAME = 'RocketLeagueUserMapping'
region = 'us-east-1'
# Mapping for spelling out character names
letter_lookup = {'1' : '1',
                 '2' : '2',
                 '3' : '3',
                 '4' : '4',
                 '5' : '5',
                 '6' : '6',
                 '7' : '7',
                 '8' : '8',
                 '9' : '9',
                 '0' : '0',
                'one' : '1',
                'two': '2',
                'three' : '3',
                'four' : '4',
                'five' : '5',
                'six' : '6',
                'seven' : '7',
                'eight' : '8',
                'nine' : '9',
                'zero' : '0',
                'space' : ' ',
                'underscore' : '_' ,
                'dash' : '-',
                'dot' : '.',
                'period' : '.',
                'colon' : ':',
                'semicolon' : ';',
                'open bracket' : '[',
                'close bracket' : ']',
                'closed bracket' : ']',
                'open parenthesis' : '(',
                'close parenthesis' : ')',
                'closed parenthesis' : ')' ,
                'back slash' : '/',
                'backslash' : '/',
                'forward slash' : '\\',
                'quotation mark' : '"',
                'bar' : '|',
                'question mark' : '?',
                'exclamation point' : '!',
                'at sign' : '@',
                'equals sign' : '=',
                'carrot' : '^' ,
                'star' : '*',
                'plus sign' : '+',
                'comma' : ',' ,
                'left brace' : '{',
                'right brace' : '}',
                'squiggle' : '~',
                'tilde' : '~',
                'dollar sign' : '$',
                'percent sign' : '%',
                'a' : 'a',
                'b' : 'b',
                'c' : 'c',
                'd' : 'd',
                'e' : 'e',
                'f' : 'f',
                'g' : 'g',
                'h' : 'h',
                'i' : 'i',
                'j' : 'j',
                'k' : 'k',
                'l' : 'l',
                'm' : 'm',
                'n' : 'n',
                'o' : 'o',
                'p' : 'p',
                'q' : 'q',
                'r' : 'r',
                's' : 's',
                't' : 't',
                'u' : 'u',
                'v' : 'v',
                'w' : 'w',
                'x' : 'x',
                'y' : 'y',
                'z' : 'z'
    }
# Ordered list in which to examine screen name character slots (up to twenty)
characterList = ['charOne', 'charTwo', 'charThree', 'charFour', 'charFive', 'charSix', 'charSeven', 'charEight', 'charNine', 'charTen', 
    'charEleven', 'charTwelve', 'charThirteen', 'charFourteen', 'charFifteen', 'charSixteen', 'charSeventeen', 'charEighteen', 
    'charNineteen', 'charTwenty']



# --------------- Helpers that build all of the responses ----------------------

def build_speechlet_response(title, output, reprompt_text, should_end_session):
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'card': {
            'type': 'Simple',
            'title': title,
            'content': output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }

def buildSpeechletResponseWithDirectiveNoIntent(intent):
    print("BUILDING SPEECHLET RESPONSE WITH NO INTENT")
    return {
      "outputSpeech" : None,
      "card" : None,
      "directives" : [ {
        "type" : "Dialog.Delegate"
      } ],
      "reprompt" : None,
      "shouldEndSession" : False
    }


def build_response(session_attributes, speechlet_response):
    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }


# --------------- Functions that control the skill's behavior ------------------

def get_welcome_response(session):
    """ If we wanted to initialize the session to have some attributes we could
    add those here
    """

    session_attributes = {}
    card_title = "Welcome"
    speech_output = "Welcome to the Rocket League lookup app. " \
                    "Please add a player or lookup a player."
    # If the user either does not reply to the welcome message or says something
    # that is not understood, they will be prompted again with this text.
    reprompt_text = "I'm sorry, I didn't catch that. Please add, lookup, or remove a player." 

    alexa_user_id = session['user']['userId']
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(TABLE_NAME)
    dbLookupResult = table.get_item(
            Key={'AlexaUserID' : alexa_user_id}
        )

    # Check to see if Alexa user has been created in DB
    if 'Item' not in [item for item in dbLookupResult]:
        speech_output = "Welcome to the Rocket League lookup app. There are " \
            "not currently any players. Please add a player with the phrase, 'add player'," \
            " followed by your first name"
        reprompt_text = "Sorry, I didn't catch that. Please add a new player."

    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def handle_session_end_request():
    card_title = "Session Ended"
    speech_output = ""
    # Setting this to true ends the session and exits the skill.
    should_end_session = True
    return build_response({}, build_speechlet_response(
        card_title, speech_output, None, should_end_session))

def player_not_found(player_id, session_attributes, card_title, should_end_session):
    """ Helper function to generate an Alexa response when the player was not found """
    return build_response(session_attributes, build_speechlet_response(
                    card_title, "Player "+player_id+" not found in skill lookup. Please add the player to my database with the phrase 'Alexa, add player'", "Please try with another player", should_end_session))

def create_player_id_attributes(player_id):
    return {"playerID": player_id}

def parse_api_call(player_id, json_result):
    """ Helper function to parse the resulting API call for a basic player lookup """
    print("Results for player " + player_id + " are:"+'\n'+json_result)
    # Check to see if player exists in database
    if 'code' in [keys for keys in json_result]:
        if json_result['code'] == 404:
            return "Player does not exist in Rocket League API database"
        elif json_result['code'] == 401:
            return "API key is invalid. Unauthorized request."
        elif json_result['code'] == 400:
            return "Invalid request. Please try removing the player and adding them again."
        elif json_result['code'] >= 500:
            return "Rocket League API is not currently accessible. Please try again later."

    # Find the current season
    mostRecentSeason = [season for season in json_result['rankedSeasons']][0]
    json_season = json_result['rankedSeasons'][mostRecentSeason]
    print(json_result['rankedSeasons'][mostRecentSeason])
    numPlaylists = len([playlist for playlist in json_season])
    speech_output = str(player_id) + " has "
    if numPlaylists < 1:
        speech_output = "no ranked match statistics available"
    elif numPlaylists == 1:
        if json_season['10'] != None:
            speech_output += str(json_season['10']['rankPoints']) + " points in duel"
        if json_season['11'] != None:
            speech_output += str(json_season['11']['rankPoints']) + " points in doubles"
        if json_season['12'] != None:
            speech_output += str(json_season['12']['rankPoints']) + " points in solo standard"
        if json_season['13'] != None:
            speech_output += str(json_season['13']['rankPoints']) + " points in standard"
    else:
        if json_season['10'] != None:
            if numPlaylists >= 3:
                speech_output += str(json_season['10']['rankPoints']) + " points in duel, "
            else:
                speech_output += str(json_season['10']['rankPoints']) + " points in duel"
            numPlaylists -= 1
        if json_season['11'] != None:
            if numPlaylists >= 2:
                speech_output += str(json_season['11']['rankPoints']) + " points in doubles, "
            else:
                speech_output += " and " + str(json_season['11']['rankPoints']) + " points in doubles"
            numPlaylists -= 1
        if json_season['12'] != None:
            if numPlaylists >= 2:
                speech_output += str(json_season['12']['rankPoints']) + " points in solo standard, "
            else:
                speech_output += " and " + str(json_season['11']['rankPoints']) + " points in solo standard"
            numPlaylists -= 1
        if json_season['13'] != None:
            speech_output += " and " + str(json_season['13']['rankPoints']) + " points in standard"
    speech_output += " so far in season " + mostRecentSeason

    return speech_output

def database_api_lookup(player_id, alexa_user_id):
    # Map player to their unique id and platform id
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(TABLE_NAME)
    dbLookupResult = table.get_item(
            Key={'AlexaUserID' : alexa_user_id}
        )

    # Check to see if Alexa user has been created in DB
    if 'Item' not in [item for item in dbLookupResult]:
        return "Player "+player_id+" not found in skill lookup. Please add the player to my database with the phrase 'Alexa, add player'"

    AccountNames = dbLookupResult['Item']['AccountNames']

    # Check to see if local user exists
    if player_id not in [name for name in AccountNames]:
        return "Player "+player_id+" not found in skill lookup. Please add the player to my database with the phrase 'Alexa, add player'"


    player_id_and_platform = dbLookupResult['Item']['AccountNames'][player_id].split('&')
    unique_id = player_id_and_platform[0]
    platform_id = player_id_and_platform[1]

    print('Player ID: ' + player_id)
    print('Platform ID: ' + platform_id)

    # Do an RL API lookup to see whose name it is
    # player_id = result of lookup
    session_attributes = create_player_id_attributes(player_id)
    proc = subprocess.Popen(['curl', "https://api.rocketleaguestats.com/v1/player?unique_id="+unique_id+"&platform_id="+platform_id, 
                                '-H', "Authorization: Bearer "+API_Key.key], stdout=subprocess.PIPE)
    apiLookupResult = ''
    for line in iter(proc.stdout.readline, ''):
        apiLookupResult = line
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    print(apiLookupResult)
    if apiLookupResult == '':
        speech_output = 'Nothing returned from Rocket League API for player <say-as interpret-as="spell-out">'+unique_id+'</say-as>. Please try again later.'
        return speech_output

    json_result = json.loads(apiLookupResult)
    return json_result


def lookup_player(intent, session, intent_request):
    """ Looks up a player's screenname in the database, then makes Rocket League API call to get data
    """

    card_title = "Lookup Player"
    session_attributes = {}
    should_end_session = False

    if 'name' in intent['slots']:
        # Check to see if all slots are populated 
        if intent_request[u'dialogState'] != "COMPLETED" or 'value' not in intent['slots']['name']:
            return build_response(session_attributes, buildSpeechletResponseWithDirectiveNoIntent(intent))
        player_id = intent['slots']['name']['value'].lower()
        unique_id = ""
        platform_id = ""
        alexa_user_id = session['user']['userId']

        
        api_lookup_result = database_api_lookup(player_id, alexa_user_id)

        # if function returns a string, that means there was an error, so build response. Otherwise proceed as before
        if type(api_lookup_result) == type("hi") or type(api_lookup_result)==type(u'hi'):
            should_end_session = True
            return build_response(session_attributes, build_speechlet_response(
                card_title, api_lookup_result, "", should_end_session))

        # otherwise, parse it and generate a speech output
        speech_output = parse_api_call(player_id, api_lookup_result)
        should_end_session = True
        
    else:
        speech_output = "I'm not sure what your user name is. " \
                        "Please contact your administrator."
        should_end_session = True
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, "", should_end_session))


def successfully_removed_player(player_id, session_attributes, card_title, should_end_session):
    """ Helper function to generate response on successful removal """
    speech_output = "Successfully removed player " + player_id + ". What else would you like to do?"
    reprompt_text = "I'm sorry, I didn't catch that. Please try again."
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

def remove_player(intent, session, intent_request):
    """ Removes a player from the database"""
    session_attributes = {}
    card_title = "Remove Player"
    should_end_session = False

    if intent_request[u'dialogState'] != "COMPLETED" or 'value' not in intent['slots']['name']:
            return build_response(session_attributes, buildSpeechletResponseWithDirectiveNoIntent(intent))

    # Extract variables from request
    player_id = intent['slots']['name']['value'].lower()
    print("Removing Player_id: " + player_id)

    # Map player to their unique id and platform id
    dynamodb = boto3.resource('dynamodb')
    alexa_user_id = session['user']['userId']
    table = dynamodb.Table(TABLE_NAME)

    # Update player's database item to remove the necessary player
    try:
        table.update_item(
                Key={'AlexaUserID' : alexa_user_id},
                UpdateExpression="REMOVE AccountNames."+player_id

            )
        return successfully_removed_player(player_id, session_attributes, card_title, should_end_session)
    except ClientError as e:
        speech_output = e.response['Error']['Message'] + '. Operation failed.'
        reprompt_text = 'Please try again'
        return build_response(session_attributes, build_speechlet_response(
                card_title, speech_output, reprompt_text, should_end_session))


def successfully_added_player(player_id, session_attributes, card_title, should_end_session):
    speech_output = "Successfully created player for " + player_id + '. What else would you like to do?'
    reprompt_text = "Sorry, I didn't catch that. What else would you like to do?"
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

# Create new player in database
def add_player(intent, session, intent_request):
    # Initialize variables
    card_title = "Add Player"
    session_attributes = {}
    slots = intent['slots']
    should_end_session = False
    player_id = ""
    platform_id = ""
    screenName = ""
    speech_output = ""
    reprompt_text = ""

    # Check to see if all slots are populated 
    if intent_request[u'dialogState'] != "COMPLETED":
        return build_response(session_attributes, buildSpeechletResponseWithDirectiveNoIntent(intent))
    # Check to see if intent is confirmed. If not dialogState is COMPLETED but not confirmed,
    #   user must have detected an error
    elif intent['confirmationStatus'] != "CONFIRMED":
        return build_response(session_attributes, build_speechlet_response(
            card_title, "I'm sorry, your request could not be confirmed. Please try again", "Please try again by saying, 'add player'.", should_end_session))

    # Since all slots are valid, we can save variables
    player_id = slots['name']['value'].lower()
    platform = slots['console']['value'].lower()

    # Map input slots to platform id's
    if platform == 'steam' or platform == 'pc':
        platform_id = '1'
    elif '4' in platform or 'station' in platform:   # ps4
        platform_id = '2'
    elif platform == 'xbox':
        platform_id = '3'

    # Get screename by assembling characters, one at a time until there isn't a value in the slot
    characterSlots = slots
    for slotName in characterList:
        next_slot = characterSlots[slotName]
        if 'value' not in [key for key in next_slot]:
            break
        cleanedCharKey = next_slot['value'].lower()
        cleanedCharKey = "".join(c for c in cleanedCharKey if c not in ('.')).encode('ascii')
        if cleanedCharKey not in letter_lookup.keys():
            for character in cleanedCharKey:
                screenName += letter_lookup[character]
        else:
            screenName += letter_lookup[cleanedCharKey]

    print("Character screenname is:"+ screenName)



    # Check if name already exists
    dynamodb = boto3.resource('dynamodb')
    alexa_user_id = session['user']['userId']
    table = dynamodb.Table(TABLE_NAME)
    dbLookupResult = table.get_item(
            Key={'AlexaUserID' : alexa_user_id}
    )
    if 'Item' in [item for item in dbLookupResult]:
        names = [name for name in dbLookupResult['Item']['AccountNames']]
        print("Existing names for current account: ")
        for name in names:
            print(name)

        # Check to make sure no more than 10 users per acct 
        if len(names) > 9:
            speech_output = "You already have 10 players for this account. Please remove some before adding more."
            reprompt_text = speech_output
            return build_response(session_attributes, build_speechlet_response(
                card_title, speech_output, reprompt_text, should_end_session))

        # Check if player already exists with this name
        elif player_id in names:
            speech_output = "Player already exists in this account. Please add the player with a different name"
            reprompt_text = speech_output
            return build_response(session_attributes, build_speechlet_response(
                card_title, speech_output, reprompt_text, should_end_session))

        # Account exists, need to modify 
        else:
            try:
                # Modify Item to add player to map
                table.update_item(
                    Key={'AlexaUserID' : alexa_user_id},
                    UpdateExpression="SET AccountNames."+player_id+" = :updated",
                    ExpressionAttributeValues= {':updated' : screenName+'&'+platform_id}

                )
                return successfully_added_player(player_id, session_attributes, card_title, should_end_session)
            except ClientError as e:
                speech_output = e.response['Error']['Message'] + '. Operation failed.'
                reprompt_text = "Please try again"
                return build_response(session_attributes, build_speechlet_response(
                    card_title, speech_output, reprompt_text, should_end_session))
    else:
        # Create new Item for player   
        try:
            item = {
                'AlexaUserID' : alexa_user_id,
                'AccountNames' : {
                    player_id : screenName+"&"+platform_id
                }
            }
            table.put_item(Item=item)
        except ClientError as e:
            speech_output = e.response['Error']['Message'] + '. Operation failed.'
            reprompt_text = "Please try again"
            return build_response(session_attributes, build_speechlet_response(
                card_title, speech_output, reprompt_text, should_end_session))



    speech_output = "Name saved as " + player_id + ". What else would you like to do?"
    reprompt_text = "Sorry, i didn't catch that. What else would you like to do?"

    return build_response(session_attributes, build_speechlet_response(
            card_title, speech_output, reprompt_text, should_end_session))
    

def stat_lookup(intent, session, intent_request):
    # Initialize variables
    card_title = "General Stat Lookup"
    session_attributes = {}
    should_end_session = False
    slots = intent['slots']

    # Check if dialog state is completed. "and not" is necessary because sometimes Alexa will mark dialog as "STARTED"
    #   even if all slots are filled, so the extra check is performed
    if intent_request[u'dialogState'] != "COMPLETED" and not ('value' in slots['name'] and 'value' in slots['statType']):
        return build_response(session_attributes, buildSpeechletResponseWithDirectiveNoIntent(intent))
    
    # Once slots are populated, save them
    player_id = intent['slots']['name']['value'].lower()
    stat_slot = intent['slots']['statType']['value'].lower()
    alexa_user_id = session['user']['userId']

    # Lookup will be JSON if everything went smoothly. Containing all info about player
    lookup_response = database_api_lookup(player_id, alexa_user_id)
    print("Lookup response is: ")
    print(lookup_response)
    print(type(lookup_response))
    print(type("hi"))


    # if response is unicode, there was an error
    if type(lookup_response) == type(u'hi'):
        return build_response(session_attributes, build_speechlet_response(
            card_title, lookup_response, "Please try with another player", should_end_session))

    # Calculate the desired value, and format it properly
    desired_stat = ""
    print("Requested stat slot is: " + stat_slot)
    if stat_slot == "shot to goal ratio" or stat_slot == "accuracy" or stat_slot == "goal to shot ratio":
        desired_stat = float(lookup_response['stats']['goals'])/int(lookup_response['stats']['shots'])
        desired_stat = "{0:.3f}".format(desired_stat)
    elif stat_slot == "mvp per win ratio" or stat_slot == "mvp to win ratio":
        desired_stat = float(lookup_response['stats']['mvps'])/int(lookup_response['stats']['wins'])
        desired_stat = "{0:.3f}".format(desired_stat)
    else:
        desired_stat = "not found"

    speech_response = player_id+"'s " + stat_slot+" is " + desired_stat+". What else would you like to do?"
    reprompt_text = "sorry, I didn't catch that. What else would you like to do?"
    return build_response(session_attributes, build_speechlet_response(
            card_title, speech_response, "", should_end_session))

def points_remaining(intent, session, intent_request):
    # initialize variables
    card_title = "Points/Games Remaining"
    session_attributes = {}
    should_end_session = False
    speech_output = ""
    slots = intent['slots']
    
    # Example slot values mapped to their respective playlists
    duel_slots = ['duel', 'singles', 'solo']
    doubles_slots = ['two vs two', 'doubles', '2 vs 2', 'two versus two', '2 versus 2']
    standard_slots = ['triples', 'triplets', '3 vs 3', 'three versus three', 'three vs three', '3 versus 3', ]

    # Check to make sure dialog is complete. the "and not" is necessary because lately
    #   I've had a problem where a user specifies all the information but dialogState is not marked "COMPLETED"
    if intent_request[u'dialogState'] != "COMPLETED" and not ('value' in slots['name'] and 'value' in slots['unit'] and 'value' in slots['playlist']):
        return build_response(session_attributes, buildSpeechletResponseWithDirectiveNoIntent(intent))
    
    # Pull the values from the populated slots
    player_id = intent['slots']['name']['value'].lower()
    playlist_name = slots['playlist']['value']
    unit = intent['slots']['unit']['value'].lower()
    print("Requests contains player id: " + player_id + ", playlist: " + playlist_name + ", unit: " + unit)
    
    # Find the requested playlist ID
    playlist_id = ""
    if playlist_name in duel_slots:
        playlist_id = "10"
    elif playlist_name in doubles_slots:
        playlist_id = "11"
    elif playlist_name in standard_slots:
        playlist_id = "12"
    else:
        playlist_id = "13"
    alexa_user_id = session['user']['userId']


    # Find the current season
    lookup_response = database_api_lookup(player_id, alexa_user_id)
    # Check for errors. Errors will be unicode type
    if type(lookup_response) == type(u'hi'):
        return build_response(session_attributes, build_speechlet_response(
            card_title, lookup_response, "Please try with another player", should_end_session))

    # Find the most recent season
    mostRecentSeason = [season for season in lookup_response['rankedSeasons']][0]
    json_season = lookup_response['rankedSeasons'][mostRecentSeason]
    print(lookup_response['rankedSeasons'][mostRecentSeason])
    curr_points = 0
    curr_tier = 0

    # If season data for given playlist exists, save values
    if json_season[playlist_id] != None:
        curr_points = int(json_season[playlist_id]['rankPoints']) 
        curr_tier =  int(json_season[playlist_id]['tier']) 
        print("Curr points for player " + player_id + " in playlist " + playlist_name + " is: " + str(curr_points))
    else:
        speech_output += "no data available for " + playlist_name
        return build_response(session_attributes, build_speechlet_response(
            card_title, speech_output, "", should_end_session))

    # Look up skill distribution to find how points map to tiers/divisions
    url = "https://rocketleague.tracker.network/distribution"
    f = requests.get(url).text

    # find the right number of points
    soup = BeautifulSoup(f, 'html.parser')

    # Parse the html to find current tier points, next tier points (if there is a next tier), and corresponding labels
    tier_list = soup(class_='col-md-4')
    # Index is increasing as rank goes down. Grand champion = tier_list[0]
    curr_tier_soup = tier_list[len(tier_list)-1-curr_tier]
    # Basically want tier_list[prev-1] to be one higher
    next_tier_soup = tier_list[max(0, (len(tier_list)-1-curr_tier)-1)]

    # Calculate point difference between highest possible point for current tier, and the points found from API
    points_needed = int(curr_tier_soup(class_='division')[0].find_all('div')[2].string)+1
    diff_points = points_needed - curr_points
    next_tier_label = list(next_tier_soup.h3.children)[2].split()
    print("next tier label:")
    print(next_tier_label)

    # Replace roman numerals with actual numbers so Alexa can read them
    if next_tier_label[-1] == u'I':
        next_tier_label[-1] = u'1'
    elif next_tier_label[-1] == u'II':
        next_tier_label[-1] = u'2'
    elif next_tier_label[-1] == u'III':
        next_tier_label[-1] = u'3'
    elif next_tier_label[-1] == u'IV':
        next_tier_label[-1] = u'4'
    elif next_tier_label[-1] == u'V':
        next_tier_label[-1] = u'5'
    next_tier_label = ' '.join(next_tier_label)
    
    # Formulate responses based on input. Assuming +9 points per win
    if curr_tier == 0:
        speech_output = player_id + " has reached maximum tier. Congratulations"
    elif unit == 'games':
        speech_output = player_id + " is " + str(diff_points/14+1) + " games away from reaching " + next_tier_label + " in " + playlist_name
    else:
        speech_output = player_id + " is " + str(diff_points) + " points away from reaching " + next_tier_label + " in " + playlist_name

    print(speech_output)
    return build_response(session_attributes, build_speechlet_response(
            card_title, speech_output, "", should_end_session))


# --------------- Events ------------------

def on_session_started(session_started_request, session):
    """ Called when the session starts """

    print("on_session_started requestId=" + session_started_request['requestId']
          + ", sessionId=" + session['sessionId'])


def on_launch(launch_request, session):
    """ Called when the user launches the skill without specifying what they
    want
    """

    print("on_launch requestId=" + launch_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # Dispatch to your skill's launch
    return get_welcome_response(session)


def on_intent(intent_request, session):
    """ Called when the user specifies an intent for this skill """

    #print("on_intent requestId=" + intent_request['requestId'] +
      #    ", sessionId=" + session['sessionId'])

    intent = intent_request['intent']
    if 'name' in intent_request['intent']:
        intent_name = intent_request['intent']['name']
        print("Intent: " + intent_name)

    # Dispatch to your skill's intent handlers
    if intent_name == "LookupPlayerIntent":
        return lookup_player(intent, session, intent_request)
    elif intent_name == "AddPlayerIntent" or intent_name == "AddPlayer":
        return add_player(intent, session, intent_request)
    elif intent_name == "RemovePlayerIntent":
        return remove_player(intent, session, intent_request)
    elif intent_name == "AAStatLookupIntent":
        return stat_lookup(intent, session, intent_request)
    elif intent_name == "PointsRemainingIntent":
        return points_remaining(intent, session, intent_request)
    elif intent_name == "AMAZON.HelpIntent":
        return get_welcome_response()
    elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
        return handle_session_end_request()
    else:
        raise ValueError("Invalid intent")


def on_session_ended(session_ended_request, session):
    """ Called when the user ends the session.

    Is not called when the skill returns should_end_session=true
    """
    print("on_session_ended requestId=" + session_ended_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # add cleanup logic here


# --------------- Main handler ------------------

def lambda_handler(event, context):
    """ Route the incoming request based on type (LaunchRequest, IntentRequest,
    etc.) The JSON body of the request is provided in the event parameter.
    """
    print("event.session.application.applicationId=" +
          event['session']['application']['applicationId'])

    """
    Uncomment this if statement and populate with your skill's application ID to
    prevent someone else from configuring a skill that sends requests to this
    function.
    """
    # if (event['session']['application']['applicationId'] !=
    #         "amzn1.echo-sdk-ams.app.[unique-value-here]"):
    #     raise ValueError("Invalid Application ID")

    print("LAMBDA RECEIVED:")
    
    print (event)

    if event['session']['new']:
        on_session_started({'requestId': event['request']['requestId']},
                           event['session'])

    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session'])
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'])
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended(event['request'], event['session'])
