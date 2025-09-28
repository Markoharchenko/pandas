from direct.showbase.ShowBase import ShowBase
from panda3d.core import (
    AmbientLight, PointLight, Vec4, Material, TransparencyAttrib,
    Geom, GeomNode, GeomLines, GeomTriangles,
    GeomVertexFormat, GeomVertexData, GeomVertexWriter
)
import math
import random

# =========================
# Налаштування сцени
# =========================
SCALE_FACTOR = 0.5  # глобальний масштаб

# =========================
# Візуалізація орбіти планети (біле кільце)
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
# Кільце (анулюс) для кілець планет (отримує текстуру PNG з альфою)
# =========================
def make_ring_node(name: str, inner_r: float, outer_r: float, segments: int = 180) -> GeomNode:
    fmt = GeomVertexFormat.getV3c4()
    vdata = GeomVertexData(name, fmt, Geom.UHStatic)
    v_writer = GeomVertexWriter(vdata, 'vertex')
    c_writer = GeomVertexWriter(vdata, 'color')
    color = (1.0, 1.0, 1.0, 1.0)  # прозорість забезпечує текстура

    for i in range(segments):
        ang = 2.0 * math.pi * (i / segments)
        ci, si = math.cos(ang), math.sin(ang)
        v_writer.addData3(inner_r * ci, inner_r * si, 0.0)
        c_writer.addData4f(*color)
        v_writer.addData3(outer_r * ci, outer_r * si, 0.0)
        c_writer.addData4f(*color)

    tris = GeomTriangles(Geom.UHStatic)
    for i in range(segments):
        i_in = 2 * i
        i_out = i_in + 1
        j = (i + 1) % segments
        j_in = 2 * j
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
                 texture=None, spin_speed=25.0, tilt=0.0):
        self.base = base
        self.name = name
        # умовна орбітальна швидкість (не реальна анімаційна)
        self.angular_speed = 360.0 / orbit_period
        self.spin_speed = spin_speed

        # pivot — центр обертання навколо Сонця
        self.pivot = base.render.attachNewNode(f"{name}-pivot")

        # модель планети
        self.model = base.loader.loadModel("models/smiley")
        self.model.reparentTo(self.pivot)
        self.model.setPos(distance * SCALE_FACTOR, 0, 0)
        self.model.setScale(radius * SCALE_FACTOR)

        if texture:
            tex = base.loader.loadTexture(texture)
            self.model.setTexture(tex, 1)

        # нахил осі
        self.model.setP(tilt)

        # супутники
        self.moons = []

        # візуальна орбіта планети
        orbit_node = make_orbit_node(f"{name}-orbit", self.model.getX(), segments=160, alpha=0.9)
        orbit_np = base.render.attachNewNode(orbit_node)
        orbit_np.setTransparency(TransparencyAttrib.MAlpha)

    def add_moon(self, moon):
        self.moons.append(moon)

    def update(self, dt, time_factor):
        # рух планети навколо Сонця
        self.pivot.setH(self.pivot.getH() + self.angular_speed * dt * time_factor)
        # власне обертання
        self.model.setH(self.model.getH() + self.spin_speed * dt * time_factor)
        # супутники
        for m in self.moons:
            m.update(dt, time_factor)

# =========================
# Супутник (без візуалізації орбіти)
# =========================
class Moon:
    def __init__(self, base, planet: Planet, name: str,
                 radius: float, distance: float, orbit_period: float,
                 texture: str = None, spin_speed: float = 15.0):
        self.base = base
        self.name = name
        self.planet = planet
        self.angular_speed = 360.0 / orbit_period  # умовно
        self.spin_speed = spin_speed

        self.pivot = planet.model.attachNewNode(f"{planet.name}-{name}-pivot")

        self.model = base.loader.loadModel("models/smiley")
        self.model.reparentTo(self.pivot)
        self.model.setPos(distance * SCALE_FACTOR, 0, 0)
        self.model.setScale(radius * SCALE_FACTOR)

        if texture:
            tex = base.loader.loadTexture(texture)
            self.model.setTexture(tex, 1)

    def update(self, dt, time_factor):
        self.pivot.setH(self.pivot.getH() + self.angular_speed * dt * time_factor)
        self.model.setH(self.model.getH() + self.spin_speed * dt * time_factor)

# =========================
# Пояс астероїдів (каменисті, різної форми, з текстурою)
# =========================
class AsteroidBelt:
    def __init__(self, base, inner_radius=30, outer_radius=38, count=350):
        self.base = base
        self.asteroids = []
        self.asteroid_tex = base.loader.loadTexture("asteroid.jpg")

        for i in range(count):
            r = random.uniform(inner_radius, outer_radius) * SCALE_FACTOR
            ang = random.uniform(0, 2 * math.pi)
            x = r * math.cos(ang)
            y = r * math.sin(ang)

            model = base.loader.loadModel("models/smiley")
            model.reparentTo(base.render)

            # різні масштаби по осях (не куля)
            sx = random.uniform(0.05, 0.15) * SCALE_FACTOR
            sy = random.uniform(0.05, 0.15) * SCALE_FACTOR
            sz = random.uniform(0.05, 0.15) * SCALE_FACTOR
            model.setScale(sx, sy, sz)

            # випадковий нахил
            model.setHpr(random.uniform(0, 360),
                         random.uniform(0, 360),
                         random.uniform(0, 360))

            # позиція та текстура
            model.setPos(x, y, random.uniform(-0.3, 0.3))
            model.setTexture(self.asteroid_tex, 1)

            # повільна орбітальна швидкість для поясу
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

        # фон і камера
        self.setBackgroundColor(0, 0, 0)
        self.disableMouse()
        self.default_cam_pos = (0, -150 * SCALE_FACTOR, 50 * SCALE_FACTOR)
        self.camera.setPos(*self.default_cam_pos)
        self.camera.lookAt(0, 0, 0)

        # світло
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

        # зоряне небо (сфера на камері)
        self.sky = self.loader.loadModel("models/smiley")
        self.sky.reparentTo(self.camera)
        self.sky.setScale(500)
        self.sky.setTwoSided(True)
        self.sky.setLightOff()
        self.sky.setShaderOff()
        sky_tex = self.loader.loadTexture("stars.jpg")
        self.sky.setTexture(sky_tex, 1)

        # ефекти сонця
        self.pulse_time = 0.0
        self.pulse_speed = 0.3
        self.pulse_strength = 0.3
        self.sun_spin_speed = 6.0

        # планети (умовні періоди)
        self.planets = [
            Planet(self, "Mercury", 0.6, 10, 10,  texture="mercury.jpg"),
            Planet(self, "Venus",   0.9, 16, 18,  texture="venus.jpg"),
            Planet(self, "Earth",   1.0, 22, 24,  texture="earth.jpg",  tilt=23.5),
            Planet(self, "Mars",    0.8, 28, 46,  texture="mars.jpg",   tilt=25.0),
            Planet(self, "Jupiter", 2.5, 40, 120, texture="jupiter.jpg"),
            Planet(self, "Saturn",  2.1, 52, 180, texture="saturn.jpg", tilt=27.0),
            Planet(self, "Uranus",  1.7, 64, 260, texture="uranus.jpg", tilt=98.0),
            Planet(self, "Neptune", 1.6, 76, 320, texture="neptune.jpg", tilt=28.0),
        ]

        # супутники (без візуальних орбіт)
        self.add_moons()

        # тонкі текстуровані кільця Сатурна, Урана, Нептуна
        self.add_textured_rings()

        # пояс астероїдів
        self.asteroid_belt = AsteroidBelt(self, inner_radius=30, outer_radius=38, count=400)

        # керування камерою
        self.planet_dict = {p.name: p for p in self.planets}
        self.accept("1", lambda: self.focus_on_planet("Mercury"))
        self.accept("2", lambda: self.focus_on_planet("Venus"))
        self.accept("3", lambda: self.focus_on_planet("Earth"))
        self.accept("4", lambda: self.focus_on_planet("Mars"))
        self.accept("5", lambda: self.focus_on_planet("Jupiter"))
        self.accept("6", lambda: self.focus_on_planet("Saturn"))
        self.accept("7", lambda: self.focus_on_planet("Uranus"))
        self.accept("8", lambda: self.focus_on_planet("Neptune"))
        self.accept("0", self.reset_camera)

        # керування часом
        self.time_factor = 1.0
        self.accept("+", self.speed_up)
        self.accept("-", self.slow_down)
        self.accept("=", self.reset_time)   # на багатьох клавіатурах '=' зручно для скидання
        self.accept("r", self.reset_time)   # альтернативний скидання

        # оновлення
        self.follow_target = None
        self.taskMgr.add(self.update_task, "update-orbits")

    def add_moons(self):
        earth = self._get("Earth")
        if earth:
            earth.add_moon(Moon(self, earth, "Moon", radius=0.27, distance=2.5, orbit_period=5.0, texture="moon.jpg"))

        mars = self._get("Mars")
        if mars:
            mars.add_moon(Moon(self, mars, "Phobos", radius=0.12, distance=1.8, orbit_period=3.0, texture="phobos.jpg"))
            mars.add_moon(Moon(self, mars, "Deimos", radius=0.08, distance=2.6, orbit_period=5.0, texture="deimos.jpg"))

        jupiter = self._get("Jupiter")
        if jupiter:
            jupiter.add_moon(Moon(self, jupiter, "Io",       radius=0.36, distance=3.0, orbit_period=4.0, texture="io.jpg"))
            jupiter.add_moon(Moon(self, jupiter, "Europa",   radius=0.31, distance=3.8, orbit_period=5.0, texture="europa.jpg"))
            jupiter.add_moon(Moon(self, jupiter, "Ganymede", radius=0.41, distance=4.6, orbit_period=6.0, texture="ganimede.jpg"))
            jupiter.add_moon(Moon(self, jupiter, "Callisto", radius=0.38, distance=5.4, orbit_period=7.0, texture="calisto.jpg"))

        saturn = self._get("Saturn")
        if saturn:
            saturn.add_moon(Moon(self, saturn, "Titan",     radius=0.35, distance=4.2, orbit_period=6.5, texture="titan.jpg"))
            saturn.add_moon(Moon(self, saturn, "Rhea",      radius=0.22, distance=3.4, orbit_period=6.0, texture="rhea.jpg"))
            saturn.add_moon(Moon(self, saturn, "Enceladus", radius=0.15, distance=2.6, orbit_period=4.5, texture="enceladus.jpg"))

        uranus = self._get("Uranus")
        if uranus:
            uranus.add_moon(Moon(self, uranus, "Titania", radius=0.20, distance=3.2, orbit_period=5.5, texture="titania.jpg"))
            uranus.add_moon(Moon(self, uranus, "Oberon",  radius=0.19, distance=3.8, orbit_period=6.0, texture="oberon.jpg"))
            uranus.add_moon(Moon(self, uranus, "Miranda", radius=0.12, distance=2.4, orbit_period=4.0, texture="miranda.jpg"))

        neptune = self._get("Neptune")
        if neptune:
            neptune.add_moon(Moon(self, neptune, "Triton",  radius=0.27, distance=3.5, orbit_period=5.5, texture="triton.jpg"))
            neptune.add_moon(Moon(self, neptune, "Proteus", radius=0.10, distance=2.6, orbit_period=4.5, texture="proteus.jpg"))

    def add_textured_rings(self):
        # Сатурн — тонкі кільця з текстурою
        saturn = self._get("Saturn")
        if saturn:
            s_scale = saturn.model.getScale().x
            s_ring_node = make_ring_node("Saturn-rings",
                                         inner_r=s_scale * 2.5,
                                         outer_r=s_scale * 3.0,
                                         segments=220)
            s_np = saturn.model.attachNewNode(s_ring_node)
            s_np.setTransparency(TransparencyAttrib.MAlpha)
            s_np.setTwoSided(True)
            s_tex = self.loader.loadTexture("saturn_ring.jpg")  # PNG з альфою
            s_np.setTexture(s_tex, 1)

        # Уран — тонкі кільця з текстурою
        uranus = self._get("Uranus")
        if uranus:
            u_scale = uranus.model.getScale().x
            u_ring_node = make_ring_node("Uranus-rings",
                                         inner_r=u_scale * 2.0,
                                         outer_r=u_scale * 2.3,
                                         segments=200)
            u_np = uranus.model.attachNewNode(u_ring_node)
            u_np.setTransparency(TransparencyAttrib.MAlpha)
            u_np.setTwoSided(True)
            u_tex = self.loader.loadTexture("uran_ring.png")
            u_np.setTexture(u_tex, 1)

        # Нептун — тонкі кільця з текстурою
        neptune = self._get("Neptune")
        if neptune:
            n_scale = neptune.model.getScale().x
            n_ring_node = make_ring_node("Neptune-rings",
                                         inner_r=n_scale * 1.8,
                                         outer_r=n_scale * 2.1,
                                         segments=180)
            n_np = neptune.model.attachNewNode(n_ring_node)
            n_np.setTransparency(TransparencyAttrib.MAlpha)
            n_np.setTwoSided(True)
            n_tex = self.loader.loadTexture("neptun_ring.jpg")
            n_np.setTexture(n_tex, 1)

    def _get(self, name: str) -> Planet:
        for p in self.planets:
            if p.name == name:
                return p
        return None

    # керування камерою
    def focus_on_planet(self, name):
        planet = self.planet_dict.get(name)
        if planet:
            self.follow_target = planet

    def reset_camera(self):
        self.follow_target = None
        self.camera.setPos(*self.default_cam_pos)
        self.camera.lookAt(0, 0, 0)

    # керування часом
    def speed_up(self):
        self.time_factor *= 2.0
        print(f"Прискорення часу: x{self.time_factor:.2f}")

    def slow_down(self):
        self.time_factor *= 0.5
        print(f"Сповільнення часу: x{self.time_factor:.2f}")

    def reset_time(self):
        self.time_factor = 1.0
        print("Час скинуто: x1.00")

    # головний апдейт
    def update_task(self, task):
        dt = globalClock.getDt()

        # обертання та пульсація Сонця
        self.sun.setH(self.sun.getH() + self.sun_spin_speed * dt * self.time_factor)
        self.pulse_time += dt * self.pulse_speed * self.time_factor
        intensity = 1.0 + self.pulse_strength * math.sin(self.pulse_time)
        self.sun_mat.setEmission((intensity, intensity * 0.95, 0.0, 1.0))
        self.sun.setMaterial(self.sun_mat)

        # планети і супутники
        for p in self.planets:
            p.update(dt, self.time_factor)

        # пояс астероїдів
        self.asteroid_belt.update(dt, self.time_factor)

        # слідування камерою
        if self.follow_target:
            pos = self.follow_target.model.getPos(self.render)
            self.camera.setPos(pos.x, pos.y - 10 * SCALE_FACTOR, pos.z + 3 * SCALE_FACTOR)
            self.camera.lookAt(pos)

        return task.cont

# =========================
# Запуск
# =========================
if __name__ == "__main__":
    app = SolarSystemApp()
    app.run()
