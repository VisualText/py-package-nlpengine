import ctypes
import os

path_to_dll = os.path.join(os.path.dirname(__file__), 'x64', 'NLP++.dll')
dll = ctypes.cdll.LoadLibrary(path_to_dll)
dll.setWorkingFolder.argtypes = [ctypes.c_char_p] 
dll.analyze.argtypes = [ctypes.c_char_p, ctypes.c_char_p] 
dll.analyze.restype = ctypes.c_char_p

default_working_folder = os.path.dirname(__file__)

def set_working_folder(working_folder = None):
  default_working_folder = working_folder
  if working_folder is None:
    dll.setWorkingFolder(default_working_folder.encode('utf-8'))
  else:
    dll.setWorkingFolder(working_folder.encode('utf-8'))

def analyze(str, parser = None, ):
  return dll.analyze(parser.encode('utf-8'), str.encode('utf-8')).decode('utf-8')