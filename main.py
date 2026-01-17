import pygame
import math
import random

pygame.init()
pygame.font.init()
width, height = 1800, 900

halfWidth, halfHeight = width/2, height/2

win = pygame.display.set_mode((width, height))
particleSurface = pygame.Surface((width, height), pygame.SRCALPHA)
camX = 0
camY = 0

bullets = []
enemys = []
particles = []
pickups = []

upgradeTimer = 0
bulletSafety = 6
upgrading = False
upgradeSelections = []
class particle:
    def __init__(self, x, y, xVel, yVel, shape, color, size, lifeTime, sizeChange=0, borderColor=None, acceleration=(0, 0), drag=1, fade=0):
        self.x = x
        self.y = y
        self.xVel = xVel
        self.yVel = yVel
        self.shape = shape
        self.color = color
        self.size = size
        self.sizeChange = sizeChange
        self.borderColor = borderColor
        self.acceleration = acceleration
        self.drag = drag
        self.fade = fade
        self.lifeTime = lifeTime
    def update(self):
        self.x += self.xVel
        self.y += self.yVel
        self.xVel += self.acceleration[0]
        self.yVel += self.acceleration[1]
        self.color[3] -= self.fade
        if self.color[3] < 0:
            self.color[3] = 0
        if self.borderColor != None:
            self.borderColor[3] -= self.fade
            if self.borderColor[3] < 0:
                self.borderColor[3] = 0
        self.size += self.sizeChange
        if self.size < 1:
            self.size = 0
        self.xVel *= self.drag
        self.yVel *= self.drag
        self.lifeTime -= 1
        if self.lifeTime < 1:
            particles.remove(self)
    def draw(self):
        if self.shape == "square":
            pygame.draw.rect(particleSurface, self.color, (self.x-camX, self.y-camY, self.size, self.size))
            if self.borderColor != None:
                pygame.draw.rect(particleSurface, self.borderColor, (self.x-camX, self.y-camY, self.size, self.size), 2)
        elif self.shape == "circle":
            pygame.draw.circle(particleSurface, self.color, (self.x-camX, self.y-camY), self.size)
            if self.borderColor != None:
                pygame.draw.circle(particleSurface, self.borderColor, (self.x-camX, self.y-camY), self.size, 2)

class bullet:
    def __init__(self, x, y, owner, angle, size, color, trailLength, speed, damage, force, effects, lifeTime, pierce):
        self.x = x
        self.y = y
        self.owner = owner
        self.angle = angle
        self.size = size
        self.color = color
        self.trailLength = trailLength
        self.speed = speed
        self.damage = damage
        self.force = force
        self.effects = effects
        self.lifeTime = lifeTime
        self.pierce = pierce
        self.enemyList = []
        self.augments = {}
    def draw(self):
        pygame.draw.line(win, self.color, (self.x - camX, self.y - camY), 
                         (self.x - (math.cos(self.angle) * self.trailLength) - camX, self.y - (math.sin(self.angle) * self.trailLength) - camY), round(self.size))
    def delete(self):
        if self in bullets:
            bullets.remove(self)
    def update(self):
        self.lifeTime -= 1
        if self.lifeTime < 1 or math.dist((self.x, self.y), (p.x, p.y)) > 2000:
            self.delete()
        for i in range(bulletSafety):
            self.x += math.cos(self.angle) * (self.speed / bulletSafety)
            self.y += math.sin(self.angle) * (self.speed / bulletSafety)
            for e in enemys:
                if math.dist((self.x, self.y), (e.x+(e.size/2), e.y+(e.size/2))) < e.size/2:
                    self.hitEnemy(e)
                    if not self in bullets:
                        return
        self.specialUpdate()
    def hitEnemy(self, enemy):
        if enemy in enemys and not enemy in self.enemyList:
            enemy.squish += (abs(math.cos(self.angle)) - abs(math.sin(self.angle))) * (self.force / 3) / enemy.weight
            enemy.squash += (abs(math.sin(self.angle)) - abs(math.cos(self.angle))) * (self.force / 3) / enemy.weight
            particles.append(particle(self.x-(enemy.xVel/2), self.y-(enemy.yVel/2), enemy.xVel, enemy.yVel, "circle", [self.color[0], self.color[1], self.color[2], 196], 6, 10, 0.6, fade=25.5, drag=enemy.drag))
            enemy.damaged(self.damage)
            enemy.xVel += math.cos(self.angle) * (self.force / enemy.weight)
            enemy.yVel += math.sin(self.angle) * (self.force / enemy.weight)
            for i in self.effects:
                if random.randrange(0, 100) <= i[1]:
                    index = 0
                    found = False
                    for effect in enemy.effects:
                        if effect.name == i[0](enemy, 0).name:
                            enemy.effects[index] = i[0](enemy, i[2])
                            found = True
                            break
                        index += 1
                    if found == False:
                        enemy.effects.append(i[0](enemy, i[2]))
            if self.pierce > 0:
                self.enemyList.append(enemy)
                self.pierce -= 1
            else:
                self.postEnemyHit()
    def postEnemyHit(self):
        self.delete()
    def specialUpdate(self):
        pass
class effect:
    def __init__(self, name, owner, color, duration):
        self.name = name
        self.owner = owner
        self.color = color
        self.duration = duration
        self.durationTimer = duration
    def update(self):
        self.durationTimer -= 1
        if self.durationTimer < 1:
            self.owner.effects.remove(self)
        self.specialUpdate()
    def specialUpdate(self):
        pass
class onFire(effect):
    def __init__(self, owner, duration):
        self.name = "on fire"
        self.duration = duration
        super().__init__("on fire", owner, (255, 196, 0), duration)
        self.timer = 0
    def specialUpdate(self):
        self.timer -= 1

        if self.timer < 1:
            self.owner.damaged(4)
            self.timer = 50

            for _ in range(10):
                angle = random.uniform(0, math.tau)
                speed = random.uniform(2, 6)
                particles.append(particle(
                    self.owner.x + self.owner.size/2,
                    self.owner.y + self.owner.size/2,
                    math.cos(angle) * speed,
                    math.sin(angle) * speed,
                    "circle",
                    [255, 120, 0, 200],
                    random.uniform(3, 6),
                    20,
                    sizeChange=-0.2,
                    drag=0.8,
                    fade=12
                ))
        if random.random() < 0.6:
            particles.append(particle(
                self.owner.x + random.uniform(0, self.owner.size),
                self.owner.y + random.uniform(0, self.owner.size),
                random.uniform(-2, 2),
                random.uniform(-4, -1),
                "square",
                [255, random.randint(80, 160), 0, random.randrange(120, 255)],
                random.uniform(4, 7),
                40,
                sizeChange=-0.05,
                drag=0.9,
                fade=4
            ))                    
        if random.random() < 0.25:
            particles.append(particle(
                self.owner.x + self.owner.size/2,
                self.owner.y + self.owner.size/2,
                random.uniform(-0.5, 0.5),
                random.uniform(-2, -0.5),
                "circle",
                [60, 60, 60, 80],
                random.uniform(4, 8),
                60,
                sizeChange=0.05,
                drag=0.95,
                fade=2
            ))
class freezing(effect):
    def __init__(self, owner, duration):
        super().__init__("Freezing", owner, (128, 128, 255), duration)
    def specialUpdate(self):
        self.owner.x -= self.owner.xVel / 2
        self.owner.y -= self.owner.yVel / 2
        if random.randrange(0, 4) == 3:
            particles.append(particle(self.owner.x, self.owner.y, random.uniform(-1,1), random.uniform(-1,1),
                                       "square", [128,128,255,255],self.owner.size,10,0,fade=25.5,drag=self.owner.drag))
class gun:
    def __init__(self, owner, bulletStats, firerate, reloadSpeed, magSize, bulletCount, bulletSpread, bulletSpeedSpread, augments):
        self.owner = owner
        self.bulletStats = bulletStats
        self.firerate = firerate
        self.reloadSpeed = reloadSpeed
        self.magSize = magSize
        self.bulletCount = bulletCount
        self.bulletSpread = bulletSpread
        self.bulletSpeedSpread = bulletSpeedSpread
        self.augments = augments
        self.magCount = magSize
        self.reloadTimer = 0
        self.shootTimer = 0
    def shoot(self, direction):
        if self.reloadTimer < 1 and self.shootTimer < 1 and self.magCount > 0:
            for i in range(min(self.bulletCount, self.magCount)):
                spread = ((random.uniform(-self.bulletSpread,self.bulletSpread) + random.uniform(-self.bulletSpread,self.bulletSpread) + random.uniform(-self.bulletSpread,self.bulletSpread) + random.uniform(-self.bulletSpread,self.bulletSpread)) / 4)
                bullets.append(bullet(self.owner.x + (self.owner.size/2), self.owner.y + (self.owner.size/2), self.owner, 
                                      direction+spread,self.bulletStats["size"], 
                                      self.bulletStats["color"],self.bulletStats["trailLength"], self.bulletStats["speed"] - (random.uniform(0, min(self.bulletSpeedSpread * self.bulletStats['speed'] / 20, self.bulletStats["speed"] / 2))),
                                      self.bulletStats["damage"], self.bulletStats["force"],self.bulletStats["effects"], 
                                      self.bulletStats["lifeTime"], self.bulletStats["pierce"]))
                
                self.magCount -= 1
            self.shootTimer = self.firerate
    def update(self):
        if self.reloadTimer > 0:
            self.reloadTimer -= 1
            if self.reloadTimer < 1:
                self.magCount = self.magSize
        if self.shootTimer > 0:
            self.shootTimer -= 1
    def reload(self):
        if self.reloadTimer < 1 and self.magCount < self.magSize:
            self.reloadTimer = self.reloadSpeed
class enemy:
    def __init__(self, x, y, size, colors, shape, maxHealth, speed, attackDelay, damage, drag, weight, exp):
        self.x = x
        self.y = y
        self.size = size
        self.colors = colors
        self.shape = shape
        self.maxHealth = maxHealth
        self.speed = speed
        self.attackDelay = attackDelay
        self.damage = damage
        self.drag = drag
        self.weight = weight
        self.exp = exp

        self.intel = random.randrange(0, 50)
        self.enemyDistance = 0
        for i in range(20):
            self.enemyDistance += random.uniform(0, 10)
        self.enemyDistance /= 20
        self.enemyDistance -= 5
        self.enemyDistance = abs(self.enemyDistance)
        self.hitTimer = 0
        self.xVel = 0
        self.yVel = 0
        self.health = maxHealth
        self.damageFrame = 0
        self.effects = []

        self.squish = 0
        self.squash = 0
    def die(self):
        for _ in range(30):
            angle = random.uniform(0, math.tau)
            speed = random.uniform(3, 12)
            particles.append(particle(self.x + self.size/2, self.y + self.size/2, math.cos(angle) * speed, math.sin(angle) * speed, "square", [*self.colors[0], 255],
                random.uniform(3, 6), random.randint(30, 60), sizeChange=-0.2, drag=0.8, fade=random.uniform(5,7)
            ))

        expToDrop = self.exp
        if expToDrop > 0:
            for i in range(2):
                ammount = min(random.randrange(1, expToDrop), 100)
                pickups.append([self.x + random.uniform(-self.size, self.size), self.y + random.uniform(-self.size, self.size), ammount])
                expToDrop -= ammount
                if expToDrop < 2:
                    break
            while expToDrop > 100:
                pickups.append([self.x + random.uniform(-self.size, self.size), self.y + random.uniform(-self.size, self.size), 100])
                expToDrop -= 100
            pickups.append([self.x + random.uniform(-self.size, self.size), self.y + random.uniform(-self.size, self.size), expToDrop])
        for i in range(3):
            particles.append(particle(self.x + random.uniform(-self.size/2, self.size/2), self.y + random.uniform(-self.size/2, self.size/2), 
                                    random.uniform(-8, 8)+self.xVel, random.uniform(-8, 8)+self.yVel, "square", [*self.colors[1], 255], random.uniform(self.size/3,self.size),
                                    random.randrange(30, 90), 0, [*self.colors[0], 255], (0,0), 0.8, random.randrange(1, 3)))
        self.specialDie()
        self.delete()
    def specialDie(self):
        pass
    def delete(self):
        if self in enemys:
            enemys.remove(self)
    def damaged(self, amount):
        for i in range(3):
            particles.append(particle(self.x + random.uniform(-self.size/2, self.size/2), self.y + random.uniform(-self.size/2, self.size/2), 
                                    random.uniform(-8, 8)+self.xVel, random.uniform(-8, 8)+self.yVel, "square", [*self.colors[1], 255], random.uniform(self.size/4,self.size/2),
                                    random.randrange(30, 90), 0, [*self.colors[0], 255], (0,0), 0.85, random.randrange(10, 20)))
        self.health -= amount
        self.damageFrame = 10
        if self.health < 1:
            self.die()
    def hitPlayer(self):
        if self.hitTimer <= 0:
            p.damaged(self.damage)
            self.hitTimer = self.attackDelay
        angle = math.atan2(p.y - self.y, p.x - self.x)
        p.xVel += math.cos(angle)
        p.yVel += math.sin(angle)
    def specialUpdate(self):
        pass
    def update(self):
        dist = math.dist((p.x, p.y), (self.x, self.y))
        self.x += self.xVel
        self.y += self.yVel
        angle = math.atan2(p.y + (p.yVel * min(self.intel, dist)) - self.y, p.x + (p.xVel * min(self.intel, dist)) - self.x)
        self.xVel += math.cos(angle) * self.speed
        self.yVel += math.sin(angle) * self.speed
        self.xVel *= self.drag
        self.yVel *= self.drag
        self.damageFrame -= 1
        self.hitTimer -= 1
        if dist < self.size:
            self.hitPlayer()
        for i in enemys:
            if i != self:
                dist = math.dist((i.x+(i.size/2), i.y+(i.size/2)), (self.x+(self.size/2), self.y+(self.size/2)))
                if dist < (self.size + i.size)*100:
                    angle = math.atan2(i.y - self.y, i.x - self.x)
                    self.xVel -= (math.cos(angle) / self.weight) / dist * self.enemyDistance
                    self.yVel -= (math.sin(angle) / self.weight) / dist * self.enemyDistance
                    if dist < (self.size + i.size)/2:
                        self.xVel -= (math.cos(angle) / self.weight) * i.weight
                        self.yVel -= (math.sin(angle) / self.weight) * i.weight
        for i in self.effects:
            i.update()
        self.squish += (self.squash - self.squish) / 10
        self.squash += (self.squish - self.squash) / 10

        self.squish *= 0.9
        self.squash *= 0.9
        self.specialUpdate()
    def draw(self):
        if self.shape == "square":
            dSquash = self.squash + 1
            dSquish = self.squish + 1
            if self.damageFrame < 1:
                pygame.draw.rect(win, self.colors[1], (self.x - camX - (self.size/2*self.squash), self.y - camY - (self.size/2*self.squish), self.size*dSquash, self.size*dSquish))
                pygame.draw.rect(win, self.colors[0], (self.x - camX - (self.size/2*self.squash), self.y - camY - (self.size/2*self.squish), self.size*dSquash, self.size*dSquish), 3)
            else:
                pygame.draw.rect(win, (255, 255, 255), (self.x - camX - (self.size/2*self.squash), self.y - camY - (self.size/2*self.squish), self.size*dSquash, self.size*dSquish))
class eBasic(enemy):
    def __init__(self, x, y):
        super().__init__(x, y, 15, [(255,0,0), (64, 0, 0)], "square", 70, 0.8, 15, 5, 0.8, 1, 12)
class eSmall(enemy):
    def __init__(self, x, y):
        super().__init__(x, y, 11, [(0,255,0), (64, 0, 0)], "square", 45, 0.8, 15, 5, 0.8, 1, 6)
class eFast(enemy):
    def __init__(self, x, y):
        super().__init__(x, y, 14, [(0,255,255), (0, 64, 255)], "square", 60, 0.45, 15, 5, 0.9, 0.8, 15)
class eTank(enemy):
    def __init__(self, x, y):
        super().__init__(x, y, 18, [(255, 0, 0), (0, 0, 0)], "square", 120, 0.8, 20, 8, 0.8, 2, 23)
class eStrong(enemy):
    def __init__(self, x, y):
        super().__init__(x, y, 16, [(255, 255, 0), (255, 128, 0)], "square", 100, 0.85, 15, 6, 0.8, 1.2, 25)
class eSlippery(enemy):
    def __init__(self, x, y):
        super().__init__(x, y, 15, [(255, 255, 0), (0, 64, 255)], "square", 60, 0.1, 25, 4, 0.98, 1.2, 28)
        self.intel = 0
class eSkeleton(enemy):
    def __init__(self, x, y):
        super().__init__(x, y, 11, [(255,255,255),(128,128,128)], "square", 40, 0.85, 15, 6, 0.8, 0.5, 0)
class eSteel(enemy):
    def __init__(self, x, y):
        super().__init__(x, y, 22, [(128, 128, 128), (64, 64, 64)], "square", 650, 1.1, 15, 20, 0.7, 8, 34)
class eGold(enemy):
    def __init__(self, x, y):
        super().__init__(x, y, 15, [(255, 255, 0), (196, 196, 0)], "square", 100, 0.8, 15, 5, 0.8, 1, 269)

class eSmart(enemy):
    def __init__(self, x, y):
        super().__init__(x, y, 16, [(0, 255, 255), (128, 0, 128)], "square", 70, 0, 100, 1, 0.85, 1, 30)
        self.takeOver = random.randrange(-90, 90) * (math.pi / 180)
    def specialUpdate(self):
        angle = math.atan2(p.y + ((p.yVel + math.cos(self.takeOver)) * 10) - self.y, p.x + ((p.xVel + math.sin(self.takeOver)) * 10) - self.x)
        dist = math.sqrt(math.dist((self.x + ((p.xVel + math.sin(self.takeOver)) * 10), self.y + ((p.yVel + math.cos(self.takeOver)) * 10)), (p.x + ((p.xVel + math.sin(self.takeOver)) * 10), p.y + ((p.yVel + math.cos(self.takeOver)) * 10))))

        self.xVel += math.cos(angle + (self.takeOver / max(dist / 10, 1))) * 0.6 * min(max(dist/10, 1), 2)
        self.yVel += math.sin(angle + (self.takeOver / max(dist / 10, 1))) * 0.6 * min(max(dist/10, 1), 2)
        dist = math.dist((self.x, self.y), (p.x, p.y))
        self.xVel += math.cos(angle) / dist
        self.yVel += math.sin(angle) / dist


class eDasher(enemy):
    def __init__(self, x, y):
        super().__init__(x, y, 17, [(255,255,255), (0, 0, 0)], "square", 130, 0.9, 30, 10, 0, 1.2, 30)
        self.lifeTime = 0
    def specialUpdate(self):
        self.lifeTime += 1
        self.drag = max(math.sin(self.lifeTime / 50)/1.1, 0.8)
        if self.drag > 0.8:
            particles.append(particle(self.x, self.y, -self.xVel/3, -self.yVel/3, "square", [self.colors[1][0],self.colors[1][1],self.colors[1][2],128],
                                       self.size, 90, 0, [self.colors[0][0],self.colors[0][1],self.colors[0][2],128], fade=10))
class eFrog(enemy):
    def __init__(self, x, y):
        super().__init__(x, y, 13, [(0,128,0), (0, 64, 0)], "square", 90, 0.9, 15, 5, 0, 1.1, 26)
        self.lifeTime = 0
    def specialUpdate(self):
        self.lifeTime += 1
        self.drag = abs(math.sin(self.lifeTime/12))
class eSummoner(enemy):
    def __init__(self, x, y):
        super().__init__(x, y, 17, [(196, 0, 196), (0, 0, 0)], "square", 100, 0.75, 15, 9, 0.8, 1.5, 28)
        self.spawnTimer = 300
    def specialUpdate(self):
        angle = math.atan2(p.y - self.y, p.x - self.x)
        dist = math.dist((self.x, self.y), (p.x, p.y))
        self.xVel -= math.cos(angle)*5 / math.sqrt(dist)
        self.yVel -= math.sin(angle)*5 / math.sqrt(dist)
        if dist < 500:
            self.spawnTimer -= 1
            if self.spawnTimer < 1:
                x = self.x + (math.cos(angle + (math.pi/2)) * 30)
                y = self.y + (math.sin(angle + (math.pi/2)) * 30)
                enemys.append(eSkeleton(x, y))
                for i in range(4):
                    particles.append(particle(x, y, random.uniform(-5, 5), random.uniform(-5, 5), "circle", [255, 0, 255, 128], random.uniform(3,8),
                                              80, -1, drag=0.9,fade=1))
                x = self.x - (math.cos(angle + (math.pi/2)) * 30)
                y = self.y - (math.sin(angle + (math.pi/2)) * 30)
                enemys.append(eSkeleton(x, y))
                for i in range(4):
                    particles.append(particle(x, y, random.uniform(-2, 2), random.uniform(-5, 5), "circle", [255, 0, 255, 128], random.uniform(3,8),
                                              80, -0.3, drag=0.9,fade=1))
                self.spawnTimer = 300
class eFat(enemy):
    def __init__(self, x, y):
        super().__init__(x, y, 22, [(0, 255, 0), (64, 0, 0)], "square", 110, 0.8, 15, 5, 0.8, 1.7, 19)
    def specialDie(self):
        for i in range(3):
            child = eSmall(self.x, self.y)
            child.xVel += random.uniform(-8, 8)
            child.yVel += random.uniform(-8, 8)
            enemys.append(child)
class eVeryFat(enemy):
    def __init__(self, x, y):
        super().__init__(x, y, 40, [(64, 255, 0), (96, 0, 0)], "square", 6000, 0.85, 15, 10, 0.75, 3, 45)
    def specialDie(self):
        for i in range(3):
            child = eFat(self.x, self.y)
            child.xVel += random.uniform(-15, 15)
            child.yVel += random.uniform(-15, 15)
            enemys.append(child)
class eVeryVeryFat(enemy):
    def __init__(self, x, y):
        super().__init__(x, y, 70, [(0, 255, 0), (128, 0, 0)], "square", 40000, 0.7, 15, 10, 0.8, 20, 45)
        self.dashTimer = 0
        self.dashing = False
    def specialUpdate(self):
        if self.dashing:
            if self.dashTimer > 60 * 9:
                self.xVel *= -1
                self.yVel *= -1
            self.dashTimer -= 9
            if self.dashTimer <= 0:
                self.dashing = False
            self.drag = 1
            if round(self.dashTimer/9) % 30 == 1:
                enemys.append(eFat(self.x-self.xVel, self.y-self.yVel))
        else:
            self.dashTimer += 1
            if self.dashTimer > 60 * 9:
                self.dashing = True
            self.drag = 0.8
    def specialDie(self):
        for i in range(3):
            child = eVeryFat(self.x, self.y)
            child.xVel += random.uniform(-15, 15)
            child.yVel += random.uniform(-15, 15)
            enemys.append(child)
class player:
    def __init__(self, x, y, color, speed, drag, gun, augments, maxHealth, size, regen):
        self.x = x
        self.y = y
        self.color = color
        self.speed = speed
        self.drag = drag
        self.gun = gun
        self.augments = augments
        self.maxHealth = maxHealth
        self.health = maxHealth
        self.size = size
        self.regen = regen
        self.effects = []

        self.xVel = 0
        self.yVel = 0
        self.level = 0
        self.maxXP = 50
    def update(self, keys, mousePos, mousePressed):
        moveDir = [0, 0]
        if keys["left"]:
            moveDir[0] -= 1
        if keys["right"]:
            moveDir[0] += 1
        if keys["up"]:
            moveDir[1] -= 1
        if keys["down"]:
            moveDir[1] += 1
        moveAngle = math.atan2(moveDir[1], moveDir[0])
        if moveAngle != 0 or keys["right"]:
            self.xVel += math.cos(moveAngle) * self.speed
            self.yVel += math.sin(moveAngle) * self.speed
        if mousePressed[0]:
            self.gun.shoot(math.atan2(mousePos[1] - ((self.y + (self.size/2)) - camY), mousePos[0] - ((self.x + (self.size/2)) - camX)))
        if keys["reload"]:
            self.gun.reload()
        self.x += self.xVel
        self.y += self.yVel
        self.xVel *= self.drag
        self.yVel *= self.drag
        self.health += self.regen
        if self.health > self.maxHealth:
            self.health = self.maxHealth
    def die(self):
        restartGame()
    def damaged(self, ammount):
        self.health -= ammount
        if self.health <= 0:
            self.die()
    def draw(self):
        pygame.draw.rect(win, (0, 0, 0), (self.x - camX, self.y - camY, self.size, self.size))
        pygame.draw.rect(win, self.color, (self.x - camX, self.y - camY, self.size, self.size), 3)
    def drawUI(self):
        zi = max(min(self.health / self.maxHealth, 1), 0)
        healthColor = (255 - (zi * 255), zi * 255, 0)
        pygame.draw.rect(win, (255, 255, 255), (50, height - 50, width - 100, 15), 5)
        pygame.draw.rect(win, healthColor, (50, height - 50, (width - 100) * zi, 15), 5)

        zi = self.level / self.maxXP
        expColor = (255 * zi, 0, 255)
        pygame.draw.rect(win, (0, 196, 196), (60, height - 20, width - 120, 5))
        pygame.draw.rect(win, expColor, (60, height - 20, (width - 120) * zi, 5))

        font = pygame.font.SysFont('Roboto', 30)
        text = font.render(f"{self.gun.magCount}/{self.gun.magSize}", True, (255, 255, 255))
        textRect = text.get_rect()
        textRect.center = (width - 60, height - 60)
        win.blit(text, textRect)

        if self.gun.reloadTimer > 1:
            pygame.draw.rect(win, (128, 128, 128), (width - 110, height - 80, 100, 10), 3)
            zi = 1 - min(self.gun.reloadTimer / self.gun.reloadSpeed, 1)
            pygame.draw.rect(win, (0, 0, 255), (width - 110, height - 80, 100 * zi, 10), 3)
class upgrade:
    def __init__(self, name, color, description, playerBuffs, gunBuffs, bulletBuffs, augments):
        self.name = name
        self.color = color
        self.description = description
        self.playerBuffs = playerBuffs
        self.gunBuffs = gunBuffs
        self.bulletBuffs = bulletBuffs
        self.augments = augments
    def select(self):
        if "color" in self.playerBuffs:
            p.color = (round((p.color[0] + self.playerBuffs["color"][0]) / 2), round((p.color[1] + self.playerBuffs["color"][1]) / 2), round((p.color[2] + self.playerBuffs["color"][2]) / 2))
        if "speed" in self.playerBuffs:
            p.speed *= self.playerBuffs["speed"]
        if "drag" in self.playerBuffs:
            p.drag *= self.playerBuffs["drag"]
        if "augments" in self.playerBuffs:
            p.augments.extend(self.augments)
        if "maxHealth" in self.playerBuffs:
            p.maxHealth *= self.playerBuffs["maxHealth"]
        if "size" in self.playerBuffs:
            p.size *= self.playerBuffs["size"]

        if "firerate" in self.gunBuffs:
            p.gun.firerate *= self.gunBuffs["firerate"]
        if "magSize" in self.gunBuffs:
            p.gun.magSize *= self.gunBuffs["magSize"]
            p.gun.magSize = round(p.gun.magSize)
            p.gun.magSize = max(p.gun.magSize, 1)
        if "bulletCount" in self.gunBuffs:
            p.gun.bulletCount += self.gunBuffs["bulletCount"]
        if "bulletSpread" in self.gunBuffs:
            p.gun.bulletSpread *= self.gunBuffs["bulletSpread"]
        if "bulletSpeedSpread" in self.gunBuffs:
            p.gun.bulletSpeedSpread *= self.gunBuffs["bulletSpeedSpread"]
        if "reloadSpeed" in self.gunBuffs:
            p.gun.reloadSpeed *= self.gunBuffs["reloadSpeed"]

        if "size" in self.bulletBuffs:
            p.gun.bulletStats["size"] *= self.bulletBuffs["size"]
        if "color" in self.bulletBuffs:
            p.gun.bulletStats["color"] = (round((p.gun.bulletStats["color"][0] + self.bulletBuffs["color"][0]) / 2), round((p.gun.bulletStats["color"][1] + self.bulletBuffs["color"][1]) / 2), round((p.gun.bulletStats["color"][2] + self.bulletBuffs["color"][2]) / 2))
        if "trailLength" in self.bulletBuffs:
            p.gun.bulletStats["trailLength"] *= self.bulletBuffs["trailLength"]
        if "speed" in self.bulletBuffs:
            p.gun.bulletStats["speed"] *= self.bulletBuffs["speed"]
        if "damage" in self.bulletBuffs:
            p.gun.bulletStats["damage"] *= self.bulletBuffs["damage"]
        if "force" in self.bulletBuffs:
            p.gun.bulletStats["force"] *= self.bulletBuffs["force"]
        if "effects" in self.bulletBuffs:
            if not self.bulletBuffs["effects"] in p.gun.bulletStats["effects"]:
                p.gun.bulletStats["effects"].append(self.bulletBuffs["effects"])
        if "lifeTime" in self.bulletBuffs:
            p.gun.bulletStats["lifeTime"] *= self.bulletBuffs["lifeTime"]
        if "pierce" in self.bulletBuffs:
            p.gun.bulletStats["pierce"] += self.bulletBuffs["pierce"]
        self.extraChanges()
    def extraChanges(self):
        pass
    def draw(self, index):
        zi = 1-(upgradeTimer / 60)
        pygame.draw.rect(win, (self.color[1][0]*zi, self.color[1][1]*zi, self.color[1][2]*zi), (index * halfWidth, 0, width/2, height))
        pygame.draw.rect(win, (self.color[0][0]*zi, self.color[0][1]*zi, self.color[0][2]*zi), (index * halfWidth, 0, width/2, height), 6)
        font = pygame.font.SysFont('Roboto', 30)
        text = font.render(self.name, True, (self.color[0][0]*zi, self.color[0][1]*zi, self.color[0][2]*zi))
        textRect = text.get_rect()
        textRect.center = ((index * halfWidth) + (halfWidth/2), height / 4)
        win.blit(text, textRect)

        font = pygame.font.SysFont('Roboto', 20)
        text = font.render(self.description, True, (self.color[0][0]*zi, self.color[0][1]*zi, self.color[0][2]*zi))
        textRect = text.get_rect()
        textRect.center = ((index * halfWidth) + (halfWidth/2), height / 3)
        win.blit(text, textRect)

class uStrongBullet(upgrade):
    def __init__(self):
        super().__init__("Strong Bullet", [(255, 64, 0), (0, 0, 0)], "100% More Bullet Per Bullet!", {}, {"firerate" : 1.3, "reloadSpeed" : 1.1}, {"damage" : 1.9, "force" : 1.4, "color" : (255,64,0), "trailLength" : 1.1, "speed" : 0.93, "lifeTime" : 1.2}, [])
class uExtraBullet(upgrade):
    def __init__(self):
        super().__init__("Extra Bullet", [(0, 255, 128), (0, 0, 0)], "+1 Bullets Fired.", {}, {"firerate" : 1.1, "bulletCount" : 1, "bulletSpread" : 2.1, "bulletSpeedSpread" : 1.9}, {"damage" : 0.8, "trailLength" : 0.8}, [])
class uExtendedMag(upgrade):
    def __init__(self):
        super().__init__("Extened Magazine", [(196, 196, 196), (32, 32, 32)], "x1.8 Magazine Size.", {}, {"magSize" : 1.8, "reloadSpeed" : 1.35}, {}, [])
class uFasterFirerate(upgrade):
    def __init__(self):
        super().__init__("Faster firerate", [(255, 255, 0), (0, 0, 0)], "Squeaky Clean Barrels", {}, {"firerate" : 0.6}, {"force" : 0.85}, [])
class uFasterReload(upgrade):
    def __init__(self):
        super().__init__("Quick Hands", [(0, 255, 0), (0, 0, 0)], "Halves Reload Speed", {}, {"reloadSpeed" : 0.6}, {}, [])
class uSpicyBullets(upgrade):
    def __init__(self):
        super().__init__("Spicy Bullets", [(255, 128, 0), (64, 64, 64)], "Bullets Are Spicy", {}, {"reloadSpeed" : 1.4}, {"effects" : (onFire, 50, 140), "color" : (255, 128, 0)}, [])
class uHighDamageBullets(upgrade):
    def __init__(self):
        super().__init__("High Damage Bullets", [(255, 0, 0), (128, 0, 0)], "x1.5 damage bullets", {}, {"reloadSpeed" : 1.1, "firerate" : 1.2}, {"damage" : 1.5, "color" : (0, 255, 255), "lifeTime" : 1.1}, [])
class uAccuracy(upgrade):
    def __init__(self):
        super().__init__("Improved Accuracy", [(255, 255, 0), (0, 64, 0)], "more accurate shots", {}, {"bulletSpread" : 0.5, "bulletSpeedSpread" : 0.4, "firerate" : 0.85}, {"speed" : 1.1, "lifeTime" : 1.5}, [])
class uPeirce(upgrade):
    def __init__(self):
        super().__init__("Sharp Shots", [(128, 128, 255), (0, 0, 0)], "+1 pierce", {}, {"firerate" : 1.05, "reloadSpeed" : 1.05}, {"pierce" : 1, "trailLength" : 1.2, "color" : (0, 0, 255), "lifeTime" : 1.1}, [])
class uWomboCombo(upgrade):
    def __init__(self):
        super().__init__("Wombo Combo", [(255, 0, 0), (0, 255, 0)], "Combines bullets into 1.", {}, {"reloadSpeed" : 0.9}, {"color" : (0, 255, 0), "lifeTime" : 1.7}, [])
    def extraChanges(self):
        p.gun.bulletStats["damage"] *= p.gun.bulletCount
        p.gun.magSize /= p.gun.bulletCount
        p.gun.bulletCount = 1
        p.gun.magSize = round(p.gun.magSize)
        p.gun.magSize = max(p.gun.magSize, 1)
        
class uChillyBullets(upgrade):
    def __init__(self):
        super().__init__("Chilly Bullets", [(128, 128, 255), (196, 196, 255)], "Bullets Are Chilly", {}, {"reloadSpeed" : 1.4, "magSize" : 0.93, "firerate" : 1.2}, {"speed" : 0.9, "color" : (128, 128, 255), "effects" : (freezing, 60, 160)}, [])
class uShotGun(upgrade):
    def __init__(self):
        super().__init__("Shotgun", [(196, 128, 0), (0, 0, 0)], "Shotgun Effect", {}, {"firerate" : 1.4, "bulletCount" : 3, "bulletSpread" : 10, "bulletSpeedSpread" : 2.6, "reloadSpeed" : 1.3}, {"damage" : 0.7, "lifeTime" : 0.1, "speed" : 1.1, "trailLength" : 1.1, "color" : (196, 196, 128)}, [])
class uSpray(upgrade):
    def __init__(self):
        super().__init__("Spray & Pray", [(64, 196, 255), (0, 0, 64)], "x4 firerate, /2 damage", {}, {"bulletSpread" : 2.5, "bulletSpeedSpread" : 1.2, "firerate" : 0.25, "reloadSpeed" : 1.3, "lifeTime" : 0.8}, {"color" : (255,255,0), "damage" : 0.5, "speed" : 0.95, "trailLength" : 0.6}, [])
class uLazer(upgrade):
    def __init__(self):
        super().__init__("lazer", [(255, 0, 0), (255, 255, 16)], "zippity zippity zap", {}, {"magSize" : 1.1, "reloadSpeed" : 1.4, "firerate" : 0.8, "bulletSpeedSpread" : 0.3}, {"pierce" : 2, "damage" : 0.9, "force" : 0.4, "speed" : 1.2, "trailLength" : 1.1, "color" : (255, 0, 0)}, [])
class uHeavyMagazine(upgrade):
    def __init__(self):
        super().__init__("Heavy Magazine", [(0, 0, 0), (20,20,20)], "2x mag size, increses spread", {}, {"reloadSpeed" : 1.6, "firerate" : 1.1, "bulletSpread" : 2, "bulletSpeedSpread" : 1.2, "magSize" : 2}, {"color" : (30,30,30), "speed" : 0.9}, [])
class uSlugger(upgrade):
    def __init__(self):
        super().__init__("Slugger", [(128,128,128), (64,128,64)], "x2 impactfull", {}, {"magSize" : 0.85, "firerate" : 1.5}, {"force" : 2, "speed" : 0.6, "damage" : 1.2, "color" : (255,255,255), "size" : 1.3, "trailLength" : 0.8, "lifeTime" : 1.2}, [])
upgrades = [uStrongBullet(), uExtraBullet(), uExtendedMag(), uFasterFirerate(), uFasterReload(), uSpicyBullets(), uHighDamageBullets(), uAccuracy(), 
            uPeirce(), uWomboCombo(), uChillyBullets(), uShotGun(), uSpray(), uLazer(), uHeavyMagazine(), uSlugger()]

rounds = [[(eBasic, 100), 400, 90*60], [(eBasic, 50), (eFast, 25), (eTank, 25), 400, 100*60], [(eBasic, 30),(eTank,10),(eFast,10),(eFat, 10),(eStrong, 15), 350, 100*60],
          [(eStrong, 60), (eBasic, 10), (eFast, 10), (eTank, 10), (eFat, 15), (eSlippery, 20), (eSmart, 5), 200, 120*60], [(eStrong, 75), (eTank, 5), (eFast, 5), (eFat, 7), (eSlippery, 7), (eSummoner, 15), (eSteel, 15),(eSmart, 15), 200, 130*60],
          [(eSmart, 80), (eSteel, 20), (eSummoner, 15), (eDasher, 15), (eFrog, 15), (eGold, 10), 100, 140*60],[(eVeryFat, 1), 100*60, 99*60]]

#rounds = [[(eBasic, 100), (eFast, 100), (eTank, 100), (eStrong, 100), (eFat, 100), (eSlippery, 100), (eSteel, 100), (eGold, 100), (eSummoner, 100), (eFrog, 100), (eDasher, 100), 500, 9999999999999999999]]
class spawner:
    def __init__(self, rounds):
        self.rounds = rounds
        self.spawnTimer = 0
        self.roundIndex = 0
        self.roundTimer = self.rounds[self.roundIndex][-1]
    def spawn(self):
        smallest = None
        smallestAmmount = -1
        index = 0
        for i in range(len(self.rounds[self.roundIndex]) - 2):
            spawnChance = random.uniform(0, 1)
            spawnChance *= self.rounds[self.roundIndex][index][1]
            if spawnChance > smallestAmmount:
                smallestAmmount = spawnChance
                smallest = self.rounds[self.roundIndex][index][0]
            index += 1
        if smallest != None:
            a = random.uniform(0, 360) * (math.pi / 180)
            enemys.append(smallest(p.x + (math.cos(a) * 400), p.y + (math.sin(a) * 400)))
    def update(self):
        self.spawnTimer -= 1
        self.roundTimer -= 1
        if self.spawnTimer < 1:
            self.spawn()
            self.spawnTimer = self.rounds[self.roundIndex][-2]
        if self.roundTimer < 1:
            self.roundIndex += 1
            if self.roundIndex > len(self.rounds)-1:
                self.roundIndex = 0
            self.roundTimer = self.rounds[self.roundIndex][-1]
        

defaultBulletStats = {"size" : 4,
                      "color" : (0, 255, 255),
                      "trailLength" : 25,
                      "speed" : 25,
                      "damage" : 10,
                      "force" : 5,
                      "effects" : [],
                      "lifeTime" : 100,
                      "pierce" : 0}

spawn = spawner(rounds)
#enemys.append(enemy(500, 500, 15, [(255,0,0), (64, 0, 0)], "square", 70, 0.75, 15, 5, 0.85, 1, 12))
#enemys.append(enemy(250, 500, 16, [(255,255,0), (255, 128, 0)], "square", 90, 0.8, 15, 5, 0.85, 1, 20))

p = player(0, 0, (0, 255, 255), 0.8, 0.8, None, [], 100, 15, 0.1 / 60)
defaultGun = gun(p, defaultBulletStats, 30, 120, 12, 1, 0.03, 3, [])
p.gun = defaultGun

spawnTimer = 0
t = 0

def restartGame():
    global p, defaultGun, spawnTimer, t, enemys, bullets, pickups, particles, spawn, camX, camY, defaultBulletStats
    defaultBulletStats = {"size" : 4,
                        "color" : (0, 255, 255),
                        "trailLength" : 25,
                        "speed" : 25,
                        "damage" : 10,
                        "force" : 5,
                        "effects" : [],
                        "lifeTime" : 100,
                        "pierce" : 0}
    spawn = spawner(rounds)

    p = player(0, 0, (0, 255, 255), 0.8, 0.8, None, [], 100, 15, 0.1 / 60)
    camX = 0
    camY = 0
    defaultGun = gun(p, defaultBulletStats, 30, 120, 12, 1, 0.03, 3, [])
    p.gun = defaultGun

    spawnTimer = 0
    t = 0

    bullets = []
    enemys = []
    particles = []
    pickups = []

clock = pygame.time.Clock()
run = True
while run:
    win.fill((0, 0, 0))
    particleSurface.fill((0, 0, 0, 0))
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
    keys = pygame.key.get_pressed()
    mousePos = pygame.mouse.get_pos()
    mousePressed = pygame.mouse.get_pressed()
    if not upgrading:
        playerControls = {"left" : keys[pygame.K_a], "right" : keys[pygame.K_d], "up" : keys[pygame.K_w], "down" : keys[pygame.K_s], 
                        "reload" : keys[pygame.K_r]}
        p.update(playerControls, mousePos, mousePressed)
        p.gun.update()
        for i in pickups:
            particles.append(particle(i[0], i[1], random.uniform(-0.5, 0.5), random.uniform(-0.5, 0.5), "circle", [i[2]*2, 0, 255, 170], 2, 25, 
                                      sizeChange=-0.05, fade=6))
            dist = max(math.dist((i[0], i[1]), (p.x, p.y)), 10)
            if dist < p.size:
                p.level += i[2]
                if p.level >= p.maxXP:
                    upgradeTimer = 60
                    upgrading = True
                    upgradeSelections = [*random.choices(upgrades), *random.choices(upgrades)]
                    p.level -= p.maxXP
                    p.maxXP *= 1.14
                pickups.remove(i)
            angle = math.atan2(p.y + (p.size/2) - i[1], p.x + (p.size/2) - i[0])
            i[0] += (math.cos(angle) / min(dist, 200)) * 150
            i[1] += (math.sin(angle) / min(dist, 200)) * 150
        for i in bullets:
            i.update()
        for i in enemys:
            i.update()
        for i in particles:
            i.update()
        spawn.update()
        t += 1
    else:
        if upgradeTimer < 1:
            if mousePressed[0]:
                if mousePos[0] < width/2:
                    upgradeSelections[0].select()
                else:
                    upgradeSelections[1].select()
                upgrading = False
        else:
            upgradeTimer -= 1
    camX += ((p.x + (p.size/2) - (width/2)) - camX) / 15
    camY += ((p.y + (p.size/2) - (height/2)) - camY) / 15
    for i in range(200):
        x = (i * 50 - camX * 0.2) % width
        y = (i * 80 - camY * 0.2) % height
        pygame.draw.circle(win, (10, 10, 20), (x, y), 2)
    pygame.draw.rect(win, (min(round(abs(p.x / 1000)), 255), min(round(abs(p.y / 1000)), 255), 30), ((-camX % (height+20))-20, 0, 20, height))
    pygame.draw.rect(win, (min(round(abs(p.x / 1000)), 255), min(round(abs(p.y / 1000)), 255), 30), ((-camX % (height+20))+halfWidth, 0, 20, height))

    pygame.draw.rect(win, (min(round(abs(p.x / 1000)), 255), min(round(abs(p.y / 1000)), 255), 30), (0, (-camY % (height+20))-20, width, 20))
    p.draw()
    for i in pickups:
        pygame.draw.circle(win, (i[2] * 2.55, 0, 255 - (i[2] * 1.28)), (i[0]-camX, i[1]-camY), max(2, min(5, i[2] / 10)))
    for i in bullets:
        i.draw()
    for i in enemys:
        i.draw()
    for i in particles:
        i.draw()
    win.blit(particleSurface, (0, 0))
    p.drawUI()
    if upgrading:
        upgradeSelections[0].draw(0)
        upgradeSelections[1].draw(1)
    pygame.display.update()
    clock.tick(60)

pygame.quit()
