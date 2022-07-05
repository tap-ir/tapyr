#!/usr/bin/python3 -i
#pytapir is a python client for RESTruct

import os
import requests
import json
import time 
import urllib 
import datetime 

class Attributes():
 def __init__(self, attributes):
   for name, value in attributes.items():
     if type(value) == dict:
       self.__dict__[name]  = Attributes(value)
     else:
       self.__dict__[name] = value
  
 def __repr__(self):
   return str(self.__dict__)

 def value(self):
   return self.__dict__

class ChildInfo():
  def __init__(self, id, name, has_children):
    self.id = id
    self.name = name
    self.has_children = has_children

  def __repr__(self):
    return str(self.__dict__)

class Node(json.JSONEncoder):
  def __init__(self, server, values):
    value = Attributes(values["attributes"]).value() 
    self.__dict__ = value
    self.__value = value
    self.id = values["id"]
    self.path = values["path"]
    self.server = server
    self.__name = values["name"] 
    self.children = []
    
    try:
      for child in values["children"]:
        self.children.append(ChildInfo(child["id"], child["name"], child["has_children"]))
    except Exception as e:
      pass
    self.children_name = []#keep for compatibility 
    for child in self.children:
      self.children_name.append(child.name)

  def default(self, obj):
    return obj.id

  def value(self):
    return self.__value

  def name(self):
    return self.__name

  def child(self, name):
    for child in self.children: 
      if name == child.name:
        return self.server.node_by_id(child.id)

  def __iter__(self):
    for name in self.children_name:
      yield self.child(name)

  def __repr__(self):
    return str(self.__dict__) 

class Tapir():
  def __init__(self, address = None, api_key = None, tls=False):
    if address == None:
      address = os.getenv('TAPIR_ADDRESS')
      if address == None:
        address = "127.0.0.1:3583"
    if api_key == None:
      api_key = os.getenv('TAPIR_KEY')
      if api_key == None:
        api_key = "key"
    self.ip, self.port = address.split(":")
    self.key = api_key
    self.requests = requests.Session()
    self.requests.headers.update({"x-api-key" : api_key})
    if tls:
      self.requests.verify = False
      self.base_url = "https://" + self.ip + ":" + self.port + "/api"
    else:
      self.base_url = "http://" + self.ip + ":" + self.port + "/api"

  def attribute_path(self, node, attribute):
    return { "node_id" : node.id, "attribute_name" : attribute }

  def attribute_path_from_id(self, id, attribute):
    return { "node_id" : id, "attribute_name" : attribute }
  
  def node_attributes_json(self, path):
    url = self.base_url + path
    response = self.requests.get(url)
    if response.ok:
      return response.content.decode('UTF-8')
    return None

  def node_attributes(self, path):
    url = self.base_url + path 
    response = self.requests.get(url)
    if response.ok:
      return json.loads(response.content.decode('UTF-8'))
    return None

  def node(self, path):
    attributes = self.node_attributes(path)
    if attributes:
      attributes["path"] = path
      return Node(self, attributes)
    return None

  def node_attributes_by_id(self, node_id, name, path, attributes, children):
    url = self.base_url + "/node"
    response = self.requests.post(url, json={"node_id" : node_id, "option" : {"name" : name, "path" : path,
                                  "attributes" : attributes, "children" : children}})
    if response.ok:
      return json.loads(response.content.decode('UTF-8'))
    return None

  def node_by_id(self, node_id, name=True, path=False, attributes=True, children=True):
   attributes = self.node_attributes_by_id(node_id, name, path, attributes, children)
   if attributes:
     return Node(self, attributes) #attributes path is null
   return None

  def nodes_attributes_by_id(self, nodes_id, name, path, attributes, children):
    url = self.base_url + "/nodes"
    response = self.requests.post(url, json={"nodes_id" : nodes_id, "option" : {"name" : name, "path" : path, 
                                             "attributes" : attributes, "children" : children}})
    if response.ok:
      return json.loads(response.content.decode('UTF-8'))
    return None

  def nodes_by_id(self, nodes_id, name=False, path=False, attributes=True, children=False):
    nodes_attributes = self.nodes_attributes_by_id(nodes_id, name, path, attributes, children)
    if nodes_attributes:
      nodes = []
      for attr in nodes_attributes:
        node = Node(self, attr) 
        nodes += (node,)
      return nodes
    return None

  def path(self, node_id):
    url = self.base_url + "/path"
    response = self.requests.post(url, data=json.dumps(node_id))
    if response.ok:
      return response.content.decode('UTF-8')
    return None

  def add_attribute(self, node_id, name, value, descr = None):
    url = self.base_url + "/attribute"
    if descr:
      r = self.requests.post(url, json={'node_id' : node_id, 'name' : name, 'value' : value, 'description' : descr}) 
    else:
      r = self.requests.post(url, json={'node_id' : node_id, 'name' : name, 'value' : value}) 
    if r.ok:
      return True
    else:
      return False

  def schedule(self, plugin, arguments, relaunch = False):
    url = self.base_url + "/schedule"
    r = self.requests.post(url, json={'name' : plugin, 'arguments' : json.dumps(arguments), 'relaunch' : relaunch })
    if r.ok:
      return json.loads(r.content.decode('UTF-8')) 
    else:
      return None 

  #this block until all task are finished, this block the entire server so must be used for debug purpose only
  def join(self):
    url = self.base_url + "/join"
    r = self.requests.post(url)
    if r.ok:
      return True
    return False

  #this block until a result is found this must be use for debug purpose only !
  def run(self, plugin, arguments, relaunch = False):
    url = self.base_url + "/run"
    r = self.requests.post(url, json={'name' : plugin, 'arguments' : json.dumps(arguments), 'relaunch' : relaunch})
    if r.ok:
       return json.loads(r.content.decode('UTF-8')) 
    else:
      return None

  def task_count(self):
    url = self.base_url + "/task_count"
    r = self.requests.post(url)
    if r.ok:
      return json.loads(r.content.decode('UTF-8')) 
    return 0 

  def task(self, task_id):
    url = self.base_url + "/task"
    r = self.requests.post(url, params={'task_id':task_id})
    if r.ok:
       return json.loads(r.content.decode('UTF-8'))
    else:
      return None

  def upload(self, file_path):
     file_name = file_path.split("/")[-1]
     try :
       f = open(file_path, 'rb')
     except :
       return None
     url = self.base_url + "/upload"
     data = f.read() 
     f.close()
     r = self.requests.post(url, params={'name' : file_name}, data=data, stream=True)
     if r.ok: 
       return json.loads(r.content.decode('UTF-8'))
     else:
       raise Exception(r.text)

  def delete(self, node_id):
    url = self.base_url + "/delete"
    response = self.requests.post(url, data=json.dumps(node_id))
    # if response.ok:
      # return response.content.decode('UTF-8')
    return None

  def clear(self):
    url = self.base_url + "/clear"
    response = self.requests.get(url)

  def download(self, node_id, file_path): 
     url = self.base_url + "/download"
     r = self.requests.post(url, json=node_id, stream=True)
     if r.ok:
       f = open(file_path, 'wb')
       for data in r.iter_content(1024*1024*10): 
          f.write(data)
       f.close()
     else:
       raise Exception(r.text)
    
  def read_all(self, node_id):
     url = self.base_url + "/download"
     r = self.requests.post(url, json=node_id, stream=True)
     if r.ok:
       buff = b""
       for data in r.iter_content(1024*1024*10): 
          buff += data
       return buff
     else:
       raise Exception(r.text)

  def read(self, node_id, size, offset = 0):
     url = self.base_url + "/read"
     r = self.requests.post(url, json={'node_id' : node_id, 'offset': offset, 'size': size}, stream=True)
     if r.ok:
       buff = bytearray()
       for data in r.iter_content(1024*1024): 
          buff.extend(data)
       return buff
     else:
       raise Exception(r.text)

  def query(self, query, root = "/root"):
     url = self.base_url + "/query"
     r = self.requests.post(url, json={'query' : query, 'root' : root})
     if r.ok:
       return json.loads(r.content.decode('UTF-8'))
     else:
       raise Exception(r.text)

  def plugins(self):
     url = self.base_url + "/plugins"
     r = self.requests.get(url)
     if r.ok:
      return json.loads(r.content.decode('UTF-8'))
     return None

  def plugin(self, plugin_name):
     url = self.base_url + "/plugin/" + plugin_name 
     r = self.requests.get(url)
     if r.ok:
       return json.loads(r.content.decode('UTF-8'))
     return None

  def save(self, file_name):
    url = self.base_url + "/save"
    save_file = { "file_name" : file_name }
    r = self.requests.post(url, json = save_file)
    if r.ok:
      return True
    return False

  def load(self, file_name):
    url = self.base_url + "/load"
    load_file = { "file_name" : file_name  }
    r = self.requests.post(url, json = load_file)
    if r.ok:
      return True
    return False

  #XXX deprecated use directly the magic plugins
  def scan(self, plugins_datatypes = None):
     if plugins_datatypes:
       url = self.base_url + "/scan_config"
       r = self.requests.post(url, json=plugins_datatypes)
     else:
       url = self.base_url + "/scan"
       r = self.requests.post(url)
     if r.ok:
       return json.loads(r.content.decode('UTF-8'))
     return None

  def node_count(self):
     url = self.base_url + "/node_count"
     r = self.requests.get(url)
     if r.ok:
      return json.loads(r.content.decode('UTF-8'))
     return None

  def attribute_count(self):
     url = self.base_url + "/attribute_count"
     r = self.requests.get(url)
     if r.ok:
      return json.loads(r.content.decode('UTF-8'))
     return None

  #After & Before must follow rfc3339
  def timeline(self, after, before, name=False, path=False, attributes=False, children=False):
    url = self.base_url + "/timeline"
    r = self.requests.post(url, json={'after' : after, 'before' : before, 'option' : {"path" : path, "name" : name, "attributes": attributes, "children" : children}})
    if r.ok:
      return json.loads(r.content.decode('UTF-8'))
    else:
      raise Exception(r.text)

if __name__ == "__main__":
  try :
    session = Tapir("127.0.0.1", "3583")
    root = session.node("/root")
  except Exception as e:
    print("Error: ", e)
