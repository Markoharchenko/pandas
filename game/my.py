from panda3d.core import *
from panda3d.bullet import *
from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from panda3d.core import WindowProperties
import sys
import random


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

        # Create grid of blocks instead of single platform
        self.create_block_grid()

        # Input keys
        self.keys = {"w": False, "s": False, "a": False, "d": False, "space": False}
        for key in self.keys:
            self.accept(key, self.set_key, [key, True])
            self.accept(f"{key}-up", self.set_key, [key, False])
        self.accept("escape", sys.exit)

        # Update loop
        self.taskMgr.add(self.update, "update")

    def set_key(self, key, value):
        self.keys[key] = value

    def center_mouse(self):
        size = self.win.getProperties().getSize()
        self.win.movePointer(0, int(size.x / 2), int(size.y / 2))

    def create_player(self):
        shape = BulletCapsuleShape(0.4, 1.0, ZUp)
        self.player_node = BulletCharacterControllerNode(shape, 0.4, 'Player')
        self.player_np = render.attachNewNode(self.player_node)
        self.player_np.setPos(0, 0, 3)  # Start higher to avoid falling through blocks
        self.physics_world.attachCharacter(self.player_node)

        self.camera.reparentTo(self.player_np)
        self.camera.setZ(1.5)

        self.heading = 0
        self.pitch = 0
        self.mouse_sensitivity = 0.2

    def create_block(self, x, y, z):
        block_size = 1.5  # Increased size for hitbox
        half_size = block_size / 2
        
        # Create collision shape
        shape = BulletBoxShape(Vec3(half_size, half_size, half_size))
        node = BulletRigidBodyNode(f'Block_{x}_{y}')
        node.addShape(shape)
        node.setMass(0)  # Static object
        
        # Position the block
        np = render.attachNewNode(node)
        np.setPos(x, y, z)
        self.physics_world.attachRigidBody(node)
        
        # Create visual representation
        visual = loader.loadModel("models/box")
        visual.setScale(block_size)
        
        # Random color for variety
        r = random.random()
        g = random.random()
        b = random.random()
        visual.setColor(r, g, b, 1)
        
        visual.reparentTo(np)
        return np

    def create_block_grid(self):
        grid_size = 10  # 10x10 grid
        spacing = 1.6  # Adjusted spacing to accommodate larger blocks
        
        for x in range(-grid_size//2, grid_size//2):
            for y in range(-grid_size//2, grid_size//2):
                # Create blocks with elevation changes
                height = random.choice([0, 0, 0, 0.5, 1.0])  # Mostly flat with some variation
                self.create_block(x * spacing, y * spacing, height)

        # Create a solid area under spawn point
        for x in range(-1, 2):
            for y in range(-1, 2):
                self.create_block(x * spacing, y * spacing, 0)

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

        walk_dir = quat.xform(walk_dir)

        if walk_dir.lengthSquared() > 0:
            walk_dir.normalize()
            walk_dir *= 5.0
        else:
            walk_dir = Vec3(0, 0, 0)

        self.player_node.setLinearMovement(walk_dir, is_local=False)

        # Jump
        if self.keys["space"] and self.player_node.isOnGround():
            self.player_node.doJump()

        # Physics step
        self.physics_world.doPhysics(dt, 10, 1.0 / 300.0)

        return Task.cont


app = MinecraftPhysics()
app.run()
