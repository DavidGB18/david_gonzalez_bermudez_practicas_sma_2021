from ctypes import create_string_buffer
import json
import time
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour, OneShotBehaviour
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
            msg = Message(to=data['spade_chatbot_receiver']['username'])     # Instantiate the message
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

                if (msg.body == "What time is it?"):
                    msg.set_metadata("performative", "query")     # Set the "inform" FIPA performative
                    msg.set_metadata("ontology", "time")
                    await self.send(msg)
                    print("Message sent!")
                    timeReplyTemplate = Template()
                    timeReplyTemplate.set_metadata("performative", "inform")
                    timeReplyTemplate.set_metadata("ontology", "time")
                    self.agent.add_behaviour(
                        behaviour=SenderAgent.WaitForDataTime(),
                        template=timeReplyTemplate
                    )
                elif (msg.body.find("Tell me about ") != -1):
                    msg.set_metadata("performative", "query")     # Set the "inform" FIPA performative
                    msg.set_metadata("ontology", "personInfo")
                    await self.send(msg)
                    print("Message sent!")
                    personReplyTemplate = Template()
                    personReplyTemplate.set_metadata("performative", "inform")
                    personReplyTemplate.set_metadata("ontology", "personInfo")
                    self.agent.add_behaviour(
                        behaviour=SenderAgent.WaitForDataPerson(),
                        template=personReplyTemplate
                    )
                elif (msg.body.find("Create file ") != -1):
                    msg.set_metadata("performative", "request")     # Set the "inform" FIPA performative
                    msg.set_metadata("ontology", "createFile")
                    await self.send(msg)
                    print("Message sent!")
                    createFileReplyTemplate = Template()
                    createFileReplyTemplate.set_metadata("performative", "confirm")
                    createFileReplyTemplate.set_metadata("ontology", "createFile")
                    self.agent.add_behaviour(
                        behaviour=SenderAgent.WaitForDataCreateFile(),
                        template=createFileReplyTemplate
                    )
                elif (msg.body.find("Bye") != -1):
                    msg.set_metadata("performative", "request")     # Set the "inform" FIPA performative
                    msg.set_metadata("ontology", "endAgents")
                    await self.send(msg)
                    print("Message sent!")
                    endReplyTemplate = Template()
                    endReplyTemplate.set_metadata("performative", "confirm")
                    endReplyTemplate.set_metadata("ontology", "end")
                    self.agent.add_behaviour(
                        behaviour=SenderAgent.WaitForDataEnd(),
                        template=endReplyTemplate
                    )
            # stop agent from behaviour
            print("Sender")
            await self.agent.stop()
    class WaitForData(OneShotBehaviour):
        async def run(self):
            answer = await self.receive(timeout=30)
            if answer:
                print('Message has arrived!')
            else:
                print('Data did not arrived, 30 seconds passed :(')
                print('Byeee')
    class WaitForDataInfo(OneShotBehaviour):
        async def run(self):
            answer = await self.receive(timeout=30)
            if answer:
                print('Message has arrived!')
            else:
                print('Data did not arrived, 30 seconds passed :(')
                print('Byeee')
    class WaitForDataPerson(OneShotBehaviour):
        async def run(self):
            answer = await self.receive(timeout=30)
            if answer:
                print('Message has arrived!')
            else:
                print('Data did not arrived, 30 seconds passed :(')
                print('Byeee')
    class WaitForDataCreateFile(OneShotBehaviour):
        async def run(self):
            answer = await self.receive(timeout=30)
            if answer:
                print('Message has arrived!')
            else:
                print('Data did not arrived, 30 seconds passed :(')
                print('Byeee')
    class WaitForDataEnd(OneShotBehaviour):
        async def run(self):
            answer = await self.receive(timeout=30)
            if answer:
                print('Message has arrived!')
            else:
                print('Data did not arrived, 30 seconds passed :(')
                print('Byeee')

    async def setup(self):
        print("Agent "+str(self.jid)+ " started")
        b = self.InformBehav()
        self.add_behaviour(b)

class ReceiverAgent(Agent):
    class TimeBehav(CyclicBehaviour):
         async def run(self):
            terminate = True
            while(terminate):
                print("EndAgentsBehav running")

                msg = await self.receive(timeout=10) # wait for a message for 10 seconds
                if msg:
                    print("Message received with content: {}".format(msg.body))
                    replyMsg = Message(to=data['spade_chatbot_sender']['username'])     # Instantiate the message
                    replyMsg.set_metadata("performative", "inform")
                    replyMsg.set_metadata("ontology", "time")
                    # Get time
                    replyMsg.body(strftime("Today is %d %B, %Y, it is %A and it is %H:%M:%S", gmtime()))
                    await self.send(replyMsg)
                else:
                    print("Did not received any message after 10 seconds")
            print("Receiver")
            # stop agent from behaviour
            await self.agent.stop()
    class PersonInfoBehav(CyclicBehaviour):
         async def run(self):
            terminate = True
            while(terminate):
                print("EndAgentsBehav running")

                msg = await self.receive(timeout=10) # wait for a message for 10 seconds
                if msg:
                    print("Message received with content: {}".format(msg.body))
                    
                    myString = msg.body.split("Tell me about ")[1]
                    s = myString.replace(" ", "_")
                    print("Sale: " + s)
                    page = requests.get('https://es.wikipedia.org/wiki/' + s)
                    html_soup = BeautifulSoup(page.content, 'html.parser')

                    panel = html_soup.find('div',{'id' : 'mw-content-text'})
                    parrafo = panel.find('p').text

                    replyMsg = Message(to=data['spade_chatbot_sender']['username'])     # Instantiate the message
                    replyMsg.set_metadata("performative", "inform")
                    replyMsg.set_metadata("ontology", "personInfo")
                    
                    replyMsg.body(parrafo)
                    await self.send(replyMsg)   
                else:
                    print("Did not received any message after 10 seconds")
            print("Receiver")
            # stop agent from behaviour
            await self.agent.stop()
    class CreateFileBehav(CyclicBehaviour):
         async def run(self):
            terminate = True
            while(terminate):
                print("CreateFileBehav running")

                msg = await self.receive(timeout=10) # wait for a message for 10 seconds
                if msg:
                    print("Message received with content: {}".format(msg.body))
                    
                    s = msg.body.split("Create file ")[1]
                    print(s)
                    f = open(s, "x")
                    f.close()
                    replyMsg = Message(to=data['spade_chatbot_sender']['username'])     # Instantiate the message
                    replyMsg.set_metadata("performative", "confirm")
                    replyMsg.set_metadata("ontology", "createFile")
                    await self.send(replyMsg)   
                else:
                    print("Did not received any message after 10 seconds")
            print("Receiver")
            # stop agent from behaviour
            await self.agent.stop()
    class EndAgentsBehav(CyclicBehaviour):
        async def run(self):
            terminate = True
            while(terminate):
                print("EndAgentsBehav running")

                msg = await self.receive(timeout=10) # wait for a message for 10 seconds
                if msg:
                    replyMsg = Message(to=data['spade_chatbot_sender']['username'])     # Instantiate the message
                    replyMsg.set_metadata("performative", "confirm")
                    replyMsg.set_metadata("ontology", "end")
                    await self.send(replyMsg)
                    self.kill()
                else:
                    print("Did not received any message after 10 seconds")
            print("Receiver")
            # stop agent from behaviour
            await self.agent.stop()

    async def setup(self):
        print("Behavs started")
        time = self.TimeBehav()
        person = self.PersonInfoBehav()
        create = self.CreateFileBehav()
        end = self.EndAgentsBehav()

        timeTemplate = Template()
        personInfoTemplate = Template()
        createFileTemplate = Template()
        endAgentsTemplate = Template()

        # Msg templates
        # Performative to make consistent with FIPA-ACL
        # Ontology to different functionalities
        timeTemplate.set_metadata("performative", "query")
        timeTemplate.set_metadata("ontology", "time")
        
        personInfoTemplate.set_metadata("performative", "query")
        personInfoTemplate.set_metadata("ontology", "personInfo")
        
        createFileTemplate.set_metadata("performative", "request")
        createFileTemplate.set_metadata("ontology", "createFile")

        endAgentsTemplate.set_metadata("performative", "request")
        endAgentsTemplate.set_metadata("ontology", "endAgents")

        # Adding the Behaviour with the template will filter all the msg
        self.add_behaviour(time, timeTemplate)
        self.add_behaviour(person, personInfoTemplate)
        self.add_behaviour(create, createFileTemplate)
        self.add_behaviour(end, endAgentsTemplate)



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