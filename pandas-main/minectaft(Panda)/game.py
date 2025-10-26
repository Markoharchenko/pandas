from direct.showbase.ShowBase import ShowBase
from mapmanager import Mapmanager

class Game(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        self.land = Mapmanager(self.loader, self.render)
        base.camLens.setFov(90)

        self.land.startNew()
        self.land.addBlock((0, 10, 0))
        self.land.addBlock((10, 10, 0))
        self.land.addBlock((0, 10, 10))

game = Game()
game.run()

