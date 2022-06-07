#!/usr/bin/python3 
import unittest
import os
import datetime

from pytapir import Tapir

session = Tapir("127.0.0.1", "3583")
root = session.node("/root")
path = os.getcwd() + "/../tapyr-test-data"

session.run("local", {"files" : [path], "mount_point" : root.id})

class RustructTest(unittest.TestCase):
  def setUp(self):
    self.session = Tapir("127.0.0.1", "3583")

  def test_error(self):
    self.assertEqual(self.session.node("/root/error"), None)
    self.assertEqual(self.session.node("/error"), None)

  def test_root_node(self):
    root = self.session.node("/root")
    self.assertEqual(root.name(), "root")
    self.assertEqual(root.id, {'index1' : 1, 'stamp': 0})
    self.assertEqual(root.children_name, ['test-data'])

  def test_root_by_id(self):
    root = self.session.node_by_id({'index1' : 1, 'stamp': 0})
    self.assertEqual(root.name(), "root")
    self.assertEqual(root.id, {'index1' : 1, 'stamp': 0})
    self.assertEqual(root.children_name, ['test-data'])

  def test_unicode_path(self):
    node = self.session.node("/root/test-data/exif/image2_unicode_é.jpg")
    self.assertEqual(node.name(), "image2_unicode_é.jpg")

  def test_1_upload(self):
    path = os.getcwd() + "/../test-data/exif/image1.jpg"
    result = self.session.upload(path)
    self.assertEqual(result, 161713)
    result = self.session.upload("./test-data/none")
    self.assertEqual(result, None)

  def test_exif_plugin_image1_node(self):
    image1 = self.session.node("/root/test-data/exif/image1.jpg")
    session.run("exif", {"files" : [ image1.id ]})
    image1 = self.session.node("/root/test-data/exif/image1.jpg")
    self.assertEqual(image1.name(), "image1.jpg")
    self.assertEqual(image1.exif.primary.date_time_digitized, '2008-10-22T16:28:39Z')
    self.assertEqual(image1.exif.thumbnail.y_resolution + image1.exif.thumbnail.x_resolution, 144.0)

  def test_unicode_child_node(self):
    root = self.session.node("/root/test-data")
    child = root.child('exif').child(u'image2_unicode_é.jpg')
    self.assertEqual(child.name(),u'image2_unicode_é.jpg')

  def test_run_hash_plugin(self):
    image1 = self.session.node("/root/test-data/exif/image1.jpg")
    res = self.session.run("hash", { "files" : [ image1.id ]})
    self.assertEqual('{}', res["result"])
    image1 = self.session.node("/root/test-data/exif/image1.jpg")
    self.assertEqual(image1.hash, '5d66eec547469a1817bda4abe35c801359b2bb55')

  #must test download too
  def test_readall(self):
    image1 = self.session.node("/root/test-data/exif/image1.jpg")
    data = self.session.read_all(image1.id)
    self.assertEqual(len(data), 161713)
    try:
      data = self.session.read_all("/root/exif/none")
    except Exception as e: #XXX now pytapir raise exception, check the exception result ?
      pass
      # self.assertEqual(data, None)

  def test_query_attribute_name(self):
    nodes = self.session.query("attribute.name == 'data'")
    self.assertEqual(len(nodes), 9)
  #self.assertEqual(nodes[0], "/root/exif/image1.jpg") #could be in any order

  def test_query_node_name(self):
    nodes = self.session.query("name == 'image1.jpg'")
    self.assertEqual(len(nodes), 1)

  def test_query_node_name_unicode(self):
    nodes = self.session.query(u"name == 'image2_unicode_é.jpg'")
    self.assertEqual(len(nodes), 1)

  def test_query_name_fixed(self):
    nodes = self.session.query("name == u'image1.jpg'")
    self.assertEqual(len(nodes), 1)

  def test_query_name_regexp(self):
    nodes = self.session.query("name == r'([^\s]+(\.(?i)(jpg|tiff))$)'")
    self.assertEqual(len(nodes), 2)

  def test_query_name_wildcard(self):
    nodes = self.session.query("name == w'*.jpg'")
    self.assertEqual(len(nodes), 2)
    nodes = self.session.query("name == w'image?.jpg'")
    self.assertEqual(len(nodes), 1)
    nodes = self.session.query("name == w'image?_*.jpg'")
    self.assertEqual(len(nodes), 1)

  def test_query_fuzzy(self):
    nodes = self.session.query("attribute.name == f'data'")
    self.assertEqual(len(nodes), 9)
    nodes = self.session.query("name == f'imag1.jpg'")
    self.assertEqual(len(nodes), 1)

  def test_query_or(self):
    nodes = self.session.query("name == 'image1.jpg' or name == w'image2*'")
    self.assertEqual(len(nodes), 2)
    nodes = self.session.query("(name == 'image1.jpg') or (name == w'image2*')")
    self.assertEqual(len(nodes), 2)

  def test_query_and(self):
    nodes = self.session.query("name == 'image1.jpg' and attribute.name == 'data'")
    self.assertEqual(len(nodes), 1)
    nodes = self.session.query("(name == 'image1.jpg') and (attribute.name == 'data')")
    self.assertEqual(len(nodes), 1)

  def test_query_data_binary(self):
    nodes = self.session.query("data == '\x7F\x45\x4C\x46'")
    self.assertEqual(len(nodes), 1)
    nodes = self.session.query("data == r'\x7F\x45\x4C\x46'")
    self.assertEqual(len(nodes), 1)

  def test_query_data_utf8(self):
    nodes = self.session.query("data == r'икра'")
    self.assertEqual(len(nodes), 1)
    nodes = self.session.query("data == 'икра'")
    self.assertEqual(len(nodes), 1)

  def test_query_line_utf8_utf16(self):
    nodes = self.session.query("data == t'икра'")
    self.assertEqual(len(nodes), 2)

  def test_scan_and_query_dot_attribute(self):
    for (node_id, plugin) in self.session.scan():
      session.run(plugin, {"files" : [node_id]})
    nodes = self.session.query("attribute.name == 'exif'")
    self.assertEqual(len(nodes), 2)
    nodes = self.session.query("attribute.name == 'exif.primary.model'")
    self.assertEqual(len(nodes), 2)
    nodes = self.session.query("attribute.name == w'exif.*.model'")
    self.assertEqual(len(nodes), 2)

if __name__ == '__main__':
    unittest.main(verbosity=2)
