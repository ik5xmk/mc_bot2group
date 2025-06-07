# mc_bot2group
Code to manage receiving and sending messages on MeshCom groups with a telegram bot.<br>

The solution involves a Linux system (for example a raspberry or a virtual machine also in the cloud) that communicates with a telegram bot and with a meshcom node, via UDP. See the commands **--extudp and --extudpip** of the meshcom nodes.<br>

This code works exclusively with groups (linked to the MCC of your country, so for example for Italy the 222xx groups) and that have been configured within the lora meshcom node. This means that you can send a message to any group that begins with 222 (see the configuration in the code) in the meshcom network but you will only be able to receive the 222xx groups that have been configured in the lora node. At the moment up to 6 groups and only numbers up to 5 digits.<br>

It is a very simple code, the bot accepts a single command: **/nnnnn your text message**<br>Un esempio: /222 Ciao a tutti!

The message will arrive from telegram to your node and will exit from it indicating the callsign of the node itself as the source. In this way everyone will be free to have their own bot and manage their own groups. It is an aid, a convenience, in addition to what is already present in the meshcom network, namely the management via web interface (from the node) of messages and the mobile application. For further information, refer to the official website of the MeshCom project.<br>

The communication between the code (in python) and telegram and the lora node is via IP with **UDP protocol**. Make sure, if you are not working in the same network, that you have correctly managed NAT and FIREWALL so that communication to and from the node is active. I remind you that **the lora meshcom node sends packets on the network through port 1799 and receives them on the same port**. For this reason you will also have a NAT of this type for forwarding messages from the code to the node (if located in different networks): 1798:1799<br>

The first step is to create a telegram bot, call @BotFather and follow the instructions. For help, search the internet, there are many guides. **You need to take note of the Token that will be assigned to your bot** and that you will have to insert in the code. **You also need the CHAT_ID**, so start your bot (/start) and type something. Open the browser and type this URL by inserting your token: https://api.telegram.org/bot__YOUR_TOKEN__/getUpdates The response will be a JSON packet. We need the CHAT_ID which will be a negative value (probably -100.....). This parameter must also be inserted in the code.<br>

Complete the code (CONFIGURATION section) with the IP of the remote lora node, the node callsign, the MCC prefix and the telegram bot data. Once done, run the code and it will listen locally to receive data from both the bot and the node. Go to the bot and try to send a message to a group (not privately), you will see it transit to the node and then out of it (check on the meshcom server). Have the meshcom network send a message to a group that you configured in your node, it will arrive on your node and then to the code to finally be sent to your telegram bot.<br>

The program reports the arrival of packets with non-compliant payload for messages (e.g. location packets) and they are ignored, as well as messages that have a different destination. This way of doing things can be used for future developments. Here is an example of what is received by the code, coming from the node and the telegram bot:<br>

![](https://github.com/ik5xmk/mc_bot2group/blob/main/mc_bot2group_01.jpg)
<br>
This is bot side:
<br>
![](https://github.com/ik5xmk/mc_bot2group/blob/main/mc_bot2group_02.jpg)
<br>
Other features in development:<br>
http://lora.dig-italia.it
