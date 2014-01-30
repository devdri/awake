import json,shutil,os
class Config:
    def __init__(self, name="awake.json",default=False, rom=False):	
        self.default=default
        self.rom=rom
        if name is None:
            assert rom==False
            name="awake.json"
        if rom:
            name=name+".json"
        if not os.path.isfile(name):
            shutil.copy("awake/defaults.json",name)
        self.config=json.load(open(name))
    def get(self,keys):
        tmp=self.config
        try:
            for key in keys:
                tmp=tmp[key]
        except KeyError:
            assert self.default==False
            if self.rom:
                tmp=defaultromconfig.get(keys)
            else:
                tmp=defaultconfig.get(keys)
        return tmp
defaultconfig=Config("awake/defaults.json",True)
defaultromconfig=Config("awake/romdefaults",True,True)
