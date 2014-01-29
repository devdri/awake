import json,shutil,os
class Config:
    def __init__(self, name="awake.json",default=False):	
        self.default=default
        if name is None:
            name="awake.json"
        if not os.path.isfile(name):
            shutil.copy("awake/defaults.json",name)
        self.config=json.load(open(name))
    def get(self,keys):
        tmp=self.config
        try:
            for key in keys:
                tmp=tmp[key]
        except KeyError:
            tmp=defaultconfig.get(keys)
        return tmp
class RomConfig:
    def __init__(self, name="blue",default=False):
        self.default=default
        if name is None:
            name="blue"
        name=name+".json"
        if not os.path.isfile(name):
            shutil.copy("awake/romdefaults.json",name)
        self.config=json.load(open(name))
    def get(self,keys):
        tmp=self.config
        try:
            for key in keys:
                tmp=tmp[key]
        except KeyError:
            tmp=defaultromconfig.get(keys)
        return tmp
defaultconfig=Config("awake.json",True)
defaultromconfig=RomConfig("awake/romdefaults.json",True)
