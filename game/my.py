from panda3d.core import *
from panda3d.bullet import *
from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from panda3d.core import KeyboardButton, WindowProperties
from direct.gui.DirectGui import DirectButton, DirectFrame
from direct.gui.OnscreenText import OnscreenText
import random, sys, json, os

SAVE_FILE = "world_save.json"#GJO0YT

class MinecraftClone(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        # 🔧 Вікно
        self.disableMouse()

        # Стани
        self.game_started = False
        self.is_dead = False

        # ⚙️ Bullet Physics (ініціалізуємо завчасно)
        self.physics_world = BulletWorld()
        self.physics_world.setGravity(Vec3(0, 0, -9.8))

        # 📦 Параметри світу
        self.blocks = []              # всі NodePath блоків (і базових, і динамічних)
        self.base_positions = set()   # координати базових блоків (щоб не зберігати/не дублювати їх)
        self.block_size = 1.5
        self.spacing = 1.6

        # 🎮 Рух і стрибок
        self.speed = 5
        self.jump_speed = 6
        self.velocity_z = 0.0
        self.is_jumping = False

        # 👣 Стояння на блоці
        self.eye_height = 1.8
        self.ground_snap_distance = 0.2

        # 💀 Смерть/відродження
        self.death_height = -10
        self.spawn_pos = Point3(0, 0, 10)

        # UI
        self.menu_ui = None
        self.respawn_ui = None

        # Звуки
        self.place_sound = loader.loadSfx("done.mp3")
        self.break_sound = loader.loadSfx("break.mp3")
        self.death_sound = loader.loadSfx("death.mp3")
        self.respawn_sound = loader.loadSfx("born.mp3")

        # Керування мишею спочатку для меню (показати курсор)
        self.show_cursor(True)

        # Створити меню
        self.create_main_menu()

        # Підписки на події
        self.accept("mouse3", self.place_block)
        self.accept("mouse1", self.break_block)
        self.accept("escape", self.on_escape)
        self.accept("p", self.save_world)  # збереження світу на P

        # Гарантоване автозбереження при закритті (кнопка закриття вікна/Alt+F4)
        base.exitFunc = self.exit_game

        # Оновлення
        self.taskMgr.add(self.update, "update")

    # ---------- КОРИСНІ МЕТОДИ ----------
    def show_cursor(self, visible: bool):
        props = WindowProperties()
        props.setCursorHidden(not visible)
        self.win.requestProperties(props)
        # Центр для захоплення мишки під час гри
        self.center_x = self.win.getXSize() // 2
        self.center_y = self.win.getYSize() // 2
        if not visible:
            self.win.movePointer(0, self.center_x, self.center_y)

    def exit_game(self):
        # Автозбереження світу перед виходом
        try:
            self.save_world()
        finally:
            sys.exit(0)

    def on_escape(self):
        if not self.game_started:
            self.exit_game()
        # Якщо в грі — повернутися до меню паузи
        self.show_main_menu()

    # ---------- МЕНЮ ----------
    def create_main_menu(self):
        if self.menu_ui is not None:
            return

        self.menu_ui = DirectFrame(
            frameColor=(0, 0, 0, 0.7),
            frameSize=(-1.33, 1.33, -1, 1),
            parent=aspect2d
        )

        title = OnscreenText(
            text="MinecraftClone",
            pos=(0, 0.4),
            scale=0.12,
            fg=(1, 1, 1, 1),
            parent=self.menu_ui
        )

        play_btn = DirectButton(
            text="Грати",
            scale=0.09,
            pos=(0, 0, 0.05),
            frameColor=(0.2, 1, 0.2, 1),      # зелений фон
            text_fg=(1, 1, 1, 1),             # білий текст
            command=self.start_game,
            parent=self.menu_ui,
            relief=1
        )
        quit_btn = DirectButton(
            text="Вийти",
            scale=0.09,
            pos=(0, 0, -0.2),
            frameColor=(1, 0.2, 0.2, 1),      # червоний фон
            text_fg=(0, 0, 0, 1),             # чорний текст
            command=self.exit_game,           # автозбереження перед виходом
            parent=self.menu_ui,
            relief=1
        )

        self.menu_ui.show()

    def show_main_menu(self):
        self.show_cursor(True)
        if self.menu_ui is None:
            self.create_main_menu()
        else:
            self.menu_ui.show()
        # Блокуємо гру
        self.game_started = False

    def hide_main_menu(self):
        if self.menu_ui:
            self.menu_ui.hide()
        self.show_cursor(False)

    def start_game(self):
        # При першому старті — ініціалізуємо світ
        if not hasattr(self, "world_initialized"):
            self.init_world()
            self.world_initialized = True
            # Автозавантаження збереженого світу (тільки динамічні блоки, без платформи)
            self.load_world()

        # Старт
        self.game_started = True
        self.is_dead = False
        self.hide_main_menu()
        # Початкова позиція камери
        self.camera.setPos(0, 0, 5)
        self.pitch = 0
        self.yaw = 0
        self.camera.setHpr(self.yaw, self.pitch, 0)

    # ---------- ВІДРОДЖЕННЯ UI ----------
    def create_respawn_ui(self):
        if self.respawn_ui is not None:
            return

        self.respawn_ui = DirectFrame(
            frameColor=(0, 0, 0, 0.6),
            frameSize=(-1.33, 1.33, -1, 1),
            parent=aspect2d
        )

        self.respawn_button = DirectButton(
            text="Відро",
            scale=0.08,
            pos=(-0.3, 0, -0.1),
            command=self.on_respawn_button,
            parent=self.respawn_ui,
            frameColor=(0.2, 1, 0.2, 1),
            text_fg=(1, 1, 1, 1),
            relief=1
        )

        # 🟥 Кнопка "Вийти"
        self.quit_button = DirectButton(
            text="Вийти",
            scale=0.08,
            pos=(0.3, 0, -0.1),
            command=self.exit_game,  # автозбереження перед виходом
            parent=self.respawn_ui,
            frameColor=(1, 0.2, 0.2, 1),
            text_fg=(0, 0, 0, 1),
            relief=1
        )
        self.respawn_ui.hide()

    def show_respawn_ui(self):
        if self.respawn_ui is None:
            self.create_respawn_ui()
        self.respawn_ui.show()
        self.show_cursor(True)

    def hide_respawn_ui(self):
        if self.respawn_ui:
            self.respawn_ui.hide()
        self.show_cursor(False)

    def on_respawn_button(self):
        self.respawn_player()

    # ---------- СВІТ ----------
    def init_world(self):
        # Створюємо рівну платформу
        self.create_flat_platform()
        # Камера
        self.camera.setPos(self.spawn_pos)
        self.pitch = 0
        self.yaw = 0
        self.camera.setHpr(self.yaw, self.pitch, 0)

    def create_block(self, x, y, z, is_base=False):
        half_size = self.block_size / 2
        shape = BulletBoxShape(Vec3(half_size, half_size, half_size))
        node = BulletRigidBodyNode(f'Block_{x}_{y}_{z}')
        node.addShape(shape)
        node.setMass(0)

        np = render.attachNewNode(node)
        np.setPos(x, y, z)
        node.setPythonTag("nodepath", np)
        node.setPythonTag("is_base", is_base)
        self.physics_world.attachRigidBody(node)

        visual = loader.loadModel("models/box")
        visual.setScale(self.block_size)

        r = random.uniform(0.4, 1.0)
        g = random.uniform(0.6, 1.0)
        b = random.uniform(0.4, 1.0)
        visual.setColor(r, g, b, 1)

        visual.reparentTo(np)
        self.blocks.append(np)

        # Відтворення звуку при створенні блоку (не для масового створення?)
        self.place_sound.play()
        return np

    def create_flat_platform(self):
        grid_size = 30
        for x in range(-grid_size // 2, grid_size // 2):
            for y in range(-grid_size // 2, grid_size // 2):
                bx = x * self.spacing
                by = y * self.spacing
                bz = 0
                self.create_block(bx, by, bz, is_base=True)
                self.base_positions.add((bx, by, bz))

    # ---------- ЖИТТЯ / СМЕРТЬ ----------
    def player_died(self):
        if self.is_dead:
            return
        print("💀 Гравець загинув!")
        self.is_dead = True
        self.velocity_z = 0.0
        self.is_jumping = False
        self.death_sound.play()
        self.show_respawn_ui()

    def respawn_player(self):
        print("🧬 Відродження!")
        self.camera.setPos(self.spawn_pos)
        self.velocity_z = 0.0
        self.is_jumping = False
        self.is_dead = False
        self.respawn_sound.play()
        self.hide_respawn_ui()

    # ---------- ІГРОВА ЛОГІКА ----------
    def update(self, task):
        dt = globalClock.getDt()

        # Якщо в меню або мертвий — логіка гри не виконується
        if not self.game_started or self.is_dead:
            return Task.cont

        self.physics_world.doPhysics(dt)

        is_down = base.mouseWatcherNode.is_button_down
        direction = Vec3(0, 0, 0)

        # WASD
        if is_down(KeyboardButton.ascii_key('w')):
            direction.y += 1
        if is_down(KeyboardButton.ascii_key('s')):
            direction.y -= 1
        if is_down(KeyboardButton.ascii_key('a')):
            direction.x -= 1
        if is_down(KeyboardButton.ascii_key('d')):
            direction.x += 1

        # 🎯 Мишка — обертання
        if self.mouseWatcherNode.hasMouse():
            md = self.win.getPointer(0)
            dx = md.getX() - self.center_x
            dy = md.getY() - self.center_y

            self.yaw -= dx * 0.1
            self.pitch -= dy * 0.1
            self.pitch = max(-90, min(90, self.pitch))
            self.camera.setHpr(self.yaw, self.pitch, 0)
            self.win.movePointer(0, self.center_x, self.center_y)

        # 🎮 Рух у напрямку камери (горизонтально)
        cam_vec = self.camera.getQuat().getForward()
        right_vec = self.camera.getQuat().getRight()
        move_vec = (cam_vec * direction.y + right_vec * direction.x)
        if move_vec.length_squared() > 0:
            move_vec.normalize()
            self.camera.setPos(self.camera.getPos() + move_vec * self.speed * dt)

        # 👣 Перевірка землі під камерою (рейтрейс вниз)
        cam_pos = self.camera.getPos()
        ray_from = Point3(cam_pos.x, cam_pos.y, cam_pos.z)
        ray_to   = Point3(cam_pos.x, cam_pos.y, cam_pos.z - 100.0)
        result = self.physics_world.rayTestClosest(ray_from, ray_to)

        ground_available = result.hasHit()
        target_ground_cam_z = None
        if ground_available:
            hit_pos = result.getHitPos()
            ground_top_z = hit_pos.z
            target_ground_cam_z = ground_top_z + self.eye_height

        # ⏫ Стрибок
        is_on_ground = False
        if ground_available:
            if (self.camera.getZ() <= target_ground_cam_z + self.ground_snap_distance
                and self.velocity_z <= 0.05):
                is_on_ground = True

        if is_down(KeyboardButton.space()) and is_on_ground:
            self.velocity_z = self.jump_speed
            self.is_jumping = True

        # 🪂 Гравітація + “прилипання” до землі
        self.velocity_z += -9.8 * dt
        new_z = self.camera.getZ() + self.velocity_z * dt

        if ground_available and self.velocity_z <= 0 and new_z <= target_ground_cam_z:
            new_z = target_ground_cam_z
            self.velocity_z = 0.0
            self.is_jumping = False

        self.camera.setZ(new_z)

        # 💀 Перевірка на смерть при падінні
        if (self.camera.getZ() < self.death_height) and (not self.is_dead):
            self.player_died()

        return Task.cont

    # ---------- ВЗАЄМОДІЯ З БЛОКАМИ ----------
    def place_block(self):
        if self.is_dead or not self.game_started:
            return
        direction = self.camera.getQuat().getForward().normalized()
        origin = self.camera.getPos()
        target_pos = origin + direction * 2.0

        x = round(target_pos.x / self.spacing) * self.spacing
        y = round(target_pos.y / self.spacing) * self.spacing
        z = round(target_pos.z / self.spacing) * self.spacing

        # Ігноруємо, якщо намагаємось ставити в позицію базової платформи (можна дозволити — за бажанням)
        if (x, y, z) in self.base_positions:
            return

        self.create_block(x, y, z, is_base=False)

    def break_block(self):
        if self.is_dead or not self.game_started:
            return
        origin = self.camera.getPos()
        direction = self.camera.getQuat().getForward().normalized()
        ray_from = origin
        ray_to = origin + direction * 3.0

        result = self.physics_world.rayTestClosest(ray_from, ray_to)
        if result.hasHit():
            hit_node = result.getNode()
            np = hit_node.getPythonTag("nodepath")

            if np and np in self.blocks:
                # Не дозволяємо ламати базову платформу
                if hit_node.getPythonTag("is_base"):
                    return

                self.physics_world.removeRigidBody(hit_node)
                np.removeNode()
                self.blocks.remove(np)

                # Відтворення звуку при знищенні блоку
                self.break_sound.play()

    # ---------- ЗБЕРЕЖЕННЯ / ЗАВАНТАЖЕННЯ ----------
    def save_world(self):
        # Зберігаємо лише НЕбазові блоки (динамічні)
        data = []
        for np in self.blocks:
            node = np.node()
            if node.getPythonTag("is_base"):
                continue
            pos = np.getPos()
            data.append({"x": float(pos.x), "y": float(pos.y), "z": float(pos.z)})

        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f)
        print(f"✅ Світ збережено у {SAVE_FILE}")

    def clear_dynamic_blocks(self):
        # Видалити всі динамічні блоки перед завантаженням, щоб не дублювати
        to_remove = []
        for np in self.blocks:
            node = np.node()
            if not node.getPythonTag("is_base"):
                to_remove.append(np)
        for np in to_remove:
            node = np.node()
            self.physics_world.removeRigidBody(node)
            np.removeNode()
            self.blocks.remove(np)

    def load_world(self):
        if not os.path.exists(SAVE_FILE):
            print("ℹ️ Немає збереженого світу.")
            return

        # Очищуємо динамічні блоки перед завантаженням
        self.clear_dynamic_blocks()

        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        for block_data in data:
            x = float(block_data["x"])
            y = float(block_data["y"])
            z = float(block_data["z"])
            # захист від випадкового дублювання базових
            if (x, y, z) in self.base_positions:
                continue
            self.create_block(x, y, z, is_base=False)

        print("🌍 Світ завантажено!")

# Запуск
app = MinecraftClone()
app.run()
