from direct.showbase.ShowBase import ShowBase
from panda3d.core import (
    AmbientLight, PointLight, Vec4, Material, TransparencyAttrib,
    Geom, GeomNode, GeomLines, GeomTriangles,
    GeomVertexFormat, GeomVertexData, GeomVertexWriter, TextNode
)
from direct.gui.OnscreenText import OnscreenText
from direct.gui.OnscreenImage import OnscreenImage
from direct.gui.DirectGui import DirectFrame
import math
import random

SCALE_FACTOR = 0.5  # глобальний масштаб

# =========================
# Візуалізація орбіти (біле кільце)
# =========================
def make_orbit_node(name: str, radius: float, segments: int = 160, alpha: float = 0.9) -> GeomNode:
    fmt = GeomVertexFormat.getV3c4()
    vdata = GeomVertexData(name, fmt, Geom.UHStatic)
    v_writer = GeomVertexWriter(vdata, 'vertex')
    c_writer = GeomVertexWriter(vdata, 'color')
    color = (1.0, 1.0, 1.0, alpha)

    for i in range(segments + 1):
        ang = 2.0 * math.pi * (i / segments)
        x = radius * math.cos(ang)
        y = radius * math.sin(ang)
        v_writer.addData3(x, y, 0.0)
        c_writer.addData4f(*color)

    lines = GeomLines(Geom.UHStatic)
    for i in range(segments):
        lines.addVertices(i, i + 1)

    geom = Geom(vdata)
    geom.addPrimitive(lines)
    node = GeomNode(name)
    node.addGeom(geom)
    return node

# =========================
# Кільце (анулюс) з UV
# =========================
def make_ring_node(name: str, inner_r: float, outer_r: float, segments: int = 180, repeat_u: int = 4) -> GeomNode:
    fmt = GeomVertexFormat.getV3t2()
    vdata = GeomVertexData(name, fmt, Geom.UHStatic)
    v_writer = GeomVertexWriter(vdata, 'vertex')
    t_writer = GeomVertexWriter(vdata, 'texcoord')

    for i in range(segments + 1):
        ang = 2.0 * math.pi * (i / segments)
        ci, si = math.cos(ang), math.sin(ang)
        v_writer.addData3(inner_r * ci, inner_r * si, 0.0)
        t_writer.addData2f((i / segments) * repeat_u, 0.0)
        v_writer.addData3(outer_r * ci, outer_r * si, 0.0)
        t_writer.addData2f((i / segments) * repeat_u, 1.0)

    tris = GeomTriangles(Geom.UHStatic)
    for i in range(segments):
        i_in = 2 * i
        i_out = i_in + 1
        j_in = 2 * (i + 1)
        j_out = j_in + 1
        tris.addVertices(i_in, i_out, j_out)
        tris.addVertices(i_in, j_out, j_in)

    geom = Geom(vdata)
    geom.addPrimitive(tris)
    node = GeomNode(name)
    node.addGeom(geom)
    return node

# =========================
# Планета
# =========================
class Planet:
    def __init__(self, base, name, radius, distance, orbit_period,
                 texture=None, spin_speed=25.0, tilt=0.0, moons_count=0):
        self.base = base
        self.name = name
        self.radius = radius
        self.distance = distance
        self.orbit_period = orbit_period
        self.tilt = tilt
        self.moons_count = moons_count

        self.angular_speed = 360.0 / orbit_period  # умовна швидкість
        self.spin_speed = spin_speed

        self.pivot = base.render.attachNewNode(f"{name}-pivot")

        self.model = base.loader.loadModel("models/smiley")
        self.model.reparentTo(self.pivot)
        self.model.setPos(distance * SCALE_FACTOR, 0, 0)
        self.model.setScale(radius * SCALE_FACTOR)

        self.texture_file = texture
        if texture:
            tex = base.loader.loadTexture(texture)
            self.model.setTexture(tex, 1)

        self.model.setP(tilt)
        self.moons = []

        orbit_node = make_orbit_node(f"{name}-orbit", self.model.getX(), segments=160, alpha=0.9)
        self.orbit_np = base.render.attachNewNode(orbit_node)
        self.orbit_np.setTransparency(TransparencyAttrib.MAlpha)

    def add_moon(self, moon):
        self.moons.append(moon)

    def update(self, dt, time_factor):
        self.pivot.setH(self.pivot.getH() + self.angular_speed * dt * time_factor)
        self.model.setH(self.model.getH() + self.spin_speed * dt * time_factor)
        for m in self.moons:
            m.update(dt, time_factor)

# =========================
# Супутник
# =========================
class Moon:
    def __init__(self, base, planet: Planet, name: str,
                 radius: float, distance: float, orbit_period: float,
                 texture: str = None, spin_speed: float = 15.0):
        self.base = base
        self.name = name
        self.planet = planet
        self.angular_speed = 360.0 / orbit_period
        self.spin_speed = spin_speed

        self.pivot = planet.model.attachNewNode(f"{planet.name}-{name}-pivot")

        self.model = base.loader.loadModel("models/smiley")
        self.model.reparentTo(self.pivot)
        self.model.setPos(distance * SCALE_FACTOR, 0, 0)
        self.model.setScale(radius * SCALE_FACTOR)
        self.texture_file = texture
        if texture:
            tex = base.loader.loadTexture(texture)
            self.model.setTexture(tex, 1)

    def update(self, dt, time_factor):
        self.pivot.setH(self.pivot.getH() + self.angular_speed * dt * time_factor)
        self.model.setH(self.model.getH() + self.spin_speed * dt * time_factor)

# =========================
# Пояс астероїдів
# =========================
class AsteroidBelt:
    def __init__(self, base, inner_radius=30, outer_radius=38, count=400):
        self.base = base
        self.asteroids = []
        self.asteroid_tex = base.loader.loadTexture("asteroid.jpg")
        self.root = base.render.attachNewNode("asteroid-belt")

        for i in range(count):
            r = random.uniform(inner_radius, outer_radius) * SCALE_FACTOR
            ang = random.uniform(0, 2 * math.pi)
            x = r * math.cos(ang)
            y = r * math.sin(ang)

            model = base.loader.loadModel("models/smiley")
            model.reparentTo(self.root)

            sx = random.uniform(0.05, 0.15) * SCALE_FACTOR
            sy = random.uniform(0.05, 0.15) * SCALE_FACTOR
            sz = random.uniform(0.05, 0.15) * SCALE_FACTOR
            model.setScale(sx, sy, sz)

            model.setHpr(random.uniform(0, 360),
                         random.uniform(0, 360),
                         random.uniform(0, 360))

            model.setPos(x, y, random.uniform(-0.3, 0.3))
            model.setTexture(self.asteroid_tex, 1)

            orbit_speed = 360.0 / random.uniform(200, 400)
            self.asteroids.append((model, r, ang, orbit_speed))

    def update(self, dt, time_factor):
        for i, (model, r, ang, speed) in enumerate(self.asteroids):
            ang += speed * dt * (math.pi / 180.0) * time_factor
            x = r * math.cos(ang)
            y = r * math.sin(ang)
            model.setPos(x, y, model.getZ())
            self.asteroids[i] = (model, r, ang, speed)

# =========================
# Головний застосунок
# =========================
class SolarSystemApp(ShowBase):
    def __init__(self):
        super().__init__()

        self.setBackgroundColor(0, 0, 0)
        self.disableMouse()  # власне керування камерою

        # Шрифт
        self.font = self.loader.loadFont("DejaVuSans.ttf")
        TextNode.setDefaultFont(self.font)

        # Світло
        amb = AmbientLight("ambient")
        amb.setColor(Vec4(0.12, 0.12, 0.16, 1))
        amb_np = self.render.attachNewNode(amb)
        self.render.setLight(amb_np)

        plight = PointLight("sun-light")
        plight.setColor(Vec4(1.0, 0.95, 0.85, 1))
        self.sun_light_np = self.render.attachNewNode(plight)
        self.render.setLight(self.sun_light_np)

        # Сонце
        self.sun = self.loader.loadModel("models/smiley")
        self.sun.reparentTo(self.render)
        self.sun.setScale(6.0 * SCALE_FACTOR)
        self.sun.setPos(0, 0, 0)
        sun_tex = self.loader.loadTexture("sun.jpg")
        self.sun.setTexture(sun_tex, 1)
        self.sun_mat = Material()
        self.sun_mat.setEmission((1.0, 1.0, 0.0, 1.0))
        self.sun.setMaterial(self.sun_mat)
        self.sun_light_np.reparentTo(self.sun)

        # Зоряне небо (сфера на камері)
        self.sky = self.loader.loadModel("models/smiley")
        self.sky.reparentTo(self.camera)
        self.sky.setScale(500)
        self.sky.setTwoSided(True)
        self.sky.setLightOff()
        self.sky.setShaderOff()
        sky_tex = self.loader.loadTexture("stars.jpg")
        self.sky.setTexture(sky_tex, 1)

        # Ефекти сонця
        self.pulse_time = 0.0
        self.pulse_speed = 0.3
        self.pulse_strength = 0.3
        self.sun_spin_speed = 6.0

        # Планети
        self.planets = [
            Planet(self, "Меркурій", 0.6, 10, 10,  texture="mercury.jpg", moons_count=0),
            Planet(self, "Венера",   0.9, 16, 18,  texture="venus.jpg",   moons_count=0),
            Planet(self, "Земля",    1.0, 22, 24,  texture="earth.jpg",   tilt=23.5, moons_count=1),
            Planet(self, "Марс",     0.8, 28, 46,  texture="mars.jpg",    tilt=25.0, moons_count=2),
            Planet(self, "Юпітер",   2.5, 40, 120, texture="jupiter.jpg", moons_count=79),
            Planet(self, "Сатурн",   2.1, 52, 180, texture="saturn.jpg",  tilt=27.0, moons_count=82),
            Planet(self, "Уран",     1.7, 64, 260, texture="uranus.jpg",  tilt=98.0, moons_count=27),
            Planet(self, "Нептун",   1.6, 76, 320, texture="neptune.jpg", tilt=28.0, moons_count=14),
        ]

        # Місяці
        self.add_moons()

        # Кільця
        self.add_textured_rings()

        # Пояс астероїдів
        self.asteroid_belt = AsteroidBelt(self, inner_radius=30, outer_radius=38, count=400)

        # Швидкий доступ
        self.planet_dict = {p.name: p for p in self.planets}

        # Інфо-панель
        self.info_visible = True
        self.info_frame = None
        self.info_text = None
        self.info_image = None

        # Порівняння ваги: g та маса людини
        self.surface_gravity = {
            "Меркурій": 3.7,
            "Венера": 8.87,
            "Земля": 9.81,
            "Марс": 3.71,
            "Юпітер": 24.79,
            "Сатурн": 10.44,
            "Уран": 8.69,
            "Нептун": 11.15,
            "Місяць": 1.62,
        }
        self.human_mass = 70  # кг

        # Індикатор маси людини
        self.mass_text = OnscreenText(
            text=f"Маса людини: {self.human_mass} кг",
            pos=(1.15, 0.90), scale=0.05, fg=(0.7, 1.0, 0.7, 1),
            align=TextNode.ARight, mayChange=True, font=self.font
        )

        # Окрема панель порівняння ваги
        self.weight_frame = None

        # Час
        self.time_factor = 1.0
        self.time_text = OnscreenText(
            text="Час: x1.00",
            pos=(1.15, 0.95), scale=0.05, fg=(1,1,1,1), align=TextNode.ARight, mayChange=True, font=self.font
        )

        # Клавіатура: фокус на планеті
        self.accept("1", lambda: self.focus_on_planet("Меркурій"))
        self.accept("2", lambda: self.focus_on_planet("Венера"))
        self.accept("3", lambda: self.focus_on_planet("Земля"))
        self.accept("4", lambda: self.focus_on_planet("Марс"))
        self.accept("5", lambda: self.focus_on_planet("Юпітер"))
        self.accept("6", lambda: self.focus_on_planet("Сатурн"))
        self.accept("7", lambda: self.focus_on_planet("Уран"))
        self.accept("8", lambda: self.focus_on_planet("Нептун"))
        self.accept("0", self.reset_camera)

        # Фокус на супутнику (клавіша f): циклічно переключає місяці вибраної планети
        self.accept("f", self.focus_on_next_moon)
        self.moon_focus_index = {}  # ім'я планети -> індекс поточного супутника

        # Час: керування
        self.accept("+", self.speed_up)
        self.accept("-", self.slow_down)
        self.accept("=", self.reset_time)
        self.accept("r", self.reset_time)

        # Регулювання маси людини
        self.accept("[", self.decrease_mass)
        self.accept("]", self.increase_mass)

        # Інфо-панель
        self.accept("i", self.toggle_info)

        # Порівняння та хелп
        self.accept("c", self.show_size_comparison)
        self.comparison_mode = False
        self.saved_positions = {}          # name -> (parent_np, local_pos)
        self.planet_diameters = {
            "Меркурій": 4879,
            "Венера": 12104,
            "Земля": 12742,
            "Марс": 6779,
            "Юпітер": 139820,
            "Сатурн": 116460,
            "Уран": 50724,
            "Нептун": 49244,
        }
        self.accept("h", self.toggle_help)
        self.help_frame = None

        # Порівняння ваги на всіх світах
        self.accept("g", self.toggle_weight_comparison)

        # Параметри камери (вільне обертання навколо центру)
        self.cam_angle_h = 0.0   # азимут
        self.cam_angle_p = 20.0  # підйом
        self.cam_distance = 150 * SCALE_FACTOR
        self.last_mouse_pos = None
        self.mouse_btn_held = False

        # Миша
        self.accept("mouse1", self.start_rotate)
        self.accept("mouse1-up", self.stop_rotate)
        self.accept("wheel_up", self.zoom_in)
        self.accept("wheel_down", self.zoom_out)

        # Стан слідування
        self.follow_target = None

        # Оновлення
        self.taskMgr.add(self.update_task, "update-orbits")

    # ==== МИША ====
    def start_rotate(self):
        if self.mouseWatcherNode.hasMouse():
            self.last_mouse_pos = (self.mouseWatcherNode.getMouseX(),
                                   self.mouseWatcherNode.getMouseY())
            self.mouse_btn_held = True

    def stop_rotate(self):
        self.mouse_btn_held = False

    def zoom_in(self):
        self.cam_distance = max(20 * SCALE_FACTOR, self.cam_distance - 5 * SCALE_FACTOR)

    def zoom_out(self):
        self.cam_distance += 5 * SCALE_FACTOR

    # ==== Сонце ====
    def hide_sun(self):
        self.sun.hide()

    def show_sun(self):
        self.sun.show()

    # ==== Місяці ====
    def add_moons(self):
        zemlya = self._get("Земля")
        if zemlya:
            zemlya.add_moon(Moon(self, zemlya, "Місяць", radius=0.27, distance=2.5, orbit_period=5.0, texture="moon.jpg"))

        mars = self._get("Марс")
        if mars:
            mars.add_moon(Moon(self, mars, "Фобос", radius=0.12, distance=1.8, orbit_period=3.0, texture="phobos.jpg"))
            mars.add_moon(Moon(self, mars, "Деймос", radius=0.08, distance=2.6, orbit_period=5.0, texture="deimos.jpg"))

        yupiter = self._get("Юпітер")
        if yupiter:
            yupiter.add_moon(Moon(self, yupiter, "Іо",       radius=0.36, distance=3.0, orbit_period=4.0, texture="io.jpg"))
            yupiter.add_moon(Moon(self, yupiter, "Європа",   radius=0.31, distance=3.8, orbit_period=5.0, texture="europa.jpg"))
            yupiter.add_moon(Moon(self, yupiter, "Ганімед",  radius=0.41, distance=4.6, orbit_period=6.0, texture="ganimede.jpg"))
            yupiter.add_moon(Moon(self, yupiter, "Каллісто", radius=0.38, distance=5.4, orbit_period=7.0, texture="calisto.jpg"))

        saturn = self._get("Сатурн")
        if saturn:
            saturn.add_moon(Moon(self, saturn, "Титан",     radius=0.35, distance=4.2, orbit_period=6.5, texture="titan.jpg"))
            saturn.add_moon(Moon(self, saturn, "Рея",       radius=0.22, distance=3.4, orbit_period=6.0, texture="rhea.jpg"))
            saturn.add_moon(Moon(self, saturn, "Енцелад",   radius=0.15, distance=2.6, orbit_period=4.5, texture="enceladus.jpg"))

        uran = self._get("Уран")
        if uran:
            uran.add_moon(Moon(self, uran, "Тітанія", radius=0.20, distance=3.2, orbit_period=5.5, texture="titania.jpg"))
            uran.add_moon(Moon(self, uran, "Оберон",  radius=0.19, distance=3.8, orbit_period=6.0, texture="oberon.jpg"))
            uran.add_moon(Moon(self, uran, "Міранда", radius=0.12, distance=2.4, orbit_period=4.0, texture="miranda.jpg"))

        neptun = self._get("Нептун")
        if neptun:
            neptun.add_moon(Moon(self, neptun, "Тритон",  radius=0.27, distance=3.5, orbit_period=5.5, texture="triton.jpg"))
            neptun.add_moon(Moon(self, neptun, "Протей",  radius=0.10, distance=2.6, orbit_period=4.5, texture="proteus.jpg"))

    # ==== Кільця ====
    def add_textured_rings(self):
        saturn = self._get("Сатурн")
        if saturn:
            s_scale = saturn.model.getScale().x
            s_ring_node = make_ring_node("Saturn-rings", inner_r=s_scale * 2.5, outer_r=s_scale * 3.0, segments=220, repeat_u=4)
            s_np = saturn.model.attachNewNode(s_ring_node)
            s_np.setTransparency(TransparencyAttrib.MAlpha)
            s_np.setTwoSided(True)
            s_np.setTexture(self.loader.loadTexture("saturn_ring.jpg"), 1)

        uranus = self._get("Уран")
        if uranus:
            u_scale = uranus.model.getScale().x
            u_ring_node = make_ring_node("Uranus-rings", inner_r=u_scale * 2.0, outer_r=u_scale * 2.3, segments=200, repeat_u=4)
            u_np = uranus.model.attachNewNode(u_ring_node)
            u_np.setTransparency(TransparencyAttrib.MAlpha)
            u_np.setTwoSided(True)
            u_np.setTexture(self.loader.loadTexture("uran_ring.png"), 1)

        neptune = self._get("Нептун")
        if neptune:
            n_scale = neptune.model.getScale().x
            n_ring_node = make_ring_node("Neptune-rings", inner_r=n_scale * 1.8, outer_r=n_scale * 2.1, segments=180, repeat_u=4)
            n_np = neptune.model.attachNewNode(n_ring_node)
            n_np.setTransparency(TransparencyAttrib.MAlpha)
            n_np.setTwoSided(True)
            n_np.setTexture(self.loader.loadTexture("neptun_ring.jpg"), 1)

    def _get(self, name: str) -> Planet:
        for p in self.planets:
            if p.name == name:
                return p
        return None

    # ==== Інфо-панель ====
    def show_info(self, target):
        if not self.info_visible:
            return
        self.clear_info()

        self.info_frame = DirectFrame(frameColor=(0, 0, 0, 0.5), frameSize=(-1.35, -0.35, 0.65, 0.95), pos=(0, 0, 0))

        # Планета або супутник
        texture_file = getattr(target, "texture_file", None)
        if texture_file:
            self.info_image = OnscreenImage(image=texture_file, pos=(-1.25, 0, 0.82), scale=(0.12, 1, 0.12))
            self.info_image.setTransparency(True)

        # Базовий текст
        base_text = ""
        if isinstance(target, Planet):
            base_text = (
                f"{target.name}\n"
                f"Радіус: {target.radius}\n"
                f"Відстань: {target.distance}\n"
                f"Орбітальний період: {target.orbit_period}\n"
                f"Нахил осі: {target.tilt}°\n"
                f"Супутників: {target.moons_count}\n"
            )
        else:
            # Це супутник
            base_text = (
                f"{target.name}\n"
                f"Супутник планети: {target.planet.name}\n"
            )

        # Додати вагу людини за наявності g
        g_text = ""
        # Якщо це супутник і для нього є g — показати його; інакше показати g планети
        g_key = target.name
        if isinstance(target, Moon) and g_key not in self.surface_gravity:
            g_key = target.planet.name

        g_val = self.surface_gravity.get(g_key)
        if g_val is not None:
            weight = self.human_mass * g_val
            if g_key != target.name:
                g_text += f"g (на {g_key}): {g_val:.2f} м/с²\n"
            else:
                g_text += f"g: {g_val:.2f} м/с²\n"
            g_text += f"Вага людини ({self.human_mass} кг): {weight:.1f} Н\n"

        self.info_text = OnscreenText(
            text=base_text + g_text,
            pos=(-1.05, 0.85), scale=0.05, fg=(1, 1, 1, 1), align=TextNode.ALeft, mayChange=True, font=self.font
        )

    def clear_info(self):
        if self.info_text:
            self.info_text.destroy(); self.info_text = None
        if self.info_image:
            self.info_image.destroy(); self.info_image = None
        if self.info_frame:
            self.info_frame.destroy(); self.info_frame = None

    # ==== Порівняння ваги на всіх планетах ====
    def toggle_weight_comparison(self):
        if self.weight_frame:
            self.weight_frame.destroy()
            self.weight_frame = None
            return

        self.weight_frame = DirectFrame(frameColor=(0, 0, 0, 0.6), frameSize=(-1.35, 1.35, -0.95, 0.95), pos=(0, 0, 0))
        lines = [f"Порівняння ваги людини ({self.human_mass} кг) на різних світах:\n"]
        worlds = ["Меркурій", "Венера", "Земля", "Марс", "Юпітер", "Сатурн", "Уран", "Нептун", "Місяць"]
        for w in worlds:
            g = self.surface_gravity.get(w)
            if g is not None:
                weight = self.human_mass * g
                lines.append(f"• {w}: g={g:.2f} м/с², вага={weight:.1f} Н")
        OnscreenText(
            text="\n".join(lines),
            pos=(-1.2, 0.8), scale=0.05, fg=(0.8, 1, 0.8, 1), align=TextNode.ALeft, mayChange=False, font=self.font, parent=self.weight_frame
        )

    # ==== Камера та час ====
    def focus_on_planet(self, name):
        planet = self.planet_dict.get(name)
        if planet:
            self.follow_target = planet
            self.show_info(planet)

    def focus_on_next_moon(self):
        # Визначити активну планету: якщо фокус на планеті, беремо її; якщо на місяці — її планету.
        planet = None
        if isinstance(self.follow_target, Planet):
            planet = self.follow_target
        elif isinstance(self.follow_target, Moon):
            planet = self.follow_target.planet
        else:
            # за замовчуванням — Земля
            planet = self.planet_dict.get("Земля")

        if not planet or not planet.moons:
            return

        idx = self.moon_focus_index.get(planet.name, -1)
        idx = (idx + 1) % len(planet.moons)
        self.moon_focus_index[planet.name] = idx

        moon = planet.moons[idx]
        self.follow_target = moon
        self.show_info(moon)

    def reset_camera(self):
        self.follow_target = None
        self.cam_angle_h = 0.0
        self.cam_angle_p = 20.0
        self.cam_distance = 150 * SCALE_FACTOR
        self.clear_info()

    def speed_up(self):
        self.time_factor *= 2.0
        self.time_text.setText(f"Час: x{self.time_factor:.2f}")

    def slow_down(self):
        self.time_factor *= 0.5
        self.time_text.setText(f"Час: x{self.time_factor:.2f}")

    def reset_time(self):
        self.time_factor = 1.0
        self.time_text.setText("Час: x1.00")

    def increase_mass(self):
        self.human_mass += 5
        self.mass_text.setText(f"Маса людини: {self.human_mass} кг")
        # Оновити інфо-панель, якщо активна
        if self.follow_target and self.info_visible:
            self.show_info(self.follow_target)
        # Якщо таблиця порівняння відкрита — перебудувати
        if self.weight_frame:
            self.toggle_weight_comparison()
            self.toggle_weight_comparison()

    def decrease_mass(self):
        self.human_mass = max(5, self.human_mass - 5)
        self.mass_text.setText(f"Маса людини: {self.human_mass} кг")
        # Оновити інфо-панель, якщо активна
        if self.follow_target and self.info_visible:
            self.show_info(self.follow_target)
        # Якщо таблиця порівняння відкрита — перебудувати
        if self.weight_frame:
            self.toggle_weight_comparison()
            self.toggle_weight_comparison()

    def toggle_info(self):
        self.info_visible = not self.info_visible
        if not self.info_visible:
            self.clear_info()
        elif self.follow_target:
            self.show_info(self.follow_target)

    def toggle_help(self):
        if self.help_frame:
            self.help_frame.destroy(); self.help_frame = None
        else:
            self.help_frame = DirectFrame(frameColor=(0, 0, 0, 0.6), frameSize=(-1.35, 1.35, -0.95, 0.95), pos=(0, 0, 0))
            OnscreenText(
                text=(
                    "Керування:\n"
                    "ЛКМ + рух – обертання камери\n"
                    "Колесо – зум\n"
                    "1-8 – фокус на планеті\n"
                    "f – фокус на супутнику вибраної планети (циклічно)\n"
                    "0 – скинути камеру\n"
                    "+ / - – прискорити / сповільнити час\n"
                    "= або r – скинути час\n"
                    "[ / ] – зменшити / збільшити масу людини\n"
                    "i – показати/сховати інформацію\n"
                    "c – порівняння розмірів (без Сонця, орбіт, поясу)\n"
                    "g – порівняння ваги людини на різних світах\n"
                    "h – показати/сховати довідку\n"
                ),
                pos=(-1.2, 0.8), scale=0.05, fg=(1, 1, 0, 1), align=TextNode.ALeft, mayChange=False, font=self.font, parent=self.help_frame
            )

    # ==== Порівняння розмірів ====
    def show_size_comparison(self):
        if not self.comparison_mode:
            # Ховаємо Сонце, орбіти та пояс
            self.hide_sun()
            for p in self.planets:
                p.orbit_np.hide()
            self.asteroid_belt.root.hide()

            # Зберігаємо позиції
            self.saved_positions = {p.name: (p.pivot, p.model.getPos(p.pivot)) for p in self.planets}

            # Вирівнюємо планети в ряд у render (без текстових підписів)
            x_offset = -30.0 * SCALE_FACTOR
            spacing = 3.0
            for p in self.planets:
                p.model.wrtReparentTo(self.render)
                p.model.setPos(x_offset, 0, 0)
                x_offset += p.radius * spacing

            # Камера для огляду ряду
            self.follow_target = None
            self.cam_angle_h = 0.0
            self.cam_angle_p = 10.0
            self.cam_distance = 120 * SCALE_FACTOR

            self.clear_info()
            self.comparison_mode = True
        else:
            # Повернути все
            for p in self.planets:
                parent_np, local_pos = self.saved_positions[p.name]
                p.model.wrtReparentTo(parent_np)
                p.model.setPos(local_pos)

            self.show_sun()
            for p in self.planets:
                p.orbit_np.show()
            self.asteroid_belt.root.show()

            self.reset_camera()
            self.comparison_mode = False

    # =========================
    # Оновлення
    # =========================
    def update_task(self, task):
        dt = globalClock.getDt()

        # Сонце (не пульсує під час порівняння)
        if not self.comparison_mode:
            self.sun.setH(self.sun.getH() + self.sun_spin_speed * dt * self.time_factor)
            self.pulse_time += dt * self.pulse_speed * self.time_factor
            intensity = 1.0 + self.pulse_strength * math.sin(self.pulse_time)
            self.sun_mat.setEmission((intensity, intensity * 0.95, 0.0, 1.0))
            self.sun.setMaterial(self.sun_mat)

        # Планети та місяці
        for p in self.planets:
            p.update(dt, self.time_factor)

        # Пояс астероїдів (зупинений під час порівняння)
        if not self.comparison_mode:
            self.asteroid_belt.update(dt, self.time_factor)

        # Камера: або слідує за ціллю, або вільне обертання
        if self.follow_target and not self.comparison_mode:
            pos = self.follow_target.model.getPos(self.render)
            self.camera.setPos(pos.x, pos.y - 10 * SCALE_FACTOR, pos.z + 3 * SCALE_FACTOR)
            self.camera.lookAt(pos)
        else:
            if self.mouse_btn_held and self.mouseWatcherNode.hasMouse():
                x, y = self.mouseWatcherNode.getMouseX(), self.mouseWatcherNode.getMouseY()
                dx = x - self.last_mouse_pos[0]
                dy = y - self.last_mouse_pos[1]
                self.cam_angle_h += dx * 100
                self.cam_angle_p = max(-80, min(80, self.cam_angle_p + dy * 100))
                self.last_mouse_pos = (x, y)

            rad_h = math.radians(self.cam_angle_h)
            rad_p = math.radians(self.cam_angle_p)
            cam_x = self.cam_distance * math.cos(rad_p) * math.sin(rad_h)
            cam_y = -self.cam_distance * math.cos(rad_p) * math.cos(rad_h)
            cam_z = self.cam_distance * math.sin(rad_p)

            self.camera.setPos(cam_x, cam_y, cam_z)
            self.camera.lookAt(0, 0, 0)

        return task.cont

# =========================
# Запуск
# =========================
if __name__ == "__main__":
    app = SolarSystemApp()
    app.run()
