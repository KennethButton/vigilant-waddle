#!/usr/bin/python3.6

import json
import time

from threading import Timer
import datetime
from datetime import date

import re


import tornado.web
import tornado.httpserver
import tornado.escape
import tornado.ioloop

from tornado import gen
from tornado.concurrent import run_on_executor
from concurrent.futures import ThreadPoolExecutor

class Statistics(tornado.web.RequestHandler):

    exec_assets = ThreadPoolExecutor(max_workers=1)
    
    @gen.coroutine
    
    def get(self):
        total_shocks = 0
        for i in assets:
            try:
                for j in assets[i]['roles']:
                    for k in assets[i]['roles'][j]:
                        total_shocks += int(assets[i]['roles'][j][k]['shocks'])
            except:
                pass
        self.write(f"Shocks: {total_shocks}")
        return

class Assets(tornado.web.RequestHandler):

    exec_assets = ThreadPoolExecutor(max_workers=2)

    @gen.coroutine
    def post(self,pass_elements):
    
        if pass_elements[-1] == "/":
            pass_elements = pass_elements[:-1]
        elements = pass_elements.split('/')

        len_elements = len(elements)

        try:
            content = json.loads(self.request.body.decode('utf-8'))
        except:
            self.write(json_error(f"Your JSON is not quite correct.  Try again."))
            return

        if len_elements == 0:
            self.write(json_error(f"You have to give us something!"))
            return
        
        get_uuid = elements[0]
        if re_uuid.match(get_uuid) == None:
            self.write(json_error(f"UUID does not match accepted format."))
            return
        
        if len_elements == 1:
            if get_uuid in assets:
                self.write(json_error(f"UUID already exists in system."))
                return
            if 'name' not in content:
                self.write(json_error(f"name component required for record creation."))
                return
            assets[get_uuid] = {}
            assets[get_uuid]['_name_'] = content['name']
            assets[get_uuid]['_start_date_'] = now_stamp()
            assets[get_uuid]['roles'] = {}
            self.set_status(301)
            return

        if len_elements == 2:
            self.write(json_error(f"This spot is not createable."))
            return

        if get_uuid not in assets:
            self.write(json_error(f"This UUID does not exist, please make it."))
            return
        
        if elements[1] != "roles":
            self.write(json_error(f"This path does not exist."))
            return

        if len_elements >= 5:
            self.write(json_error(f"Stop Yodeling!"))
            return

        add_role = elements[2]
        
        if add_role not in roles:
            self.write(json_error(f"{add_role} not a recognized role in this system."))
            return

        if len_elements == 3:
                
            role_next_id = roles[add_role]['next']
            roles[add_role]['next'] = increment_id(roles[add_role]['next'])

            if add_role not in assets[get_uuid]['roles']:
                assets[get_uuid]['roles'][add_role] = {}
            
            ## ADD SANITATION ...
            assets[get_uuid]['roles'][add_role][role_next_id] = {}
            assets[get_uuid]['roles'][add_role][role_next_id] = process_content(assets[get_uuid]['roles'][add_role][role_next_id],content)
            self.set_status(301)
            self.write({add_role:role_next_id})
            return

        asset_id = elements[3]

        if len_elements == 4:
            if asset_id not in assets[get_uuid]['roles'][add_role]:
                self.write(json_error(f"This asset doesn't exist for this role in UUID."))
                return
        assets[get_uuid]['roles'][add_role][asset_id] = process_content(assets[get_uuid]['roles'][add_role][asset_id],content)
        self.write(assets[get_uuid]['roles'][add_role][asset_id])                    
        return
        
    @gen.coroutine
    def get(self,pass_elements):
        
        if pass_elements[-1] == "/":
            pass_elements = pass_elements[:-1]
            
        elements = pass_elements.split('/')
        
        
        len_elements = len(elements)
        
        if len_elements == 0:
            return
        
        get_uuid = elements[0]
        if get_uuid not in assets:
            self.write(json_error(f"UUID does not exist. {get_uuid}"))
            return
        
        if len_elements == 1:
            if get_uuid in assets:
                self.write(display_tree(assets[get_uuid],"half"))
            return

        if 'roles' not in assets[get_uuid]:
            self.write(json_error("UUID does not possess roles."))
            return

        if len_elements == 2:
            self.write(display_tree(assets[get_uuid]['roles'],"half"))
            return
            
        get_roles = elements[2]
        
        if get_roles not in assets[get_uuid]['roles']:
            self.write(json_error("Role does not exist within that identity."))
            return
        
        dir_roles = assets[get_uuid]['roles'][get_roles]
        
        if len_elements == 3:
            self.write(display_tree(dir_roles,"half"))
            return

        get_asset = elements[3]

        if get_asset not in dir_roles:
            self.write(json_error("Role does not exist within that asset."))
            return
            
        dir_asset = dir_roles[get_asset]
        
        if len_elements == 4:
            self.write(display_tree(dir_asset,"full"))
            return
        
        self.write(json.error("You've fallen off the cliff!"))
        return
        
def process_content(db,delta):
    for key in delta:
        piece = delta[key]
        
        if re_field.match(piece) == False:
            continue

        if piece == "++":
            try:
                piece = str(int(db[key]) + 1)
            except:
                pass
        elif piece[0] == "+":
            try:
                value = int(piece[1:-1])
                piece = str(value + int(db[key]))
            except:
                pass
                
        if len(piece) > 30:
            piece = piece[0:60]
        db[key] = piece
    return db

def now_stamp():
    return datetime.datetime.now().replace(microsecond=0).isoformat(' ')
        
def display_tree(structure_d,view_d):
    base_asset = {}
    for s_key in structure_d:
        if type(structure_d[s_key]) == dict:
            if view_d == "full":
                base_asset[s_key] = structure_d[s_key]
            else:
                base_asset[s_key] = "true"
        else:
            base_asset[s_key] = structure_d[s_key]
    return(base_asset)
            
        
    

def json_error(error_message):
    return({'error':error_message})

def increment_id(inc_id):
    id_basics = inc_id.split("-")
    id_key    = id_basics[0]
    id_value  = int(id_basics[1])+1
    return(f"{id_key}-{id_value}")

def save_assets(pass_assets):
    print("Dumping Database.")
    nowtime = time.time()
    fh = open(f"assets.{nowtime}.json","w")
    fh.write(json.dumps(pass_assets))
    fh.close()
    Timer(43200,save_assets,[assets]).start()
    return True
        
if __name__ == "__main__":

    assets  = {}
    roles   = {}

    re_uuid  = re.compile('[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}$')
    re_field = re.compile("^[A-Za-z0-9 ./+-\\\*]+$")
    
    print("Reading Black Gazza Database.")

    with open("assets.json") as f_assets:
        assets = json.loads(f_assets.read())

    db_entries = len(assets.keys())
    print(f"{db_entries} records in database.")

    for id in assets:
        for db_roles in assets[id]['roles']:
            if db_roles not in roles:
                roles[db_roles] = {}
            if 'next' not in roles[db_roles]:
                roles[db_roles]['next'] = ""
            for role_id in assets[id]['roles'][db_roles]:
                if roles[db_roles]['next'] < role_id:
                    roles[db_roles]['next'] = role_id

    roles_entries = len(roles.keys())
    print(f"{roles_entries} role(s) identified.")        
    for i in roles.keys():
        roles[i]['next'] = increment_id(roles[i]['next'])
        print(f"[{i}] Next ID is {roles[i]['next']}")

    app = tornado.web.Application([
        (r"/identity/(.*)/?", Assets),
        (r"/stats/?", Statistics)
    ])

    server = tornado.httpserver.HTTPServer(app)
    
    web_port = 60000
    server.listen(web_port)
    print("Starting Server.")
    Timer(43200,save_assets,[assets]).start()
    
    tornado.ioloop.IOLoop.instance().start()

