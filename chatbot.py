# Options
# time
# info from a person wikipedia
# create file
# end agent execution
# 2 more

import json
import os
import requests
import logging
import re

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

class User(Agent):
    class UserBehav(CyclicBehaviour):
        async def on_start(self):
            logging.info('UserBehav running')
            # Message
            print("Bot say: Good morning human!! My name is David. What do you want to do today?")
        
        async def run(self):
            
            msg = Message(to=data['spade_chatbot_receiver']['username'])     # Instantiate the message
            msg.set_metadata("performative", "request")     # Set the "inform" FIPA performative
            
            print("You say: ", end="")
            msg.body = input()
            
            await self.send(msg)

            logging.info('Message sent!')
            
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

        template = Template()
        template.set_metadata("performative", "inform")

        b = self.UserBehav()
        self.add_behaviour(b, template)

class Chatbot(Agent):
    class ChatbotBehav(CyclicBehaviour):

        async def on_start(self):
            logging.info('ChatbotBehav running')

        async def run(self):
            msg = await self.receive(timeout=30) # wait for a message for 10 seconds
            if msg:
                logging.info(f'(Chatbot) Message received with content: {msg.body}')
                if (re.search(r"^(H|h)ow[a-zA-Z_ ]*say[a-zA-Z_ ]*(S|s)panish:\s", msg.body)):
                    self.agent.add_behaviour(self.agent.TranslatorBehav(msg.body))

                elif (re.search(r"^(W|w)hat[a-zA-Z_ ]*time[a-zA-Z_ ]*?", msg.body)):
                    self.agent.add_behaviour(self.agent.TimeBehav())
                    
                elif (re.search(r"^(C|c)reate\s*file\s", msg.body)):
                    self.agent.add_behaviour(self.agent.CreateFileBehav(msg.body))
                    
                elif (re.search(r"^(T|t)ell\s*(me|)\s*about\s", msg.body)):
                    self.agent.add_behaviour(self.agent.PersonBehav(msg.body))

                elif (re.search(r"^((B|b)ye|(S|s)ee\s*you|(E|e)xit)", msg.body)):
                    self.agent.add_behaviour(self.agent.EndBehav())

                else:
                    self.agent.add_behaviour(self.agent.OptionsBehav())
            else:
                print("Bot say: You've been thinking for 30 seconds, are you okay?")

    class TimeBehav(OneShotBehaviour):
        async def run(self):
            logging.info('TimeBehav running')

            reply = Message(to=data['spade_chatbot_sender']['username'])     # Instantiate the message
            reply.set_metadata("performative", "inform")     # Set the "inform" FIPA performative
            timeStr = strftime("Today is %d %B, %Y, it is %A and it is %H:%M:%S", localtime())
            reply.body = timeStr
            await self.send(reply)

    class CreateFileBehav(OneShotBehaviour):
        
        def __init__(self, body):
            super().__init__()
            self.str = body

        async def run(self):
            logging.info('CreateFileBehav running')

            reply = Message(to=data['spade_chatbot_sender']['username'])     # Instantiate the message
            reply.set_metadata("performative", "inform")     # Set the "inform" FIPA performative

            fileName = self.str.split("file ")[1]
            if os.path.exists(fileName):
                reply.body = "Fille " + fileName + " already exists."
            else:
                f = open(fileName, "x")
                f.close()
                reply.body = "Fille " + fileName + " has been created."
            
            await self.send(reply)

    class PersonBehav(OneShotBehaviour):

        def __init__(self, body):
            super().__init__()
            self.str = body

        async def run(self):
            logging.info('PersonBehav running')

            reply = Message(to=data['spade_chatbot_sender']['username'])     # Instantiate the message
            reply.set_metadata("performative", "inform")     # Set the "inform" FIPA performative

            name = self.str.split("about ")[1]
            formatedName = name.replace(" ", "_")

            logging.info("Formatted name: " + formatedName)

            try:
                page = requests.get('https://en.wikipedia.org/wiki/' + formatedName)
                html_soup = BeautifulSoup(page.content, 'html.parser')
                panel = html_soup.find('div',{'id' : 'mw-content-text'})
                internalPanel = panel.find('div',{'class':'mw-parser-output'})  
                paragraph = internalPanel.findChildren("p", recursive=False)[1].text # Second p instance on English Wikipedia

                reply.body = paragraph
            
            except:
                reply.body = "It has not been possible to find information on this person."

            await self.send(reply)
            
    class TranslatorBehav(OneShotBehaviour):

        def __init__(self, body):
            super().__init__()
            self.str = body

        async def run(self):
            logging.info('TranslatorBehav running')

            reply = Message(to=data['spade_chatbot_sender']['username'])     # Instantiate the message
            reply.set_metadata("performative", "inform")     # Set the "inform" FIPA performative

            translator = Translator()
            noTranslateText = self.str.split(": ")[1]

            logging.info("Text before translate: " + noTranslateText)

            translateText = translator.translate(noTranslateText, src = 'en', dest = 'es')
            reply.body = translateText.text
            await self.send(reply)
    
    class EndBehav(OneShotBehaviour):
        async def run(self):
            logging.info('EndBehav running')

            reply = Message(to=data['spade_chatbot_sender']['username'])     # Instantiate the message
            reply.set_metadata("performative", "inform")     # Set the "inform" FIPA performative
            reply.body = "Bye human. It has been a pleasure talking to you."
            await self.send(reply)
            logging.info("Terminate Chatbot")
            await self.agent.stop()

    class OptionsBehav(OneShotBehaviour):
        async def run(self):
            logging.info('OptionsBehav running')

            reply = Message(to=data['spade_chatbot_sender']['username'])     # Instantiate the message
            reply.set_metadata("performative", "inform")     # Set the "inform" FIPA performative
            options = "I have no answer to that. But you can try this functionalities: \n" 
            options += "- What time is it? \n" 
            options += "- Create file <file_name> \n"
            options += "- Tell me about <person_name> \n"
            options += "- How can I say that on Spanish: <sentence_to_translate> \n"
            options += "- Bye"
            reply.body = options
            await self.send(reply)

    async def setup(self):
        logging.info(f'Agent {str(self.jid)} started')
        b = self.ChatbotBehav()

        # Msg Template
        template = Template()
        template.set_metadata("performative", "request")

        # Adding the Behaviour with the template will filter all the msg
        self.add_behaviour(b, template)



def main():
    # Change logging level to check execution
    #logging.getLogger().setLevel(logging.INFO)
    # Create the agent
    logging.info('Creating Agents ... ')
    chatbotAgent = Chatbot(data['spade_chatbot_receiver']['username'], 
                            data['spade_chatbot_receiver']['password'])
    future = chatbotAgent.start()
    future.result()
    userAgent = User(data['spade_chatbot_sender']['username'], 
                            data['spade_chatbot_sender']['password'])
    userAgent.start()
    
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