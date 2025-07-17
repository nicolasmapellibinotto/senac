import pygame
import random
import math
import os
from pygame import mixer

# Inicialização
pygame.init()
mixer.init()

# Configurações
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
FPS = 60
SCROLL_SPEED = 5
pygame.display.set_caption("Galactic Shooter")

# Setup de diretórios (simulado)
assets = {
    'images': {},
    'sounds': {}
}

# Cores
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 50, 50)
BLUE = (50, 50, 255)
GREEN = (50, 255, 50)
YELLOW = (255, 255, 0)
PURPLE = (150, 50, 255)

# Utilitários
def create_simple_surface(size, color):
    surf = pygame.Surface(size, pygame.SRCALPHA)
    pygame.draw.rect(surf, color, (0, 0, *size))
    return surf

# Sistema de Partículas
class ParticleSystem:
    def __init__(self):
        self.particles = []
    
    def add_particles(self, pos, color, count=10, speed=2, life=30, size=3):
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            velocity = [math.sin(angle) * speed, math.cos(angle) * speed]
            self.particles.append({
                'pos': list(pos),
                'velocity': velocity,
                'life': life,
                'max_life': life,
                'color': color,
                'size': size
            })
    
    def update(self):
        for p in self.particles[:]:
            p['pos'][0] += p['velocity'][0]
            p['pos'][1] += p['velocity'][1]
            p['life'] -= 1
            if p['life'] <= 0:
                self.particles.remove(p)
    
    def draw(self, screen):
        for p in self.particles:
            alpha = int(255 * (p['life'] / p['max_life']))
            color = (*p['color'][:3], alpha)
            pygame.draw.circle(screen, color, (int(p['pos'][0]), int(p['pos'][1])), p['size'])

# Entidades do Jogo
class Entity(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, color):
        super().__init__()
        self.image = create_simple_surface((width, height), color)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.mask = pygame.mask.from_surface(self.image)
        self.health = 100

class Player(Entity):
    def __init__(self):
        super().__init__(SCREEN_WIDTH//2, SCREEN_HEIGHT-100, 60, 60, BLUE)
        self.speed = 8
        self.shoot_cooldown = 0
        self.lives = 3
        self.score = 0
        self.power_level = 1
    
    def update(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] and self.rect.left > 0:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT] and self.rect.right < SCREEN_WIDTH:
            self.rect.x += self.speed
        if keys[pygame.K_UP] and self.rect.top > 0:
            self.rect.y -= self.speed
        if keys[pygame.K_DOWN] and self.rect.bottom < SCREEN_HEIGHT:
            self.rect.y += self.speed
        
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
    
    def shoot(self, bullets):
        if self.shoot_cooldown == 0:
            if self.power_level == 1:
                bullets.add(Bullet(self.rect.centerx, self.rect.top, 10, 15, YELLOW, -15))
            elif self.power_level >= 2:
                bullets.add(Bullet(self.rect.centerx-20, self.rect.top, 10, 15, YELLOW, -15))
                bullets.add(Bullet(self.rect.centerx+20, self.rect.top, 10, 15, YELLOW, -15))
                if self.power_level >= 3:
                    bullets.add(Bullet(self.rect.centerx-10, self.rect.top, 10, 15, YELLOW, -15, angle=-15))
                    bullets.add(Bullet(self.rect.centerx+10, self.rect.top, 10, 15, YELLOW, -15, angle=15))
            
            self.shoot_cooldown = 15 - self.power_level

class Bullet(Entity):
    def __init__(self, x, y, width, height, color, speed, angle=0):
        super().__init__(x, y, width, height, color)
        self.speed = speed
        self.angle = math.radians(angle)
    
    def update(self):
        self.rect.x += math.sin(self.angle) * self.speed
        self.rect.y += math.cos(self.angle) * self.speed
        if (self.rect.bottom < 0 or self.rect.top > SCREEN_HEIGHT or 
            self.rect.right < 0 or self.rect.left > SCREEN_WIDTH):
            self.kill()

# Classes dos Inimigos
class Enemy(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, 60, 60, RED)
        self.speed = random.uniform(1, 3)
        self.shoot_timer = random.randint(30, 180)
        self.health = 30
    
    def update(self):
        self.rect.y += self.speed
        self.shoot_timer -= 1
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()
    
    def shoot(self, enemy_bullets):
        if self.shoot_timer <= 0:
            enemy_bullets.add(Bullet(self.rect.centerx, self.rect.bottom, 8, 20, PURPLE, 5))
            self.shoot_timer = random.randint(60, 180)

class Asteroid(Entity):
    def __init__(self, x, y, size):
        colors = [(150, 150, 150), (120, 120, 120), (100, 100, 100)]
        super().__init__(x, y, size, size, random.choice(colors))
        self.speed = random.uniform(1, 3)
        self.rotation = 0
        self.rotation_speed = random.uniform(-3, 3)
        self.health = size
    
    def update(self):
        self.rect.y += self.speed
        self.rotation = (self.rotation + self.rotation_speed) % 360
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()

# Power-ups
class PowerUp(Entity):
    def __init__(self, x, y, type_):
        color = GREEN if type_ == "weapon" else YELLOW if type_ == "life" else BLUE
        super().__init__(x, y, 30, 30, color)
        self.type = type_
        self.speed = 2
    
    def update(self):
        self.rect.y += self.speed
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()

# Inicialização do Jogo
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
clock = pygame.time.Clock()

# Grupos de sprites
all_sprites = pygame.sprite.Group()
player_group = pygame.sprite.Group()
enemies = pygame.sprite.Group()
bullets = pygame.sprite.Group()
enemy_bullets = pygame.sprite.Group()
powerups = pygame.sprite.Group()

# Criar jogador
player = Player()
all_sprites.add(player)
player_group.add(player)

# Sistema de partículas
particles = ParticleSystem()

# Controles
spawn_timer = 0
level = 1
game_over = False
running = True

# Função para mostrar texto
def draw_text(surface, text, size, x, y, color=WHITE):
    font = pygame.font.SysFont('arial', size)
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect()
    text_rect.midtop = (x, y)
    surface.blit(text_surface, text_rect)

# Loop principal
while running:
    # Controle de FPS
    clock.tick(FPS)
    
    # Processar eventos
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            if event.key == pygame.K_SPACE and not game_over:
                player.shoot(bullets)
            if event.key == pygame.K_r and game_over:
                # Reiniciar jogo
                game_over = False
                player.lives = 3
                player.score = 0
                player.power_level = 1
                player.rect.center = (SCREEN_WIDTH//2, SCREEN_HEIGHT-100)
                player_group.add(player)
                all_sprites.add(player)
                for entity in enemies:
                    entity.kill()
                for bullet in enemy_bullets:
                    bullet.kill()
                for bullet in bullets:
                    bullet.kill()
                for powerup in powerups:
                    powerup.kill()
    
    if not game_over:
        # Atualização
        all_sprites.update()
        particles.update()
        
        # Spawn de inimigos
        spawn_timer += 1
        if spawn_timer >= 60 - (level * 2):
            spawn_timer = 0
            if random.random() < 0.7:  # 70% chance de inimigo normal
                enemy = Enemy(random.randint(50, SCREEN_WIDTH-50), -50)
            else:  # 30% chance de asteroide
                size = random.randint(40, 80)
                enemy = Asteroid(random.randint(50, SCREEN_WIDTH-50), -size, size)
            
            all_sprites.add(enemy)
            enemies.add(enemy)
        
        # Disparo dos inimigos
        for enemy in enemies:
            if isinstance(enemy, Enemy) and random.random() < 0.02:
                enemy.shoot(enemy_bullets)
        
        # Spawn de power-ups aleatórios
        if random.random() < 0.005:  # 0.5% chance por frame
            powerup_type = random.choice(["weapon", "life"])
            powerup = PowerUp(random.randint(50, SCREEN_WIDTH-50), -30, powerup_type)
            all_sprites.add(powerup)
            powerups.add(powerup)
        
        # Colisões: Tiro do jogador com inimigos
        hits = pygame.sprite.groupcollide(enemies, bullets, False, True)
        for enemy, bullet_list in hits.items():
            enemy.health -= len(bullet_list) * 10
            for bullet in bullet_list:
                particles.add_particles(bullet.rect.center, YELLOW)
            
            if enemy.health <= 0:
                particle_color = PURPLE if isinstance(enemy, Enemy) else (150, 150, 150)
                particles.add_particles(enemy.rect.center, particle_color, 20, 3, 40, 5)
                player.score += 100 if isinstance(enemy, Enemy) else 50
                enemy.kill()
                
                # Chance de dropar power-up ao morrer
                if isinstance(enemy, Enemy) and random.random() < 0.3:
                    powerup = PowerUp(enemy.rect.centerx, enemy.rect.centery, "weapon")
                    all_sprites.add(powerup)
                    powerups.add(powerup)
        
        # Colisões: Tiro inimigo com jogador
        hits = pygame.sprite.spritecollide(player, enemy_bullets, True, pygame.sprite.collide_mask)
        for bullet in hits:
            player.health -= 10
            particles.add_particles(bullet.rect.center, RED, 10, 2, 20, 3)
            if player.health <= 0:
                player.lives -= 1
                player.health = 100
                particles.add_particles(player.rect.center, BLUE, 30, 4, 60, 5)
                if player.lives <= 0:
                    game_over = True
                    player.kill()
        
        # Colisões: Jogador com inimigos
        hits = pygame.sprite.spritecollide(player, enemies, False, pygame.sprite.collide_mask)
        for enemy in hits:
            player.health -= 20
            enemy.health -= 50
            particles.add_particles(player.rect.center, RED, 20, 3, 40, 4)
            if enemy.health <= 0:
                player.score += 100 if isinstance(enemy, Enemy) else 50
                enemy.kill()
            if player.health <= 0:
                player.lives -= 1
                player.health = 100
                if player.lives <= 0:
                    game_over = True
                    player.kill()
        
        # Colisões: Jogador com power-ups
        hits = pygame.sprite.spritecollide(player, powerups, True, pygame.sprite.collide_mask)
        for powerup in hits:
            if powerup.type == "weapon":
                player.power_level = min(player.power_level + 1, 3)
                particles.add_particles(powerup.rect.center, GREEN, 20, 2, 30, 4)
            elif powerup.type == "life":
                player.lives = min(player.lives + 1, 5)
                particles.add_particles(powerup.rect.center, YELLOW, 20, 2, 30, 4)
        
        # Aumentar nível conforme a pontuação
        level = min(1 + player.score // 2000, 10)
    
    # Desenhar tudo
    screen.fill(BLACK)
    
    # Desenhar fundo estrelado (simulado)
    for _ in range(5):
        pygame.draw.circle(screen, WHITE, 
                          (random.randint(0, SCREEN_WIDTH), 
                           random.randint(0, SCREEN_HEIGHT)), 
                          1)
    
    all_sprites.draw(screen)
    particles.draw(screen)
    enemy_bullets.draw(screen)
    
    # Interface do usuário
    # Barra de vida
    pygame.draw.rect(screen, RED, (10, 10, 200, 20))
    pygame.draw.rect(screen, GREEN, (10, 10, 200 * (player.health/100), 20))
    draw_text(screen, f"HP: {player.health}", 20, 110, 10)
    
    # Vidas
    for i in range(player.lives):
        pygame.draw.circle(screen, BLUE, (30 + i * 40, 50), 15)
    
    # Pontuação e nível
    draw_text(screen, f"Score: {player.score}", 30, SCREEN_WIDTH//2, 10)
    draw_text(screen, f"Level: {level}", 30, SCREEN_WIDTH - 100, 10)
    
    # Power level
    draw_text(screen, f"Power: {'I' * player.power_level}", 20, SCREEN_WIDTH - 100, 50)
    
    # Tela de game over
    if game_over:
        draw_text(screen, "GAME OVER", 64, SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 100, RED)
        draw_text(screen, f"Final Score: {player.score}", 40, SCREEN_WIDTH//2, SCREEN_HEIGHT//2)
        draw_text(screen, "Press R to Restart", 30, SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 80, YELLOW)
    
    pygame.display.flip()

pygame.quit()
