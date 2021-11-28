import json
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
            msg = Message(to=data['spade_intro']['username'])     # Instantiate the message
            msg.set_metadata("performative", "inform")     # Set the "inform" FIPA performative
            print("Good morning human!! My name is David. What do you want to know today?")
            #print("Buenos días. Puede hacerme las siguientes preguntas:\n")
            # Options
            # time
            # info from a person wikipedia
            # create file
            # end agent execution
            # 2 more
            terminate = True
            while (terminate):

            
                msg.body = input()                      # Set the message content
                #msg.body = "What time is it?"
                #msg.body = "Create file holo"
                #msg.body = "Tell me about Elon Musk"
                #msg.body = "Bye"
                #More metadata can be added
                #msg.set_metadata("ontology", "myOntology")
                #msg.set_metadata("language", "OWL-S")
                if (msg.body.find("Bye") != -1):
                    terminate = False
                await self.send(msg)
                print("Message sent!")

            
            # stop agent from behaviour
            print("Sender")
            await self.agent.stop()

    async def setup(self):
        print("Agent "+str(self.jid)+ " started")
        b = self.InformBehav()
        self.add_behaviour(b)

class ReceiverAgent(Agent):
    class RecvBehav(OneShotBehaviour):
        async def run(self):
            terminate = True
            while(terminate):
                print("RecvBehav running")

                msg = await self.receive(timeout=10) # wait for a message for 10 seconds
                if msg:
                    print("Message received with content: {}".format(msg.body))
                    if (msg.body == "What time is it?"):
                        #print(strftime("%Y-%m-%d %H:%M:%S", gmtime()))
                        print(strftime("Today is %d %B, %Y, it is %A and it is %H:%M:%S", gmtime()))
                    elif (msg.body.find("Create file ") != -1):
                        s = msg.body.split("Create file ")[1]
                        print(s)
                        f = open(s, "x")
                        f.close()
                    elif (msg.body.find("Tell me about ") != -1):
                        myString = msg.body.split("Tell me about ")[1]
                        s = myString.replace(" ", "_")
                        print("Sale: " + s)
                        page = requests.get('https://es.wikipedia.org/wiki/' + s)
                        html_soup = BeautifulSoup(page.content, 'html.parser')

                        panel = html_soup.find('div',{'id' : 'mw-content-text'})
                        parrafo = panel.find('p').text
                        print(parrafo,'\n')
                    elif (msg.body.find("Bye") != -1):
                        terminate = False
                else:
                    print("Did not received any message after 10 seconds")
            print("Receiver")
            # stop agent from behaviour
            await self.agent.stop()

    async def setup(self):
        print("ReceiverAgent started")
        b = self.RecvBehav()

        # Msg Template
        template = Template()
        template.set_metadata("performative", "inform")

        # Adding the Behaviour with the template will filter all the msg
        self.add_behaviour(b, template)



def main():
    
    # Create the agent
    print("Creating Agents ... ")
    receiveragent = ReceiverAgent(data['spade_intro']['username'], 
                            data['spade_intro']['password'])
    future = receiveragent.start()
    future.result()
    senderagent = SenderAgent(data['spade_intro_2']['username'], 
                            data['spade_intro_2']['password'])
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