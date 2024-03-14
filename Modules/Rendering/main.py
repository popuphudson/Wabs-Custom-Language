import pygame
win = None
clock = None

def SetMode(args):
    global win
    pygame.init()
    win = pygame.display.set_mode((args[0], args[1]))

def Fill(args):
    global win
    win.fill(args[0])

def DrawRect(args):
    global win
    pygame.draw.rect(win, (args[0][0],args[0][1],args[0][2]), (args[1], args[2], args[3], args[4]))

def UpdateDisplay(args):
    pygame.display.flip()

def SetupClock(args):
    global clock
    clock = pygame.time.Clock()

def Tick(args):
    global clock
    clock.tick(args[0])

def GetEvents(args):
    events = []
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            events.append(["QUIT"])
        elif event.type == pygame.KEYDOWN:
            events.append(["KEYDOWN", event.key])
        elif event.type == pygame.KEYUP:
            events.append(["KEYUP", event.key])
        elif event.type == pygame.MOUSEBUTTONDOWN:
            events.append(["MOUSEDOWN", event.pos, event.button])
        elif event.type == pygame.MOUSEBUTTONUP:
            events.append(["MOUSEUP", event.pos, event.button])
    return events

def GetPressedKeys(args):
    keys = pygame.key.get_pressed()
    return keys

def GetMousePos(args):
    return pygame.mouse.get_pos()

def GetMouseClick(args):
    return pygame.mouse.get_pressed()