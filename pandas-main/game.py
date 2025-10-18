from direct.showbase.ShowBase import ShowBase

from mapmanager import Mapmanager

class Game(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        self.land = Mapmanager(self.loader, self.render)
        self.land.loadLand("land3.txt")
        base.camLens.setFov(90)


game = Game()
game.run()