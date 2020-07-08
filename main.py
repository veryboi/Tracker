from __future__ import print_function
import win32gui
import time
import psutil
import win32process
import win32com.client
import pygame
import math
from pygame.locals import *
import pygame.gfxdraw
import pickle
import os
import signal


(width, height) = (1280, 620)
screen = pygame.display.set_mode((width, height))
r = 300
cx = r + 10
cy = r + 10
colors = [(255, 102, 102), (255, 197, 102), (217, 255, 102), (121, 255, 102), (102, 255, 179), (102, 236, 255), (102, 140, 255), (160, 102, 255)]
bold_colors = [(255, 0, 0), (255, 159, 0), (191, 255, 0), (32, 255, 0), (0, 255, 128), (0, 223, 255), (0, 64, 255), (96,0,255)]
gray = (179, 179, 179)
dark_gray = (128, 128, 128)
_circle_cache = {}
clock = pygame.time.Clock()

def _circlepoints(r):
    r = int(round(r))
    if r in _circle_cache:
        return _circle_cache[r]
    x, y, e = r, 0, 1 - r
    _circle_cache[r] = points = []
    while x >= y:
        points.append((x, y))
        y += 1
        if e < 0:
            e += 2 * y - 1
        else:
            x -= 1
            e += 2 * (y - x) - 1
    points += [(y, x) for x, y in points if x > y]
    points += [(-x, y) for x, y in points if x]
    points += [(x, -y) for x, y in points if y]
    points.sort()
    return points


def render(text, font, gfcolor=pygame.Color('dodgerblue'), ocolor=(255, 255, 255), opx=2):
    textsurface = font.render(text, True, gfcolor).convert_alpha()
    w = textsurface.get_width() + 2 * opx
    h = font.get_height()

    osurf = pygame.Surface((w, h + 2 * opx)).convert_alpha()
    osurf.fill((0, 0, 0, 0))

    surf = osurf.copy()

    osurf.blit(font.render(text, True, ocolor).convert_alpha(), (0, 0))

    for dx, dy in _circlepoints(opx):
        surf.blit(osurf, (dx + opx, dy + opx))

    surf.blit(textsurface, (opx, opx))
    return surf


def time_keeper(seconds):
    day = seconds // (24 * 3600)
    seconds = seconds % (24 * 3600)
    hour = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60
    return "%dd %dh %dm %ds" % (day, hour, minutes, seconds)


def save_obj(obj, name ):
    with open(name + '.pkl', 'wb') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)


def load_obj(name ):
    with open(name + '.pkl', 'rb') as f:
        return pickle.load(f)


def save():
    save_obj(stuff, 'time')
    print("All files saved")



stuff = dict()
seconds = 0
running = True
n = 0
pygame.font.init()

small_font = pygame.font.SysFont("agencyfb", 20)
big_font = pygame.font.SysFont("agencyfb", 40)
biggester_font = pygame.font.SysFont("agencyfb", 64)

if pygame.font.match_font("agencyfb") is None:
    small_font = pygame.font.SysFont("Helvetica", 20)
    big_font = pygame.font.SysFont("Helvetica", 40)
    biggester_font = pygame.font.SysFont("Helvetica", 64)

pygame.init()
pygame.display.set_caption("Usage Tracker")
# print(pygame.font.get_fonts())
oldDelta = time.time()
scroll = 0
process_mod = 0

last_saved = time.time()
print(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'time.pkl'))
if os.path.isfile(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'time.pkl')):
    stuff = load_obj('time')
    print("loaded hash")
    seconds = 0
    for key, val in stuff.items():
        seconds += val[1]
    print("loaded seconds")
else:
    print("created hash")
    save_obj(stuff, 'time')
signal.signal(signal.SIGTERM, save)
signal.signal(signal.SIGINT, save)


while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            save()
        elif event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                running = False
                save()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 4:
                if scroll > 0:
                    scroll -= 1
                    print(scroll)
            if event.button == 5:
                if scroll < 20:
                    scroll += 1
                    print(scroll)
    if process_mod % 1 == 0:
        try:
            pid = win32process.GetWindowThreadProcessId(win32gui.GetForegroundWindow())
            # print(pid)
            x = psutil.Process(pid[-1]).name()
            t = time.time() - oldDelta
            oldDelta = time.time()
            if x in stuff:
                stuff[x][1] += t
                seconds += t
            else:
                stuff[x] = [(0,0,0),t]
                seconds += t
            # print(delta)
        except Exception as e:
            # print(e)
            pass
    if time.time()-last_saved > 10:
        last_saved = time.time()
        save()
    if seconds == 0:
        continue
    screen.fill((255, 255, 255))
    prevAngle = 0
    angles_render = []
    num = 0
    important_seconds = 0
    m_x, m_y = pygame.mouse.get_pos()
    mouse_angle = [False, 0]
    if (cx-m_x) ** 2 + (cy-m_y) ** 2 <= r**2 and (cx-m_x != 0):
        mouse_angle[0] = True
        atan_val = math.atan((cy-m_y)/(cx-m_x)) * 180 / math.pi
        if m_x > cx:
            if atan_val <= 0:
                mouse_angle[1] = -atan_val
            else:
                mouse_angle[1] = -atan_val + 360
        else:
            if atan_val >= 0:
                mouse_angle[1] = -atan_val + 180
            else:
                mouse_angle[1] = -atan_val + 180
        # print(mouse_angle[1])
    selected = [False, "", 0]
    for key, val in sorted(stuff.items(), key=lambda item: item[1][1], reverse=True):
        # print(val[1])
        angle = (360 * val[1])/seconds
        p = [(cx, cy)]
        adder = 0
        adder_diff = 10
        if num == 7:
            if mouse_angle[0]:
                if mouse_angle[1] >= prevAngle:
                    adder = adder_diff
            for n in range(0, math.floor(360 - prevAngle + 1)):
                x = cx + int((r + adder) * math.cos(-(prevAngle + n) * math.pi / 180))
                y = cy + int((r + adder) * math.sin(-(prevAngle + n) * math.pi / 180))
                p.append((x, y))
            p.append((cx + int((r + adder) * math.cos(-(360) * math.pi / 180)),
                      cy + int((r + adder) * math.sin(-(360) * math.pi / 180))))
            p.append((cx, cy))
            if adder == adder_diff:
                selected[0] = True
                selected[1] = "Other"
                selected[2] = seconds-important_seconds
                pygame.draw.polygon(screen, dark_gray, p)
                pygame.gfxdraw.aapolygon(screen, p, dark_gray)
                angles_render.append((dark_gray, "Other ", seconds-important_seconds, adder==adder_diff))
            else:
                pygame.draw.polygon(screen, gray, p)
                pygame.gfxdraw.aapolygon(screen, p, gray)
                angles_render.append((gray, "Other ", seconds - important_seconds, adder == adder_diff))
            break
        if mouse_angle[0]:
            if prevAngle + angle >= mouse_angle[1] >= prevAngle:
                adder= adder_diff
        important_seconds += val[1]
        for n in range(0, math.floor(angle)+1):
            x = cx + int((r + adder) * math.cos(-(prevAngle+n) * math.pi / 180))
            y = cy + int((r + adder) * math.sin(-(prevAngle+n) * math.pi / 180))
            p.append((x, y))
        p.append((cx + int((r + adder) * math.cos(-(prevAngle + angle) * math.pi/180)), cy + int((r + adder) * math.sin(-(prevAngle + angle) * math.pi / 180))))
        p.append((cx, cy))
        if len(p) > 2:
            if adder==adder_diff:
                selected[0] = True
                selected[1] = key
                selected[2] = val[1]
                pygame.draw.polygon(screen, bold_colors[num], p)
                pygame.gfxdraw.aapolygon(screen, p, bold_colors[num])
                angles_render.append((bold_colors[num], key, val[1], adder == adder_diff))
            else:

                pygame.draw.polygon(screen, colors[num], p)
                pygame.gfxdraw.aapolygon(screen, p, colors[num])
                angles_render.append((colors[num], key, val[1], adder == adder_diff))
            # angles_render.append((colors[num], key, val[1], adder==adder_diff))

        prevAngle += angle
        num += 1
        # print("---------")
    pygame.gfxdraw.aacircle(screen, cx, cy, int(3 * r / 4), (255, 255, 255))
    pygame.gfxdraw.filled_circle(screen, cx, cy, int(3 * r / 4), (255, 255, 255))
    if selected[0]:
        txt = big_font.render(selected[1], True, (128, 128, 128))
        txt_rect = txt.get_rect(center=(cx, cy-50))
        pct = biggester_font.render(str(round(100 * selected[2]/ seconds, 2)) + "%", True, (128, 128, 128))
        pct_rect = pct.get_rect(center=(cx, cy))
        screen.blit(pct, pct_rect)
        screen.blit(txt, txt_rect)
    ctr = 0
    anchor = (700, 100)
    for p in angles_render:
        color, txt, p_time, hover = p
        pygame.draw.rect(screen, color, (anchor[0]-20, anchor[1]+ 30 * ctr+5, 15, 15))
        if hover:
            screen.blit(small_font.render(txt.replace(".exe",""), True, (0, 0, 0)), (anchor[0], anchor[1]+ 30 * ctr))
            screen.blit(small_font.render(time_keeper(int(p_time)), True, (0, 0, 0)), (anchor[0]+200, anchor[1] + 30 * ctr) )
            screen.blit(small_font.render( str(round(100 *p_time / seconds, 2)) + "%", True, (0,0,0)), (anchor[0]+340, anchor[1]+30*ctr))
        else:
            screen.blit(small_font.render(txt.replace(".exe",""), True, (130, 130, 130)), (anchor[0], anchor[1] + 30 * ctr))
            screen.blit(small_font.render(time_keeper(int(p_time)), True, (130, 130, 130)), (anchor[0]+200, anchor[1] + 30 * ctr))
            screen.blit(small_font.render(  str(round(100 * p_time / seconds, 2)) + "%", True, (130,130,130)), (anchor[0] + 340, anchor[1] + 30 * ctr))
        ctr += 1
    screen.blit(small_font.render("Total", True, (0,0,0)), (anchor[0], anchor[1] + 30 * ctr))
    screen.blit(small_font.render(time_keeper(int(seconds)), True, (0,0,0)),
                    (anchor[0] + 200, anchor[1] + 30 * ctr))
    # print((delta) - seconds)
    pygame.display.flip()
    clock.tick(60)  # about 60 times per second




    process_mod += 1




