# mc_bot2group
Code to manage receiving and sending messages on MeshCom groups with a telegram bot.<br>

The solution involves a Linux system (for example a raspberry or a virtual machine also in the cloud) that communicates with a telegram bot and with a meshcom node, via UDP. See the commands --extudp and --extudpip of the meshcom nodes.<br>

This code works exclusively with groups (linked to the MCC of your country, so for example for Italy the 222xx groups) and that have been configured within the lora meshcom node. This means that you can send a message to any group that begins with 222 (see the configuration in the code) in the meshcom network but you will only be able to receive the 222xx groups that have been configured in the lora node. At the moment up to 6 groups and only numbers up to 5 digits.<br>

It is a very simple code, the bot accepts a single command: **/nnnnn your text message**<br>Un esempio: /222 Ciao a tutti!

The message will arrive from telegram to your node and will exit from it indicating the callsign of the node itself as the source. In this way everyone will be free to have their own bot and manage their own groups. It is an aid, a convenience, in addition to what is already present in the meshcom network, namely the management via web interface (from the node) of messages and the mobile application. For further information, refer to the official website of the MeshCom project.<br>
