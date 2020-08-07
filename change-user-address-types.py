from tkinter import *
from tkinter import messagebox
import requests
import configparser
import xmltodict
import pprint
import string

# configurations ##############################################################
config = configparser.ConfigParser()
config.read('config.ini')

apikey   = config['misc']['apikey']

# main program ################################################################
def main(*args):
    
    # open the file to write errors, assumes in the same directory
    error_file_object = open("error.txt","w")
    try: 
        error_file_object.write("Beginning of error file for change-user-address-types program.\n")
    except IOError:
        gui.msgbox(error_file_object, "Could not write the error file in the current path")
        error_file_object.close()
        return
    
    # user ID file
    user_file_name = gui.get_user()
    if user_file_name == "":
        error_file_object.write("Bad user file name: "+user_file_name)
        gui.msgbox(user_file_name, "Bad user file name")
        error_file_object.close()
        return
    # strip leading and trailing spaces
    user_file_name = user_file_name.strip()
    print("user file name = ", user_file_name)
    gui.clear_user()
    
    # open the file to read, assumes in the same directory
    try: 
        with open(user_file_name, 'r') as file_object:
            user_ids_from_file = file_object.read().splitlines()
 #           print("Here are the lines in the file:", user_ids_from_file)
    except IOError:
        error_file_object.write("File name does not exist in the current path: "+user_file_name)
        gui.msgbox(user_file_name, "This file name does not exist in the current path")
        error_file_object.close()
        return
     
    
    zcount=0
    for z in user_ids_from_file:
        print("user", zcount, ":", z)
        user = z
        zcount = zcount + 1
        #if this is a blank line in the file, just skip it
        if user == "":
    #       gui.msgbox(user, "Bad user ID.")
           continue
     
        # get user record
        r = requests.get("https://api-na.hosted.exlibrisgroup.com/almaws/v1/users/"+user+"?user_id_type=all_unique&status=ACTIVE&apikey="+apikey)
        
        # check for errors
        errors_exist = check_errors(r)
        if errors_exist[0] == True:
            error = errors_exist[1]
            print("error was:", error)
            if error.startswith("API-key not defined"):
                print("problem with API Key, write this to an error file\n")
                error_file_object.write("Problem with API Key: "+apikey)
                gui.msgbox(user, error)
                error_file_object.close()
                return
            if "not found" in error:
                print("There was an error with user",user,"\n")
            # not sure what other errors we might find here so check this    
            error_file_object.write(error+"\n")
 
    #        gui.msgbox(user, error)
            continue
        
        # parse user record. 
        original_user_xml = r.text
     #   print(original_user_xml, "\n")
        user_dict = xmltodict.parse(r.text,dict_constructor=dict)
     #   print("all user_dict before change", user_dict)
        primaryID = user_dict['user']['primary_id']
        firstname = user_dict['user']['first_name']
        lastname = user_dict['user']['last_name']
        contact_info_base = user_dict['user']['contact_info']
        
        # keep track if there is nothing to update in this record so we don't write when we don't need to
        nothing_to_update = True
        
        if contact_info_base == None:
            print("there was no contact info in this one\n")
     #       gui.msgbox("all okay","No user contact info to update in this record")
        else:
            print("there is contact info here\n")
            addresses_base = user_dict['user']['contact_info']['addresses']
            if addresses_base == None:
                print("there was no addresses info in this one\n")
     #           gui.msgbox("all okay","No user addresses info to update in this record")
            else:
                print("there is addresses info here\n")
                print("before user_dict change, eachaddressbase= ",user_dict['user']['contact_info']['addresses']['address'])
                eachaddressbase = user_dict['user']['contact_info']['addresses']['address']
            
                # if eachaddressbase is one address, the type will be dict, if it is several, the type will be a list
                if type(eachaddressbase) == dict:
                    print("only one address in this record\n")
                    new_user_dict_addresses = {}
                    
                    # only update the preferred address?
                    preferred_address = eachaddressbase['@preferred']
        #            print("preferred address:", preferred_address)
                    if (preferred_address == "true"):
                       print("this address is the preferred one\n")
                    else:
                       print("this address is not the preferred one\n")
                       
                    # COPY THIS SECTION FOR MULTIPLE ADDRESSES   
                      
                    print("the address type text is: ",eachaddressbase['address_types'])
                    eachaddresstypesbase = eachaddressbase['address_types']
                             
                    # if this is one type of address, the type will be dict, if it is several, the type will be a list
                    if type(eachaddresstypesbase['address_type']) == dict:
                        print("only one address type in this record\n")
                        
                        if eachaddresstypesbase['address_type']['@desc'] == "Home":
                            print("this record already has a home address type - no changes needed\n")
          #                  add_home_address_type = {'@desc': 'Home', '#text': 'home'}
                        else:
                            # append the home checkbox here
                            print("this record needs the home address type added\n")
                            add_home_address_type = []
                            add_home_address_type.append(eachaddresstypesbase['address_type'])
                            new_address_type_text = {'@desc': 'Home', '#text': 'home'}
                            add_home_address_type.append(new_address_type_text)
                            nothing_to_update = False
                            print("new address type, originally one address & address type:", add_home_address_type, "\n")
         
                    else:
                        print("there is more than one address type in this record\n")
                        add_home_address_type = []
                        home_address = False
                        ind_address_type_base = eachaddresstypesbase['address_type']
                        print("individual address type base: ",ind_address_type_base)
                        # first determine if any of the address types are home
                        count = 0
                        for k in ind_address_type_base:
                            print(f"user address type #{count}")
                            count = count + 1
                            type_of_address = k['@desc']
                            print("The address type is: ",type_of_address)
                            if (type_of_address == "Home"):
                                print("this record already has a home address type - no changes needed\n")
                                add_home_address_type = eachaddresstypesbase
                                home_address = True
                                break 
                        print("we left the loop\n")
                        if home_address == False:
                            # append the home checkbox here
                            print("this record needs the home address type added\n")
                            add_home_address_type = eachaddresstypesbase['address_type']
     #                       add_home_address_type.append(eachaddresstypesbase['address_type'])
                            new_address_type_text = {'@desc': 'Home', '#text': 'home'}
                            add_home_address_type.append(new_address_type_text)
                            nothing_to_update = False
                            print("new address type, originally one address and multiple address types:", add_home_address_type, "\n")
                                
                # END OF SECTION TO COPY
                                                            
                else:         #this record has several addresses and is a list
                    print("more than one address in this record\n")
                    new_user_dict_addresses = []
                    home_address = False
                    # eachaddressbase is currently set to user_dict['user']['contact_info']['addresses']['address']
                    # addresses_base is currently set to user_dict['user']['contact_info']['addresses']
                                
                    # loop through addresses until we get to the preferred one and use that
                    # only update the preferred address
                    
                    # start with -1 on count so we get the right number for getting this record later                           
                    count_addresses = -1
                    for k in eachaddressbase:
                        count_addresses = count_addresses + 1
                        print(f"user address #{count_addresses}")
                        preferred_address = k['@preferred']
                        print("preferred address:", preferred_address)
                        #preferred address
                        if (preferred_address == "true"):
                            print("this address is the preferred one\n")
                            
            # COPIED FROM THE EARLIER SECTION
                            print("the address type text is: ",k['address_types'])
                            eachaddresstypesbase = k['address_types']
                             
                            # if this is one type of address, the type will be dict, if it is several, the type will be a list
                            if type(eachaddresstypesbase['address_type']) == dict:
                                print("only one address type in this record\n")
                        
                                if eachaddresstypesbase['address_type']['@desc'] == "Home":
                                    print("this preferred record already has a home address type - no changes needed\n")
                                    #add_home_address_type = {'@desc': 'Home', '#text': 'home'}
                                else:
                                    # append the home checkbox here
                                    print("this preferred record needs the home address type added\n")
                                    add_home_address_type = []
                                    add_home_address_type.append(eachaddresstypesbase['address_type'])
                                    new_address_type_text = {'@desc': 'Home', '#text': 'home'}
                                    add_home_address_type.append(new_address_type_text)
                                    nothing_to_update = False
                                    print("new address type, originally more than one address & address type:", add_home_address_type, "\n")
                                # we got everything we needed - leave the loop    
                                break
                            
                            else: #more than one address type in the preferred record
                                print("there is more than one address type in this preferred record\n")
                                add_home_address_type = []
                                home_address = False
                                ind_address_type_base = eachaddresstypesbase['address_type']
                                print("individual address type base: ",ind_address_type_base)
                                # first determine if any of the address types are home
                                count = 0
                                for q in ind_address_type_base:
                                    print(f"user address type #{count}")
                                    count = count + 1
                                    type_of_address = q['@desc']
                                    print("The address type is: ",type_of_address)
                                    if (type_of_address == "Home"):
                                       print("this record already has a home address type in the preferred address - no changes needed\n")
                                       add_home_address_type = eachaddresstypesbase
                                       home_address = True
                                       break 
                                print("we left the ind_address_type_base loop\n")
                                
                                if home_address == False:
                                # append the home checkbox here
                                    print("this record needs the home address type added\n")
                                    add_home_address_type = eachaddresstypesbase['address_type']
            #                       add_home_address_type.append(eachaddresstypesbase['address_type'])
                                    new_address_type_text = {'@desc': 'Home', '#text': 'home'}
                                    add_home_address_type.append(new_address_type_text)
                                    nothing_to_update = False
                                    print("new address type, originally multiple addresses and multiple address types:", add_home_address_type, "\n")
                                #break out of outside loop as well    
                                break
                        else:
                            print("this address is not the preferred one, keep going\n")
                                                    
                    print("we left the eachaddressbase loop\n")
                    
                                
        
    # put the code here to copy the new address info into the XML
               
            if nothing_to_update == False:
               print("We have something to update in the record\n")
               if type(eachaddressbase) == dict:
                   print("record had one address\n")
                   user_dict['user']['contact_info']['addresses']['address']['address_types']['address_type']= add_home_address_type
               else:
                   print("record has multiple addresses\n")
                   print(user_dict['user']['contact_info']['addresses']['address'][count_addresses],"\n")
                   user_dict['user']['contact_info']['addresses']['address'][count_addresses]['address_types']['address_type']= add_home_address_type
                   
         #          user_dict['user']['contact_info']['addresses']['address']['address_types']['address_type']= add_home_address_type
                   
               print("after user_dict change here is the address part, ",user_dict['user']['contact_info']['addresses'],"\n")
                   
                 
               # remake the XML
               new_user_xml = xmltodict.unparse(user_dict)
               #print(new_user_xml)
      
               # comment out the next line if you don't want to save anything to the user record
               r = putXML("https://api-na.hosted.exlibrisgroup.com/almaws/v1/users/"+user+"?user_id_type=all_unique&apikey="+apikey, new_user_xml)
            
               # check for errors
               errors_exist = check_errors(r)
               if errors_exist[0] == True:
                   print("there was an error in the putXML for user =", user)
                   error = errors_exist[1]
                   error_file_object.write("User "+user+" had this error: "+error+"\n")
     #              gui.msgbox(user, error)
                   continue
            
               # finish
               gui.update_status_success(primaryID, firstname, lastname, "UPDATED")
            else:
               gui.update_status_success(primaryID, firstname, lastname, "RETAINED")
    #end of text loop here
    print("we are done processing the file\n")
    error_file_object.write("The program has finished processing the file.")
    error_file_object.close()
# end of main here
         
 
            
# functions ###################################################################

def putXML(url, xml):
    headers = {'Content-Type': 'application/xml', 'charset':'UTF-8'}
    r = requests.put(url, data=xml.encode('utf-8'), headers=headers)
    return r

def check_errors(r):
    if r.status_code != 200:
        errors = xmltodict.parse(r.text)
        error = errors['web_service_result']['errorList']['error']['errorMessage']
        return True, error
    else: 
        return False, "OK"
            
# gui #########################################################################
class gui:
    def __init__(self, master):
        self.master = master
        master.title("CSUN change user address types")
        master.resizable(0, 0)
        master.minsize(width=600, height=100)
        master.iconbitmap("csunalone.ico")

        logo = PhotoImage(file="csunalone.png")
        self.logo = Label(image=logo)
        self.logo.image = logo
        self.logo.pack()

        self.status_title = Label(height=1, text="Enter file name of IDs to begin.", font="Consolas 12 italic")
        self.status_title.pack(fill="both", side="top")

        self.status_added = Label(height=1, text="READY", font="Consolas 12 bold", fg="green")
        self.status_added.pack(fill="both", side="top")

        self.user_entry_field = Entry(font="Consolas 16")
        self.user_entry_field.focus()
        self.user_entry_field.bind('<Key-Return>', main)
        self.user_entry_field.pack(fill="both", side="top")
        
        self.scan_button = Button(text="SCAN", font="Arial 16", command=main)
        self.scan_button.pack(fill="both", side="top")
        
    def msgbox(self, title, msg):
        messagebox.showerror("Attention", msg)
        gui.update_status_failure(title, msg)
        
    def get_user(self):
        user = self.user_entry_field.get()
        user = user.replace(" ", "")
        return user
        
    def clear_user(self):
        self.user_entry_field.delete(0, END)
        self.status_title.config(text="")
        self.status_added.config(text="")
        
    def update_status_success(self, primaryID, first, last, action):
        self.status_title.config(text=primaryID+" "+first+" "+last)
        self.status_added.config(text="ADDRESSES SUCCESSFULLY "+action+" IN USER DATABASE", fg="green")
        
    def update_status_failure(self, title, msg):
        self.status_title.config(text=title)
        self.status_added.config(text=msg, fg="red")
        
root = Tk()
gui = gui(root)
root.mainloop()
