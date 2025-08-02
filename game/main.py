from direct.showbase.ShowBase import ShowBase
from panda3d.core import DirectionalLight, Vec3

class Game(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        self.model = loader.loadModel("models/environment")
        self.model.reparentTo(render)
        self.model.setScale(0.1)
        self.model.setPos(-2, 42, -3)
        self.camera.setPos(0, -50, 10)
        self.camera.lookAt(self.model)

        light = DirectionalLight('light')
        light.setDirection(Vec3(0, 8, -2))
        render.setLight(render.attachNewNode(light))


game = Game()
game.run()