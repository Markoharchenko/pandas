class Mapmanager():
    def __init__(self, loader, render):
        self.loader = loader
        self.render = render
        self.model = "models/box"
        self.texture = "maps/noise.rgb"
        self.color = (0.2, 1, 0.35, 1)
    def startNew(self):
        self.land = self.render.attachNewNode("Land")
    
    def addBlock(self, position):
        block = self.loader.loadModel(self.model)
        block.setTexture(self.loader.loadTexture(self.texture))
        block.setPos(position)
        block.setScale(1)
        block.setColor(self.color)
        block.reparentTo(self.land)