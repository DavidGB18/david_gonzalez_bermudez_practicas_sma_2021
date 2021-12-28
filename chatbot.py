# Options
# time
# info from a person wikipedia
# create file
# end agent execution
# 2 more

import json
import os
import time
from googletrans.client import Translator
from spade.agent import Agent
from spade.behaviour import OneShotBehaviour
from spade.message import Message
from spade.template import Template
import pandas as pd
from time import gmtime, strftime
from bs4 import BeautifulSoup
import requests

# Load the json file with the crendentials
f = open('credentials.json',)
data = json.load(f)

class User(Agent):
    class UserBehav(OneShotBehaviour):
        async def run(self):

            # Message
            print("Good morning human!! My name is David. What do you want to know today?")
            
            #msg.body = input()                      # Set the message content
            msg = Message(to=data['spade_chatbot_receiver']['username'])     # Instantiate the message
            msg.set_metadata("performative", "request")     # Set the "inform" FIPA performative
            terminate = True
            while(terminate):
                print("You say: ", end="")
                msg.body = input()
                #msg.body = "What time is it?"
                #msg.body = "Create file holo"
                #msg.body = "Tell me about Elon Musk"
                #msg.body = "Bye"
                await self.send(msg)

                reply = await self.receive(timeout=10)
                if (reply):
                    print("Bot say: {}".format(reply.body))
                    if (reply.body.find("Bye") != -1):
                        self.kill(exit_code=10)
                else:
                    print("Bot say: An error has occurred")
            # stop agent from behaviour
            await self.agent.stop()

    async def setup(self):
        print("Agent "+str(self.jid)+ " started")

        template = Template()
        template.set_metadata("performative", "inform")

        b = self.UserBehav()
        self.add_behaviour(b, template)

class Chatbot(Agent):
    class ChatbotBehav(OneShotBehaviour):
        async def run(self):
            terminate = True
            while(terminate):

                msg = await self.receive(timeout=10) # wait for a message for 10 seconds
                if msg:
                    if (msg.body == "What time is it?"):
                        self.agent.add_behaviour(self.agent.TimeBehav())
                        
                    elif (msg.body.find("Create file ") != -1):
                        self.agent.add_behaviour(self.agent.CreateFileBehav(msg.body))
                        
                    elif (msg.body.find("Tell me about ") != -1):
                        self.agent.add_behaviour(self.agent.PersonBehav(msg.body))
                    
                    elif (msg.body.find("How can I say that on Spanish: ") != -1):
                        self.agent.add_behaviour(self.agent.TranslatorBehav(msg.body))

                    elif (msg.body.find("Bye") != -1):
                        self.agent.add_behaviour(self.agent.EndBehav())
                        terminate = False
                    else:
                        self.agent.add_behaviour(self.agent.OtherBehav())
                else:
                    print("Bot say: You've been thinking for a minute, are you okay?")
            # stop agent from behaviour
            await self.agent.stop()

    class TimeBehav(OneShotBehaviour):
        async def run(self):
            reply = Message(to=data['spade_chatbot_sender']['username'])     # Instantiate the message
            reply.set_metadata("performative", "inform")     # Set the "inform" FIPA performative
            timeStr = strftime("Today is %d %B, %Y, it is %A and it is %H:%M:%S", gmtime())
            reply.body = timeStr
            await self.send(reply)

    class CreateFileBehav(OneShotBehaviour):
        
        def __init__(self, body):
            super().__init__()
            self.str = body

        async def run(self):
            reply = Message(to=data['spade_chatbot_sender']['username'])     # Instantiate the message
            reply.set_metadata("performative", "inform")     # Set the "inform" FIPA performative

            fileName = self.str.split("Create file ")[1]
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
            reply = Message(to=data['spade_chatbot_sender']['username'])     # Instantiate the message
            reply.set_metadata("performative", "inform")     # Set the "inform" FIPA performative

            name = self.str.split("Tell me about ")[1]
            formatedName = name.replace(" ", "_")
            page = requests.get('https://es.wikipedia.org/wiki/' + formatedName)
            html_soup = BeautifulSoup(page.content, 'html.parser')

            panel = html_soup.find('div',{'id' : 'mw-content-text'})
            parrafo = panel.find('p').text
            reply.body = parrafo

            await self.send(reply)

    class TranslatorBehav(OneShotBehaviour):

        def __init__(self, body):
            super().__init__()
            self.str = body

        async def run(self):
            reply = Message(to=data['spade_chatbot_sender']['username'])     # Instantiate the message
            reply.set_metadata("performative", "inform")     # Set the "inform" FIPA performative

            translator = Translator()
            noTranslateText = self.str.split("How can I say that on Spanish: ")[1]
            translateText = translator.translate(noTranslateText, src = 'en', dest = 'es')
            reply.body = translateText.text
            await self.send(reply)
    
    class EndBehav(OneShotBehaviour):
        async def run(self):
            reply = Message(to=data['spade_chatbot_sender']['username'])     # Instantiate the message
            reply.set_metadata("performative", "inform")     # Set the "inform" FIPA performative
            reply.body = "Bye"
            await self.send(reply)
            self.kill(exit_code=10)

    class OtherBehav(OneShotBehaviour):
        async def run(self):
            reply = Message(to=data['spade_chatbot_sender']['username'])     # Instantiate the message
            reply.set_metadata("performative", "inform")     # Set the "inform" FIPA performative
            reply.body = "I have no answer to that."
            await self.send(reply)

    async def setup(self):
        print("Agent "+str(self.jid)+ " started")
        b = self.ChatbotBehav()

        # Msg Template
        template = Template()
        template.set_metadata("performative", "request")

        # Adding the Behaviour with the template will filter all the msg
        self.add_behaviour(b, template)



def main():
    
    # Create the agent
    print("Creating Agents ... ")
    chatbotAgent = Chatbot(data['spade_chatbot_receiver']['username'], 
                            data['spade_chatbot_receiver']['password'])
    future = chatbotAgent.start()
    future.result()
    userAgent = User(data['spade_chatbot_sender']['username'], 
                            data['spade_chatbot_sender']['password'])
    userAgent.start()
    
    while chatbotAgent.is_alive():
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            userAgent.stop()
            chatbotAgent.stop()
            break
    print("Agents finished")

if __name__ == "__main__":
    main()