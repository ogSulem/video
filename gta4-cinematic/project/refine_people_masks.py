"""Refine saved person mattes without changing the actual photographed people.

The input masks are preserved in assets/intro_masks_initial; hand-traced
corrections are normalized to the EXIF-corrected 768 x 1024 working image.
The output masks can be recreated independently of a neural-network runtime.
"""
from pathlib import Path
import argparse
import cv2
import numpy as np
from PIL import Image, ImageOps

BASE = Path(__file__).resolve().parents[1]


def make_polygon(shape, points):
    h, w = shape
    result = np.zeros(shape, np.uint8)
    pts = np.asarray([[(x * w / 768, y * h / 1024) for x, y in points]], dtype=np.int32)
    cv2.fillPoly(result, pts, 255)
    return result


def remove_above(alpha, xs, ys, start_y=0):
    """Remove background above a traced top edge, without moving any pixels."""
    h, w = alpha.shape
    top = round(start_y * h / 1024)
    for x in range(max(0, round(xs[0] * w / 768)), min(w, round(xs[-1] * w / 768) + 1)):
        y = round(np.interp(x * 768 / w, xs, ys) * h / 1024)
        alpha[top:max(top, min(h, y)), x] = 0


def refine(name, source, alpha):
    if name not in {'IMG_20191118_130227_Original', 'IMG_7373', 'IMG_6853',
                    'IMG_6854', 'IMG_6859', 'IMG_6864', 'IMG_6919', 'IMG_6923',
                    'IMG_7149', 'IMG_6847', 'IMG_6515', 'IMG_6090'}:
        return alpha
    h, w = alpha.shape
    if name in {'IMG_20191118_130227_Original', 'IMG_7373'}:
        # The restored bag/tool is connected to its person. A handful of
        # isolated 1–18 pixel background specks nearby should not be outlined.
        count, labels, stats, _ = cv2.connectedComponentsWithStats((alpha > 30).astype(np.uint8), 8)
        if count > 1:
            largest = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
            keep = (labels == largest).astype(np.uint8) * 255
            keep = cv2.dilate(keep, np.ones((3, 3), np.uint8))
            alpha = np.minimum(alpha, keep)
    if name == 'IMG_6853':
        # Remove dark background above the short hair instead of outlining it
        # as a black cap. The natural hairline and scalp remain in place.
        remove_above(alpha,
                     [340,350,360,370,380,390,400,410,420,430,440,450,460,470,480],
                     [90,65,45,37,32,30,33,37,42,47,52,57,62,72,90])
        # Clear the leafy background leaking through the gap above the raised
        # fingers. Restrict by hue and location, preserving the actual skin.
        hsv = cv2.cvtColor(np.asarray(source), cv2.COLOR_RGB2HSV)
        patch = np.zeros_like(alpha, dtype=bool)
        patch[round(174*h/1024):round(199*h/1024), round(435*w/768):round(495*w/768)] = True
        green = (hsv[:,:,0] >= 25) & (hsv[:,:,0] <= 80) & (hsv[:,:,1] > 45)
        alpha[patch & green] = 0

    if name == 'IMG_6854':
        # The blue wall leaked into the small gap between the two heads.
        rgb = np.asarray(source)
        hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
        region = make_polygon(alpha.shape, [(375,325),(430,325),(421,340),(412,350),
                              (405,362),(399,378),(394,394),(389,410),(385,425),
                              (379,440),(370,452),(366,442),(373,420),(377,390),
                              (378,365),(377,345)]) > 0
        blue = (hsv[:,:,0] >= 95) & (hsv[:,:,0] <= 140) & (hsv[:,:,1] > 50) & (hsv[:,:,2] > 52)
        alpha[region & blue] = 0
        # A blue wall and its bright horizontal seam leaked above the bent
        # right sleeve. Trace the shoulder without touching the face or arm.
        remove_above(alpha,
                     [550,560,570,580,590,600,610,620,630,635,640,645,650,
                      660,670,680,690,700,710,720,730,740,750,760,768],
                     [480,482,485,488,491,494,498,503,512,520,535,538,539,
                      540,541,541,542,543,544,545,546,547,548,549,550],
                     start_y=470)
        # The same model made the actual black sleeve partly transparent.
        # Fill the traced garment so it does not turn into a gray block.
        sleeve = make_polygon(alpha.shape, [(480,470),(505,470),(515,478),(530,477),
                              (540,478),(550,480),(560,482),(570,485),(580,488),
                              (590,491),(600,494),(610,498),(620,503),(630,512),
                              (635,520),(640,535),(645,539),(650,540),(660,541),
                              (680,541),(700,543),(720,545),(740,547),(768,550),
                              (768,575),(700,575),(650,575),(600,575),(550,575),
                              (480,575)])
        alpha = np.maximum(alpha, sleeve)
        # The original white jersey panel was mistakenly made transparent.
        # Restore only its real, traced fabric pixels; retain the bent arm.
        cloth = make_polygon(alpha.shape, [(610,614),(625,614),(640,614),(650,615),
                             (660,617),(670,620),(679,623),(673,635),(665,647),
                             (658,661),(653,672),(650,681),(645,680),(640,678),
                             (635,676),(620,675),(610,675),(600,678),(591,685),
                             (582,694),(576,704),(570,714),(560,720),(560,700),
                             (574,684),(584,667),(594,650),(600,638),(605,626)])
        alpha = np.maximum(alpha, cloth)
        # Remove the car/foliage immediately underneath the extended forearm.
        for x in range(round(680*w/768), w):
            edge = np.interp(x*768/w, [680,690,700,710,720,730,740,750,760,768],
                             [627,629,631,633,635,638,640,641,642,643])
            alpha[round(edge*h/1024):, x] = 0

    if name == 'IMG_6859':
        # Restore the original hair shape that the prior mask clipped off on
        # both sides. No pixels are invented or altered inside the outline.
        hair = make_polygon(alpha.shape, [(422,438),(416,421),(412,410),(410,399),
                            (410,389),(413,378),(418,367),(424,358),(431,351),
                            (440,345),(449,341),(460,339),(473,341),(483,345),
                            (490,349),(494,356),(497,365),(498,375),(499,385),
                            (498,396),(497,407),(493,418),(487,425),(480,430),
                            (478,440),(469,445),(449,445),(433,441)])
        # Confine this to the head so the torso and bag strap stay untouched.
        head = np.zeros_like(alpha, dtype=bool)
        head[round(325*h/1024):round(438*h/1024),
             round(400*w/768):round(520*w/768)] = True
        alpha[head] = hair[head]

    if name == 'IMG_6864':
        # A window and foliage were carried along beside the second person's
        # hair. Follow the actual outer hair edge, stopping before the arm.
        ys = [290,300,310,320,330,340,350,360,370,380,390,400,405,410,415,420,425,430,435,440,445]
        xs = [505,520,530,536,542,546,550,552,553,553,551,549,550,554,564,574,580,585,596,610,625]
        for y in range(round(290*h/1024), min(h, round(446*h/1024))):
            cutoff = round(np.interp(y*1024/h, ys, xs)*w/768)
            alpha[y, cutoff:] = 0

    if name == 'IMG_6919':
        # Remove the bright tree trunk accidentally included behind the hand,
        # following the visible knuckles and shoulder instead of a rectangle.
        ys = [535,550,560,565,570,580,590,600,610,615,618,620,622,625,630]
        xs = [215,215,177,167,156,155,158,165,176,186,185,185,177,160,145]
        for y in range(round(ys[0]*h/1024), min(h, round(ys[-1]*h/1024)+1)):
            cutoff = round(np.interp(y*1024/h, ys, xs)*w/768)
            alpha[y, :cutoff] = 0
        remove_above(alpha, [155,160,170,180,190,200,210,215,220,223],
                     [577,570,566,563,565,568,572,577,580,580])

    if name == 'IMG_6923':
        # Leaves above and behind the bald head were selected as hair.
        remove_above(alpha,
                     [360,370,380,390,400,410,420,430,440,450,460,470,480,490,500],
                     [495,489,483,478,475,473,474,477,480,484,491,500,510,512,520])

    if name == 'IMG_7149':
        # A road sign behind the person's right shoulder leaked into the matte.
        ys = [225,230,235,240,245,250,255,260,265,270,275,280,285,290,295,300,305,310,315,320]
        xs = [567,574,575,581,588,594,594,597,597,602,616,623,628,633,636,638,640,641,643,647]
        for y in range(round(ys[0]*h/1024), min(h, round(ys[-1]*h/1024)+1)):
            cutoff = round(np.interp(y*1024/h, ys, xs)*w/768)
            alpha[y, cutoff:] = 0

    if name == 'IMG_6847':
        # A thin orange lamp pole was incorrectly attached to the top of the
        # cap. Trim it while preserving the original bright cap edge.
        remove_above(alpha, [158,162,166,170,174,178,182],
                     [137,136,135,135,134,134,134])
        # The generic person model omits the backlit long hair. Restore warm
        # photographed strands, not the green foliage visible between them.
        # The soft colour key is confined to two hand-traced regions.
        hair_roi = make_polygon(alpha.shape, [(300,355),(330,355),(345,365),(356,380),
                     (363,395),(364,420),(356,435),(344,444),(355,455),(366,474),
                     (382,489),(379,500),(347,508),(307,512),(295,482),(293,410)])
        hair_roi = np.maximum(hair_roi, make_polygon(alpha.shape, [(21,346),(64,346),
                     (91,363),(104,402),(107,476),(91,500),(67,509),(42,488),
                     (24,460),(18,408)]))
        hsv = cv2.cvtColor(np.asarray(source), cv2.COLOR_RGB2HSV).astype(np.float32)
        hue_key = np.clip((31 - hsv[:,:,0]) / 6, 0, 1)
        light_key = np.clip((hsv[:,:,2] - 48) / 85, 0, 1)
        hair = (hue_key * light_key * hair_roi).astype(np.uint8)
        hair = cv2.GaussianBlur(hair, (0, 0), .55)
        alpha = np.maximum(alpha, hair)

    if name == 'IMG_6515':
        # Exclude the snow above the raised index finger while keeping the
        # finger, glasses and hood. Restore the photographed silver can rim,
        # which person-only segmentation had made partially transparent.
        remove_above(alpha, [310,315,320,325,330,335,340,345,350,355,360,
                             365,370,375,380,385,389],
                     [400,394,391,389,383,376,369,364,362,363,356,
                      355,355,355,355,355,353], start_y=315)
        # The gap inside the bent arm is background, not the person's coat.
        # Trace its boundaries along the photographed wrist and shoulder.
        opening = make_polygon(alpha.shape, [(379,438),(372,440),(362,445),(358,450),
                               (348,455),(337,460),(333,465),(333,470),(329,475),
                               (326,480),(323,485),(318,490),(313,495),(312,500),
                               (307,505),(302,510),(301,513),(308,513),(312,510),
                               (314,505),(319,500),(328,495),(333,490),(339,485),
                               (347,480),(358,475),(378,470),(397,465),(397,460),
                               (397,455),(389,450),(387,445),(382,440)])
        alpha[opening > 0] = 0
        can = make_polygon(alpha.shape, [(320,390),(327,390),(333,391),(338,395),
                           (341,401),(343,409),(343,415),(340,423),(336,429),
                           (330,432),(323,432),(317,428),(313,423),(311,417),
                           (310,409),(311,402),(313,397)])
        finger = make_polygon(alpha.shape, [(329,389),(331,382),(335,376),(340,369),
                              (345,365),(349,364),(353,367),(354,371),(350,378),
                              (346,383),(343,388)])
        alpha = np.maximum.reduce([alpha, can, finger])
        # The bench and snow at the left of the seated figure were merged into
        # the leg/strap edge. Follow the real clothing silhouette instead.
        ys = [735,740,750,760,770,780,790,795,800,805,810,815,820]
        xs = [280,279,276,271,267,259,255,245,220,215,211,204,196]
        for y in range(round(735*h/1024), min(h, round(821*h/1024))):
            cutoff = round(np.interp(y*1024/h, ys, xs)*w/768)
            alpha[y, :cutoff] = 0

    if name == 'IMG_6090':
        # Remove the yellow lamp and window leaking above/along the black hat;
        # the trace follows its real outline and never touches facial pixels.
        remove_above(alpha,
                     [350,355,360,365,370,375,380,385,390,395,400,405,410,415,
                      420,425,430,440,450,460,470,475,480,485,490,495,500,505,510,515,520],
                     [205,178,154,143,132,123,115,107,99,94,90,87,84,82,
                      79,78,77,77,77,77,78,80,83,86,90,95,101,108,117,140,195])
        # Small reflections remained alongside the hat and ears, outside the
        # preceding top trace. Restrict the removal to this head-height band.
        ys = [120,130,140,150,160,170,180,190,200,210,220,230,240,250,260,270,280]
        left = [379,374,369,364,361,358,358,355,354,354,354,350,350,354,359,363,362]
        right = [510,513,514,517,518,518,518,518,521,521,521,517,513,513,510,508,506]
        for y in range(round(120*h/1024), min(h, round(281*h/1024))):
            yy = y*1024/h
            lo = round(np.interp(yy, ys, left)*w/768)
            hi = round(np.interp(yy, ys, right)*w/768)
            alpha[y, :lo] = 0
            alpha[y, hi:] = 0

    # Small feather only at the edited boundaries; source RGB remains intact.
    return cv2.GaussianBlur(alpha, (0, 0), .45)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=BASE/'assets'/'intro_masks')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    for p in sorted((BASE/'assets'/'intro_masks_initial').glob('*.png')):
        photo = BASE/'originals'/f'{p.stem}.jpeg'
        im = ImageOps.exif_transpose(Image.open(photo)).convert('RGB')
        alpha = np.array(Image.open(p).convert('L'))
        im = im.resize((alpha.shape[1], alpha.shape[0]), Image.Resampling.LANCZOS)
        Image.fromarray(refine(p.stem, im, alpha)).save(args.output/p.name, optimize=True)
        print(p.stem, flush=True)


if __name__ == '__main__':
    main()
