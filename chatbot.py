
'''
This program is a functional chatbot with a multiagent system. The user is one agent 
and the chatbot is another agent. The chatbot has the following functions:
- What time is it?
- Crate a file
- Search for information about a specific person
- Translate a sentence from English to Spanish
- Calculate the result of an operation with addition, subtraction, multiplication, division and power
- Terminate the execution of the agents
- Show the possible functionalities
'''

import json
import os
import requests
import logging
import re
import psycopg2

from googletrans.client import Translator
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour, OneShotBehaviour
from spade.message import Message
from spade.template import Template
from time import localtime, sleep, strftime
from bs4 import BeautifulSoup

# Load the json file with the crendentials
f = open('credentials.json',)
data = json.load(f)
loggingFileName = "chatbot.log"

class User(Agent):
    class UserBehav(CyclicBehaviour):
        async def on_start(self):
            logging.info('UserBehav running')
            print("Bot say: Good morning human!! My name is David. What do you want to do today?")
        
        async def run(self):
            msg = Message(to=data['spade_chatbot']['username'])     # Instantiate the message
            msg.set_metadata("performative", "request")     # Set the "request" FIPA performative
            
            print("You say: ", end="")
            msg.body = input() # Enter the user text
            
            await self.send(msg)

            logging.info('Message sent!')
            
            # Set a timeout of 10 seconds between sending a message to the chatbot and receiving a reply
            reply = await self.receive(timeout=10) 
            
            logging.info(f'(User) Message received with content: {reply.body}')
            
            if (reply):
                print("Bot say: {}".format(reply.body))
                if (reply.body.find("Bye") != -1 and reply.body.find("-") == -1):
                    logging.info("Terminate User")
                    self.kill(exit_code=10)
            else:
                print("Bot say: An error has occurred")

        async def on_end(self):
            await self.agent.stop()

    async def setup(self):
        logging.info(f'Agent {str(self.jid)} started')

        # Msg template
        template = Template() 
        template.set_metadata("performative", "inform") # Filter inform messages

        b = self.UserBehav()
        self.add_behaviour(b, template)

class Chatbot(Agent):

    class ChatbotBehav(CyclicBehaviour):

        async def on_start(self):
            logging.info('ChatbotBehav running')
            # Connect with psycopg2 to the docker postgres db container
            db_conn = psycopg2.connect(host='host.docker.internal', port='5432', 
            dbname='chatbot_postgres_db', user='sma', password='sma')
            db_cursor = db_conn.cursor()

            # Search web to use for web scrapping
            db_cursor.execute("SELECT web FROM webs WHERE id = 1;")
            self.agent.pages = db_cursor.fetchall()

            # Return all regular expressions stored at postgres db
            db_cursor.execute("SELECT regexbehav FROM regularexpressions;")
            self.agent.regularExpressions = db_cursor.fetchall() 

        async def run(self):
            msg = await self.receive(timeout=30) # wait for a message for 30 seconds and reset
            if msg:
                logging.info(f'(Chatbot) Message received with content: {msg.body}')
                # Filter with this regex 'to\s+(S|s)panish$'
                if (re.search(str(self.agent.regularExpressions[0][0]), msg.body)):
                    self.agent.add_behaviour(self.agent.TranslatorBehav(msg.body))

                # Filter with this regex '^(H|h)ow\s+much\s+is\s+(\d+["+""*""-""/""**"])+'
                elif (re.search(str(self.agent.regularExpressions[1][0]), msg.body)):
                    self.agent.add_behaviour(self.agent.CalculateBehav(msg.body))

                # Filter with this regex '^(W|w)hat[a-zA-Z_ ]*time[a-zA-Z_ ]*\?'
                elif (re.search(str(self.agent.regularExpressions[3][0]), msg.body)):
                    self.agent.add_behaviour(self.agent.TimeBehav())
                
                # Filter with this regex '^(C|c)reate\s+file\s+'
                elif (re.search(str(self.agent.regularExpressions[4][0]), msg.body)):
                    self.agent.add_behaviour(self.agent.CreateFileBehav(msg.body))
                
                # Filter with this regex '^(S|s)how\s+login\s+file\s*'
                elif (re.search(str(self.agent.regularExpressions[5][0]), msg.body)):
                    self.agent.add_behaviour(self.agent.ShowLoginBehav())
                
                # Filter with this regex '^(T|t)ell\s+(me|)\s+about\s+'
                elif (re.search(str(self.agent.regularExpressions[6][0]), msg.body)):
                    self.agent.add_behaviour(self.agent.PersonBehav(msg.body))

                # Filter with this regex '^((B|b)ye|(S|s)ee\s+you|(E|e)xit)'
                elif (re.search(str(self.agent.regularExpressions[7][0]), msg.body)):
                    self.agent.add_behaviour(self.agent.EndBehav())

                else:
                    self.agent.add_behaviour(self.agent.OptionsBehav())
            else:
                print("Bot say: You've been thinking for 30 seconds, are you okay?")

    class TimeBehav(OneShotBehaviour):
        async def run(self):
            logging.info('TimeBehav running')

            reply = Message(to=data['spade_user']['username'])     # Instantiate the message
            reply.set_metadata("performative", "inform")     # Set the "inform" FIPA performative
            # Get localtime Europe/Madrid declared on Dockerfile
            timeStr = strftime("Today is %d %B, %Y, it is %A and it is %H:%M:%S", localtime())
            reply.body = timeStr
            await self.send(reply)

    class CreateFileBehav(OneShotBehaviour):
        
        def __init__(self, body):
            super().__init__()
            self.str = body

        async def run(self):
            logging.info('CreateFileBehav running')

            reply = Message(to=data['spade_user']['username'])     # Instantiate the message
            reply.set_metadata("performative", "inform")     # Set the "inform" FIPA performative

            # Filter with this regex '^(C|c)reate\s+file\s+'
            coincidence = re.search(str(self.agent.regularExpressions[4][0]), self.str)
            # Split an take the file name
            fileName = self.str.split(coincidence.group())[1]
            # If the file already exists it will be communicated and its content will be sent
            if os.path.exists(fileName):
                reply.body = "Fille " + fileName + " already exists. \n" + \
                    "File content: \n"
                f = open(fileName, 'r')
                reply.body += f.read()
                f.close
            # If the file does not exist, it will be created
            else:
                f = open(fileName, "w")
                # A little text will be write inside the file
                f.write("I am the file " + fileName + " and I have been created by chatbot.")
                f.close()
                reply.body = "File " + fileName + " has been created."
            
            await self.send(reply)

    class ShowLoginBehav(OneShotBehaviour):

        async def run(self):
            logging.info('ShowLoginBehav running')

            reply = Message(to=data['spade_user']['username'])     # Instantiate the message
            reply.set_metadata("performative", "inform")     # Set the "inform" FIPA performative

            if os.path.exists(loggingFileName):
                f = open(loggingFileName, 'r')
                reply.body = f.read()
                f.close()
            else:
                reply.body = "File " + loggingFileName + " does not exist."
            
            await self.send(reply)

    class PersonBehav(OneShotBehaviour):

        def __init__(self, body):
            super().__init__()
            self.str = body

        async def run(self):
            logging.info('PersonBehav running')

            reply = Message(to=data['spade_user']['username'])     # Instantiate the message
            reply.set_metadata("performative", "inform")     # Set the "inform" FIPA performative

            # Filter wiht this regex '^(T|t)ell\s+(me|)\s+about\s+'
            coincidence = re.search(str(self.agent.regularExpressions[6][0]), self.str)
            # Split and take person's name
            name = self.str.split(coincidence.group())[1]
            # Delete spaces at the end of the name
            while(name[-1] == ' '):
                name = name[:-1]
            # Replace spaces for '_' to match format with url
            formatedName = name.replace(" ", "_")

            logging.info("Formatted name: " + formatedName)

            try:
                # Access to 'https://en.wikipedia.org/wiki/<name>'
                page = requests.get(str(self.agent.pages[0][0]) + formatedName)
                # Search first paragraph of the page
                html_soup = BeautifulSoup(page.content, 'html.parser')
                panel = html_soup.find('div',{'id' : 'mw-content-text'})
                internalPanel = panel.find('div',{'class':'mw-parser-output'})  
                paragraph = internalPanel.findChildren("p", recursive=False)[1].text # Second p instance on English Wikipedia

                reply.body = paragraph
            
            except:
                # Error message, the right person could not be found
                reply.body = "It has not been possible to find information on this person. " + \
                    "You may have spelt the name wrong. Pay attention to capital letters."

            await self.send(reply)
            
    class TranslatorBehav(OneShotBehaviour):

        def __init__(self, body):
            super().__init__()
            self.str = body
        
        async def run(self):
            logging.info('TranslatorBehav running')

            reply = Message(to=data['spade_user']['username'])     # Instantiate the message
            reply.set_metadata("performative", "inform")     # Set the "inform" FIPA performative

            # Filter with this regex 'to\s+(S|s)panish$'
            coincidence = re.search(str(self.agent.regularExpressions[0][0]), self.str)
            # Catch phrase before the regex match
            noTranslateText = self.str.split(coincidence.group())[0]
            
            logging.info("Text before translate: " + noTranslateText)

            translator = Translator() # Instantiate Translator
            # Translate from English to Spanish
            translateText = translator.translate(noTranslateText, src = 'en', dest = 'es')
            reply.body = translateText.text
            await self.send(reply)
    
    class CalculateBehav(OneShotBehaviour):

        def __init__(self, body):
            super().__init__()
            self.str = body

        async def run(self):
            logging.info('CalculateBehav running')

            reply = Message(to=data['spade_user']['username'])     # Instantiate the message
            reply.set_metadata("performative", "inform")     # Set the "inform" FIPA performative

            # Filter with this regex '^(H|h)ow\s+much\s+is\s+'
            coincidence = re.search(str(self.agent.regularExpressions[2][0]), self.str)
            # Take mathematical expression after regex
            noCalcExpression = self.str.split(coincidence.group())[1]

            logging.info("Expression before calc: " + noCalcExpression)

            # Evaluate expression
            evalExpression = eval(noCalcExpression)
            
            reply.body = str(evalExpression)
            await self.send(reply)
    
    class EndBehav(OneShotBehaviour):
        async def run(self):
            logging.info('EndBehav running')

            reply = Message(to=data['spade_user']['username'])     # Instantiate the message
            reply.set_metadata("performative", "inform")     # Set the "inform" FIPA performative
            reply.body = "Bye human. It has been a pleasure talking to you."
            await self.send(reply)
            logging.info("Terminate Chatbot")
            await self.agent.stop()

    class OptionsBehav(OneShotBehaviour):
        async def run(self):
            logging.info('OptionsBehav running')

            reply = Message(to=data['spade_user']['username'])     # Instantiate the message
            reply.set_metadata("performative", "inform")     # Set the "inform" FIPA performative
            # Possible chatbot options
            options = "I have no answer to that. But you can try this functionalities: \n" + \
                "- What time is it? \n" + \
                "- Create file <file_name> \n" + \
                "- Show login file \n" + \
                "- Tell me about <person_name> \n" + \
                "- <sentence_to_translate> to Spanish\n" + \
                "- How much is <numeric_expression_with_+-*/**> \n" + \
                "- Bye"
            reply.body = options
            await self.send(reply)

    async def setup(self):
        logging.info(f'Agent {str(self.jid)} started')
        b = self.ChatbotBehav()

        # Msg Template
        template = Template()
        template.set_metadata("performative", "request") # Filter request messages

        self.add_behaviour(b, template)



def main():
    # Change logging level to check execution
    logging.basicConfig(filename='chatbot.log', encoding='utf-8', level=logging.INFO)

    # Create the agent
    logging.info('Creating Agents ... ')
    chatbotAgent = Chatbot(data['spade_chatbot']['username'], 
                            data['spade_chatbot']['password'])
    future = chatbotAgent.start()
    future.result()
    userAgent = User(data['spade_user']['username'], 
                            data['spade_user']['password'])
    userAgent.start()
    
    # Control chatbotAgent is still alive
    while chatbotAgent.is_alive():
        try:
            sleep(1)
        except KeyboardInterrupt:
            userAgent.stop()
            chatbotAgent.stop()
            break
    logging.info('Agents finished')

if __name__ == "__main__":
    main()