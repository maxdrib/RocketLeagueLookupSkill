# RocketLeagueLookupSkill
Skill available at https://www.amazon.com/dp/B072K4DDLB/ref=sr_1_1?s=digital-skills&ie=UTF8&qid=1499405961&sr=1-1&keywords=rocket+league

All else that's required to host is a separate file called API_Key.py which contains the following line:

key = "ROCKETLEAGUEAPIKEYHERE" 
The key is for https://rocketleaguestats.com API, which can be obtained upon request from the website's owner.

Otherwise, this project is a basic Alexa Skills Development Kit model which parameterises all the interactions that can occur with the Echo, along with the Python code that executes for each request. The Python code is hosted on AWS Lambda and is executed when Alexa triggers an Intent such as "LookUpIntent" or "AddPlayerIntent". Then, the Echo sends a JSON request to the Lambda function, which directs the request to the proper handler. Required inputs such as player name and playlist type are called 'slots', and those are used in order to execute specific functions and obtain the necessary information. Once that is done, the Lambda returns another JSON object to the Echo itself, which it parses to speak the proper response.

The information is all stored on a dynamoDB database (also hosted on AWS). New players are added to a table with a sort key of the echo's device ID. Users can add up to 10 players per device.
