from panda3d.core import *
from panda3d.bullet import *
from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from panda3d.core import WindowProperties
import sys


class MinecraftPhysics(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        self.disableMouse()
        props = WindowProperties()
        props.setCursorHidden(True)
        self.win.requestProperties(props)
        self.center_mouse()

        # Bullet physics world
        self.physics_world = BulletWorld()
        self.physics_world.setGravity(Vec3(0, 0, -9.81))

        # Player setup
        self.create_player()

        # Create ground blocks
        self.block_model = loader.loadModel("models/box")
        self.block_model.setTexture(loader.loadTexture("models/maps/envir-ground.jpg"))
        self.create_ground_blocks()

        # Input keys
        self.keys = {"w": False, "s": False, "a": False, "d": False, "space": False}
        for key in self.keys:
            self.accept(key, self.set_key, [key, True])
            self.accept(f"{key}-up", self.set_key, [key, False])
        self.accept("escape", sys.exit)

        # Mouse click to place blocks
        self.accept("mouse1", self.place_block)

        # Create crosshair
        self.create_crosshair()

        # Update loop
        self.taskMgr.add(self.update, "update")

    def create_crosshair(self):
        """Create a simple crosshair in the center of the screen"""
        # Vertical line
        cm = CardMaker('crosshair_v')
        cm.setFrame(-0.008, 0.008, -0.04, 0.04)  # Width, height
        self.crosshair_v = self.aspect2d.attachNewNode(cm.generate())
        self.crosshair_v.setColor(1, 1, 1, 1)  # White color
        
        # Horizontal line
        cm = CardMaker('crosshair_h')
        cm.setFrame(-0.04, 0.04, -0.008, 0.008)  # Width, height
        self.crosshair_h = self.aspect2d.attachNewNode(cm.generate())
        self.crosshair_h.setColor(1, 1, 1, 1)  # White color

    def set_key(self, key, value):
        self.keys[key] = value

    def center_mouse(self):
        size = self.win.getProperties().getSize()
        self.win.movePointer(0, int(size.x / 2), int(size.y / 2))

    def create_player(self):
        shape = BulletCapsuleShape(0.4, 1.0, ZUp)
        self.player_node = BulletCharacterControllerNode(shape, 0.4, 'Player')
        self.player_np = render.attachNewNode(self.player_node)
        self.player_np.setPos(0, 0, 5)
        self.physics_world.attachCharacter(self.player_node)

        self.camera.reparentTo(self.player_np)
        self.camera.setZ(1.0)

        self.heading = 0
        self.pitch = 0
        self.mouse_sensitivity = 0.2

    def create_ground_blocks(self):
        block_size = 1.0
        grid_size = 10  # Number of blocks in each direction

        for x in range(-grid_size, grid_size):
            for y in range(-grid_size, grid_size):
                self.create_block(x * block_size, y * block_size, 0)

    def create_block(self, x, y, z):
        shape = BulletBoxShape(Vec3(0.5, 0.5, 0.5))  # Half size for the block
        node = BulletRigidBodyNode('Block')
        node.addShape(shape)
        node.setMass(0)  # Static block

        np = render.attachNewNode(node)
        np.setPos(x, y, z)
        self.physics_world.attachRigidBody(node)

        visual = self.block_model.copyTo(np)
        visual.setScale(1, 1, 1)
        visual.setTexture(loader.loadTexture("models/maps/envir-ground.jpg"))

    def place_block(self):
        # Get the player's position and direction
        player_pos = self.player_np.getPos()
        player_facing = self.camera.getQuat().getForward()  # Get the forward direction of the camera

        # Calculate the position to place the block
        block_pos = player_pos + player_facing * 2  # Place the block 2 units in front of the player

        # Create the block at the calculated position
        self.create_block(block_pos.x, block_pos.y, block_pos.z)

    def update(self, task):
        dt = globalClock.getDt()

        # Mouse look
        if self.mouseWatcherNode.hasMouse():
            md = self.win.getPointer(0)
            x = md.getX()
            y = md.getY()
            size = self.win.getProperties().getSize()
            cx = int(size.x / 2)
            cy = int(size.y / 2)

            dx = x - cx
            dy = y - cy

            self.heading -= dx * self.mouse_sensitivity
            self.pitch = max(-90, min(90, self.pitch - dy * self.mouse_sensitivity))
            self.player_np.setH(self.heading)
            self.camera.setP(self.pitch)

            self.center_mouse()

        # Movement
        walk_dir = Vec3(0, 0, 0)
        quat = self.player_np.getQuat()

        if self.keys["w"]:
            walk_dir += Vec3(0, 1, 0)
        if self.keys["s"]:
            walk_dir += Vec3(0, -1, 0)
        if self.keys["a"]:
            walk_dir += Vec3(-1, 0, 0)
        if self.keys["d"]:
            walk_dir += Vec3(1, 0, 0)

        walk_dir = quat.xform(walk_dir)  # Apply rotation
        walk_dir.setZ(0)  # Keep movement on the X-Y plane

        if walk_dir.lengthSquared() > 0:
            walk_dir.normalize()
            walk_dir *= 5.0

        self.player_node.setLinearMovement(walk_dir, is_local=False)

        # Jump
        if self.keys["space"] and self.player_node.isOnGround():
            self.player_node.doJump()

        # Physics step
        self.physics_world.doPhysics(dt, 10, 1.0 / 300.0)

        return Task.cont


app = MinecraftPhysics()
app.run()
