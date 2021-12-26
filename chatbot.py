# Options
# time
# info from a person wikipedia
# create file
# end agent execution
# 2 more

import json
import os
import time
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

class SenderAgent(Agent):
    class InformBehav(OneShotBehaviour):
        async def run(self):

            # Message
            print("InformBehav running")
            print("Good morning human!! My name is David. What do you want to know today?")
            
            #msg.body = input()                      # Set the message content
            msg = Message(to=data['spade_chatbot_receiver']['username'])     # Instantiate the message
            msg.set_metadata("performative", "request")     # Set the "inform" FIPA performative
            terminate = True
            while(terminate):
                msg.body = input()
                #msg.body = "What time is it?"
                #msg.body = "Create file holo"
                #msg.body = "Tell me about Elon Musk"
                #msg.body = "Bye"

                if (msg.body.find("Bye") != -1):
                    terminate = False
                await self.send(msg)
                print("Message sent!")

                reply = await self.receive(timeout=10)
                if (reply):
                    if (reply.body() == "Bye"):
                        self.kill(exit_code=10)
                    print("(Emisor) Message received with content: \n{}".format(reply.body))
            # stop agent from behaviour
            print("Sender")
            await self.agent.stop()

    async def setup(self):
        print("Agent "+str(self.jid)+ " started")

        template = Template()
        template.set_metadata("performative", "inform")

        b = self.InformBehav()
        self.add_behaviour(b, template)

class ReceiverAgent(Agent):
    class RecvBehav(OneShotBehaviour):
        async def run(self):
            terminate = True
            while(terminate):
                print("RecvBehav running")

                msg = await self.receive(timeout = 30) # wait for a message for 10 seconds
                if msg:
                    print("Message received with content: {}".format(msg.body))
                    if (msg.body == "What time is it?"):
                        self.agent.add_behaviour(self.agent.TimeBehav())
                        
                    elif (msg.body.find("Create file ") != -1):
                        self.agent.add_behaviour(self.agent.CreateFileBehav(msg.body))
                        
                    elif (msg.body.find("Tell me about ") != -1):
                        self.agent.add_behaviour(self.agent.PersonBehav(msg.body))

                    elif (msg.body.find("Bye") != -1):
                        self.agent.add_behaviour(self.agent.EndBehav())
                        terminate = False
                else:
                    print("Did not received any message after 30 seconds")
            print("Receiver")
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
            if not os.path.exists(fileName):
                f = open(fileName, "x")
                f.close()
            reply.body = "Created"
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
            #print("Sale: " + formatedName)
            page = requests.get('https://es.wikipedia.org/wiki/' + formatedName)
            html_soup = BeautifulSoup(page.content, 'html.parser')

            panel = html_soup.find('div',{'id' : 'mw-content-text'})
            parrafo = panel.find('p').text
            reply.body = parrafo + '\n'

            await self.send(reply)
    
    class EndBehav(OneShotBehaviour):
        async def run(self):
            reply = Message(to=data['spade_chatbot_sender']['username'])     # Instantiate the message
            reply.set_metadata("performative", "inform")     # Set the "inform" FIPA performative
            reply.body = "Bye"
            await self.send(reply)
            self.kill(exit_code=10)

    async def setup(self):
        print("ReceiverAgent started")
        b = self.RecvBehav()

        # Msg Template
        template = Template()
        template.set_metadata("performative", "request")

        # Adding the Behaviour with the template will filter all the msg
        self.add_behaviour(b, template)



def main():
    
    # Create the agent
    print("Creating Agents ... ")
    receiveragent = ReceiverAgent(data['spade_chatbot_receiver']['username'], 
                            data['spade_chatbot_receiver']['password'])
    future = receiveragent.start()
    future.result()
    senderagent = SenderAgent(data['spade_chatbot_sender']['username'], 
                            data['spade_chatbot_sender']['password'])
    senderagent.start()
    
    while receiveragent.is_alive():
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            senderagent.stop()
            receiveragent.stop()
            break
    print("Agents finished")

if __name__ == "__main__":
    main()