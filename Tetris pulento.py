#Autores: Christopher Cardenas y Alex Contreras
from typing import ChainMap
from pygame.constants import KEYDOWN
from pygame.time import Clock
import numpy as np
#import cv2
import threading
import time
import pygame
import random

pygame.font.init()

from pygame.locals import *
pygame.init()

# Variables Globales

#*Tetris original es un 10x20
#Variables de la pantalla y bloques:

p_ancho = 1550 # Ancho de la pantalla (total)
p_altura = 1000 # Altura de la pantalla (total)
play_ancho = 540  #  30 * 18 = 540 bloques de altura
play_altura = 930  # 30 * 31 = 930 bloques de altura
t_bloque = 30 # Tamaño del bloque
pos_pant_x = (p_ancho - play_ancho) // 2 # Posicion en pantalla (eje x)
pos_pant_y = (p_altura - play_altura) // 2 # Posicion en pantalla (eje y)

#Mouse pulento
pygame.mouse.set_cursor(pygame.cursors.diamond)

# Formas de las figuras

S = [['.....',
      '.....',
      '..00.',
      '.00..',
      '.....'],
     ['.....',
      '..0..',
      '..00.',
      '...0.',
      '.....']] 
      
Z = [['.....',
      '.....',
      '.00..',
      '..00.',
      '.....'],
     ['.....',
      '..0..',
      '.00..',
      '.0...',
      '.....']]

I = [['..0..',
      '..0..',
      '..0..',
      '..0..',
      '.....'],
     ['.....',
      '0000.',
      '.....',
      '.....',
      '.....']]

O = [['.....',
      '.....',
      '.00..',
      '.00..',
      '.....']]

J = [['.....',
      '.0...',
      '.000.',
      '.....',
      '.....'],
     ['.....',
      '..00.',
      '..0..',
      '..0..',
      '.....'],
     ['.....',
      '.....',
      '.000.',
      '...0.',
      '.....'],
     ['.....',
      '..0..',
      '..0..',
      '.00..',
      '.....']]

L = [['.....',
      '...0.',
      '.000.',
      '.....',
      '.....'],
     ['.....',
      '..0..',
      '..0..',
      '..00.',
      '.....'],
     ['.....',
      '.....',
      '.000.',
      '.0...',
      '.....'],
     ['.....',
      '.00..',
      '..0..',
      '..0..',
      '.....']]

T = [['.....',
      '..0..',
      '.000.',
      '.....',
      '.....'],
     ['.....',
      '..0..',
      '..00.',
      '..0..',
      '.....'],
     ['.....',
      '.....',
      '.000.',
      '..0..',
      '.....'],
     ['.....',
      '..0..',
      '.00..',
      '..0..',
      '.....']]

# 0 = RGB (200,200,200) (Bloque exterior) 1 = (128,128,128) (Bloque interior) 2 = (20,20,250) 3 = ( 20,250,20)
# 4 = (250,20,20) 5 = (240,240,30) 6 = (250,30,240) 7 = (30,240,240)

figuras = [S, Z, I, O, J, L, T]
color_figura = [(20,20,250),(20,250,20),(250,20,20),(240,240,30),(250,30,240),(170,20,170),(0,200,140)]

# Clase de pieza
class Pieza(object):
    def __init__(self, x, y, figura):
        self.x = x
        self.y = y
        self.figura = figura
        self.color = color_figura[figuras.index(figura)]
        self.rotacion = 0

#Creacion del tablero de juego
def crear_tablero(pos_invalida={}):
    # una lista por linea y fila respectivamente
    tablero = [[(128,128,128) for _ in range(18)] for _ in range(31)]
    for i in range(len(tablero)):
        for j in range(len(tablero[i])):
            if (j, i) in pos_invalida:
                c = pos_invalida[(j,i)]
                tablero[i][j] = c
    return tablero

# Spawn de la figura, que al ser un x=18, no hay como poner el spawn al medio justo.
def formato_figura (figura): 
    posiciones = []
    format = figura.figura[figura.rotacion % len(figura.figura)]

    for i, line in enumerate(format):
        row = list(line)
        for j, column in enumerate(row):
            if column == '0':
                posiciones.append((figura.x + j+4, figura.y + i))

    for i, pos in enumerate(posiciones):
        posiciones[i] = (pos[0] - 2, pos[1] - 4)

    return posiciones

# Creacion del espacio valido donde se pueden mover las figuras
def espacio_valido (figuras, tablero):
    posicion_acept = [[(j, i) for j in range(18) if tablero[i][j] == (128,128,128)] for i in range(31)]
    posicion_acept = [j for sub in posicion_acept for j in sub] 

    formateo = formato_figura(figuras)   

    for pos in formateo:
        if pos not in posicion_acept:
            if pos[1] > -1:
                return False
    return True


def check_perdido (posiciones):
    for pos in posiciones:
        x, y = pos
        if y < 1:
            return True
    return False

# Buscador de forma
def get_forma():
    return Pieza(5, 0, random.choice(figuras))

# Impresion de texto
def texto_medio (surface, text, size, color):  
    font = pygame.font.SysFont("bahnschrift", size, bold=True)
    label = font.render(text, 1, color)

    surface.blit(label, (pos_pant_x + play_ancho /2 - (label.get_width()/2), pos_pant_y + play_altura/2 - label.get_height()/2))

# Creacion de la red del tablero
def crear_red(surface, tablero):
    sx = pos_pant_x
    sy = pos_pant_y
    # Creacion de la red que separa los bloques
    for i in range(len(tablero)):
        pygame.draw.line(surface, (0,0,0), (sx, sy + i*t_bloque), (sx+play_ancho, sy+ i*t_bloque))
        for j in range(len(tablero[i])):
            pygame.draw.line(surface, (0,0,0), (sx + j*t_bloque, sy),(sx + j*t_bloque, sy + play_altura))

# Limpieza de lineas completas
def limpia_lineas(tablero, locked):

    inc = 0
    for i in range(len(tablero)-1, -1, -1):
        row = tablero[i]
        if (128,128,128) not in row:
            inc += 1
            ind = i
            for j in range(len(row)):
                try:
                    del locked[(j,i)]
                except:
                    continue

    if inc > 0:
        for key in sorted(list(locked), key=lambda x: x[1])[::-1]:
            x, y = key
            if y < ind:
                newKey = (x, y + inc)
                locked[newKey] = locked.pop(key)

    return inc

 # Dibujo de la siguiente figura
def sig_figura(figura, surface): 
    font = pygame.font.SysFont('bahnschrift', 30)
    label = font.render('Siguiente figura:', 1, (255,255,255))

    sx = pos_pant_x + play_ancho + 60
    sy = pos_pant_y + play_altura/2 - 100
    format = figura.figura[figura.rotacion % len(figura.figura)]

    for i, line in enumerate(format):
        row = list(line)
        for j, column in enumerate(row):
            if column == '0':
                pygame.draw.rect(surface, figura.color, (sx + j*t_bloque, sy + i*t_bloque, t_bloque, t_bloque), 0)

    surface.blit(label, (sx + 10, sy - 40))

# Puntaje maximo
def cambiar_puntaje(nscore): 
    score = max_puntaje()

    with open('Puntaje.txt', 'w') as f:
        if int(score) > nscore:
            f.write(str(score))
        else:
            f.write(str(nscore))


def max_puntaje(): 
    with open('Puntaje.txt', 'r') as f:
        lines = f.readlines()
        score = lines[0].strip()

    return score
###
# Funcion de pausa
def pausa():
    pausado = True
    while pausado:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_c:
                    pausado = False
                elif event.key == pygame.K_q:
                    pygame.quit()
                    quit()
        win.fill((250,250,250))
        texto_medio (win, 'Juego Pausado, C: continuar / Q: salir', 45, (0,0,0))
        pygame.display.update()
        pygame.time.Clock()

def ventana(surface, tablero, score=0, last_score = 0):
    surface.fill((200,200,200))
    pygame.font.init()
    font = pygame.font.SysFont('bahnschrift', 60)
    
    #Puntaje Actual
    font = pygame.font.SysFont('bahnschrift', 30)
    label = font.render('Puntaje: ' + str(score), 1, (255,255,255))

    sx = pos_pant_x + play_ancho + 50
    sy = pos_pant_y + play_altura/2 - 100
    surface.blit(label, (sx + 20, sy + 160))
    
    #Ultimo puntaje
    label = font.render('Max. puntaje registrado: ' + last_score, 1, (255,255,255))
    sx = pos_pant_x - 430
    sy = pos_pant_y + 200
    surface.blit(label, (sx + 20, sy + 160))

    #Aviso de pausa
    label = font.render('Para pausar presiona P', 1, (255,255,255))
    sx = pos_pant_x - 430
    sy = pos_pant_y + 50
    surface.blit(label, (sx + 20, sy + 160))
    
    #Impresion del area ploma de la zona jugable
    for i in range(len(tablero)):
        for j in range(len(tablero[i])):
            pygame.draw.rect(surface, tablero[i][j], (pos_pant_x + j*t_bloque, pos_pant_y + i*t_bloque, t_bloque, t_bloque), 0)

    for i in range(len(tablero)):
        for j in range(len(tablero[i])):
            pygame.draw.rect(surface, tablero[i][j], (pos_pant_x + j*t_bloque, pos_pant_y + i*t_bloque, t_bloque, t_bloque), 0)

    #Borde
    pygame.draw.rect(surface, (255,255,255), (pos_pant_x, pos_pant_y, play_ancho, play_altura), 5)
    crear_red(surface, tablero)




def main(win):
    last_score = max_puntaje()
    posiciones_invalidas = {}
    tablero = crear_tablero(posiciones_invalidas)

    piez_sig = False
    run = True
    piez_actual = get_forma()
    piez_q_sigue = get_forma()
    clock = pygame.time.Clock()
    fall_time = 0
    fall_speed = 0.2
    level_time = 0
    score = 0



    while run:
        tablero = crear_tablero(posiciones_invalidas)
        fall_time += clock.get_rawtime()
        level_time += clock.get_rawtime()
        clock.tick()

        ## inicio del control del mouse
        
        clicking = False
        right_clicking = False
        middle_click = False
        mx, my = pygame.mouse.get_pos()
        posM = [mx,my]
        
        ##

        if level_time/1000 > 5:
            level_time = 0
            if level_time > 0.12:
                level_time -= 0.005

        if fall_time/1000 > fall_speed:
            fall_time = 0
            piez_actual.y += 1
            if not(espacio_valido(piez_actual, tablero)) and piez_actual.y > 0:
                piez_actual.y -= 1
                piez_sig = True

        for event in pygame.event.get():
            # Que pasa al apretar cada tecla (eventos), incluidas excepciones para que las piezas no se atraviesen entre ellas
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    piez_actual.x -= 1
                    if not(espacio_valido(piez_actual, tablero)):
                        piez_actual.x += 1
                if event.key == pygame.K_RIGHT:
                    piez_actual.x += 1
                    if not(espacio_valido(piez_actual, tablero)):
                        piez_actual.x -= 1
                if event.key == pygame.K_DOWN:
                    #velocidad de caida (rango = 5)
                    for i in range (0,5):
                        piez_actual.y += 1
                        if not(espacio_valido(piez_actual, tablero)):
                            piez_actual.y -= 1
                if event.key == pygame.K_d:
                    piez_actual.rotacion += 1
                    if not(espacio_valido(piez_actual, tablero)):
                        piez_actual.rotacion -= 1
                if event.key == pygame.K_a:
                    piez_actual.rotacion -= 1
                    if not(espacio_valido(piez_actual, tablero)):
                        piez_actual.rotacion += 1
                if event.key == pygame.K_p:
                    pausa()
            #controles del mouse

            if event.type == MOUSEBUTTONDOWN:
                if event.button == 1 :
                    clicking = True
                if event.button == 3:
                    right_clicking = True
                if event.button == 2: #boton del medio
                    middle_click = True
                #if event.button == 4: #Scroll up
                    #beta
                if event.button == 5: #Scroll down
                    for i in range (0,5):
                        piez_actual.y += 1
                        if not(espacio_valido(piez_actual, tablero)):
                            piez_actual.y -= 1

            if clicking:
                piez_actual.x -= 1
                if not(espacio_valido(piez_actual, tablero)):
                    piez_actual.x += 1
            if right_clicking:
                piez_actual.x += 1
                if not(espacio_valido(piez_actual, tablero)):
                    piez_actual.x -= 1
            if middle_click:
                piez_actual.rotacion += 1
                if not(espacio_valido(piez_actual, tablero)):
                    piez_actual.rotacion -= 1
                    
            if event.type == MOUSEBUTTONUP:
                if event.button == 1:
                    clicking = False
                if event.button == 3:
                    right_clicking = False
                if event.button == 2:
                    middle_clicking = False

            #fin controles mouse
                    

        pos_figura = formato_figura(piez_actual)

        for i in range(len(pos_figura)):
            x, y = pos_figura[i]
            if y > -1:
                tablero[y][x] = piez_actual.color

        if piez_sig:
            for pos in pos_figura:
                p = (pos[0], pos[1])
                posiciones_invalidas[p] = piez_actual.color
            piez_actual = piez_q_sigue
            piez_q_sigue = get_forma()
            piez_sig = False
            score += limpia_lineas(tablero, posiciones_invalidas) * 100

        ventana(win, tablero, score, last_score)
        sig_figura(piez_q_sigue, win)
        pygame.display.update()

        if check_perdido(posiciones_invalidas):
            texto_medio(win, "GAME OVER!", 80, (255,255,255))
            pygame.display.update()
            pygame.time.delay(1500)
            run = False
            cambiar_puntaje(score)


def main_menu(win):
    texto_medio(win, "Izq y Der para mover / A y D para girar", 45, (255,255,255))
    pygame.display.update()
    pygame.time.delay(2000)
    # Musica de fondo
    pygame.mixer.music.load('tetris99.mp3')
    pygame.mixer.music.play(-1)
    pygame.mixer.music.set_volume(0.11)
    run = True
    while run:
        win.fill((0,0,0))
        texto_medio(win, 'Presione cualquier tecla para iniciar partida', 55, (255,255,255))
        
        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if event.type == pygame.KEYDOWN:
                main(win)

    pygame.display.quit()


win = pygame.display.set_mode((p_ancho, p_altura))
pygame.display.set_caption('Tetris Acuenta')
main_menu(win)
