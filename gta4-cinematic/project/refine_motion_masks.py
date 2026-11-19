"""Build the reviewed foreground mattes used in both moving photo intros.

The original JPEGs are never touched. The input mattes are the earlier reviewed
masks or, for the fifteen photographs previously shown as panels, the selected
segmentation candidates in motion_masks_source/. Local hand-drawn corrections
restore details and remove small background islands. Coordinates refer to the
EXIF-oriented thumbnail (at most 768 x 1024), not to generated imagery.

Rebuilding requires only Pillow and NumPy, not the segmentation models.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

SHARED = Path(__file__).resolve().parents[1]
VERSIONS = (SHARED, SHARED / 'dubravnaya')
# Each source name replaces a previous mask or fills a missing one. All others
# come from the already-reviewed intro_masks directory.
SELECTED = {
    'spartak': {
        'IMG_20200819_205213_Original', 'IMG_6871',
        'IMG_20210101_003521_Original', 'IMG_6868', 'IMG_6851',
    },
    'dubravnaya': {
        'IMG_6976', '3a003eeb6f62ae091f04215208f19bec', 'IMG_6659',
        'IMG_6645', 'IMG_6639', 'IMG_6636', 'IMG_6633', 'IMG_6612',
        'IMG_6606', 'IMG_6223',
    },
}


def polygon(mask: Image.Image, points, add=True, feather=.65) -> Image.Image:
    patch = Image.new('L', mask.size)
    ImageDraw.Draw(patch).polygon(points, fill=255)
    if feather:
        patch = patch.filter(ImageFilter.GaussianBlur(feather))
    return ImageChops.lighter(mask, patch) if add else ImageChops.multiply(mask, ImageChops.invert(patch))


def correct(version: str, name: str, mask: Image.Image) -> Image.Image:
    if version == 'dubravnaya' and name == 'IMG_6751':
        # Remove the red pavement below the shoe and between the trouser legs;
        # leave the actual dark footwear and the red light on the clothing.
        mask = polygon(mask, [(0,1024),(0,988),(160,988),(168,989),(176,993),
                              (184,996),(193,1000),(202,1005),(212,1006),
                              (220,1005),(227,1001),(233,994),(245,990),
                              (260,990),(260,1024)], add=False)
        mask = polygon(mask, [(218,747),(223,755),(226,762),(229,770),
                              (231,780),(232,795),(232,814),(230,831),
                              (230,850),(229,865),(225,880),(220,893),
                              (217,888),(219,870),(219,851),(218,830),
                              (217,810),(218,790),(217,770)], add=False)
    if version == 'dubravnaya' and name == 'IMG_6645':
        # Discard the wall above the cap, then restore its original brim,
        # which the initial person mask missed. Both follow source pixels.
        mask = polygon(mask, [(590,0),(768,0),(768,477),(760,474),(740,466),
                              (720,462),(705,462),(690,465),(675,466),
                              (660,466),(650,468),(640,472),(625,476),
                              (610,481),(590,485)], add=False)
        mask = polygon(mask, [(449,553),(452,548),(458,545),(470,543),
                              (485,543),(500,544),(518,545),(532,548),
                              (546,551),(552,556),(553,561),(546,566),
                              (535,568),(517,568),(500,568),(482,567),
                              (468,565),(456,563),(451,560)])
    if version == 'dubravnaya' and name == '3a003eeb6f62ae091f04215208f19bec':
        # Open the small gap between the arm and body rather than retaining
        # a bright triangle of the window and building behind the person.
        mask = polygon(mask, [(310,624),(316,630),(318,640),(318,662),
                              (322,670),(310,679),(306,688),(307,697),
                              (302,701),(293,696),(290,687),(294,676),
                              (300,662),(304,647)], add=False)
    if version == 'dubravnaya' and name == 'IMG_6636':
        # Restore the bottle that the person detector omitted. Fingers and
        # outstretched arms are retained from the pose segmentation.
        mask = polygon(mask, [(250,216),(257,213),(268,217),(287,223),(311,230),
                              (332,237),(346,242),(355,249),(354,258),(343,266),
                              (329,269),(307,263),(286,258),(270,253),(256,248),
                              (248,241),(247,228)])
    if version == 'dubravnaya' and name == 'IMG_6223':
        # Cigarette is thinner than the model's spatial resolution.
        mask = polygon(mask, [(316,588),(328,587),(356,593),(389,600),(419,605),
                              (437,609),(444,613),(443,617),(436,619),(419,615),
                              (387,609),(355,603),(325,597),(316,596)])
        # Remove a tiny isolated wall-colour fragment beside the hair.
        mask = polygon(mask, [(385,315),(435,315),(435,385),(386,385)], add=False)
    if version == 'dubravnaya' and name == 'IMG_6976':
        # The brown cushion behind the sleeper's head was confused with hair.
        # The trace follows the crown, ear and shoulder, leaving the person.
        mask = polygon(mask, [(0,0),(768,0),(768,280),(495,280),(448,293),
                              (410,305),(380,319),(340,333),(311,325),(303,294),
                              (296,260),(283,227),(261,207),(239,184),(210,169),
                              (180,159),(151,157),(115,166),(75,177),(40,188),
                              (0,200)], add=False)
    if version == 'dubravnaya' and name == 'IMG_6639':
        # Discard a triangular piece of wall beside the armchair.
        mask = polygon(mask, [(0,610),(112,610),(108,646),(90,667),(67,691),
                              (43,720),(20,748),(0,772)], add=False)
    if version == 'dubravnaya' and name == 'IMG_6612':
        # Recover the soles of the second man's shoes, rather than making the
        # pair hover with clipped feet. All pixels come from the source photo.
        mask = polygon(mask, [(119,755),(129,750),(144,746),(158,748),(174,754),
                              (190,756),(191,771),(179,778),(151,779),(126,776)])
        mask = polygon(mask, [(196,744),(223,744),(231,751),(235,765),(237,778),
                              (222,784),(203,780),(197,765)])
    if version == 'dubravnaya' and name == 'IMG_6606':
        # The higher person is actually standing on a bin. Retain that prop so
        # both distinct people read as a single photographic moment.
        mask = polygon(mask, [(0,657),(25,643),(50,641),(88,638),(116,634),
                              (160,632),(210,628),(250,619),(305,616),(360,611),
                              (400,609),(424,615),(423,645),(416,678),(407,722),
                              (408,770),(420,830),(435,910),(445,1023),(0,1023)])
        mask = polygon(mask, [(48,523),(58,522),(61,534),(64,548),(70,558),
                              (77,566),(79,583),(80,603),(84,622),(80,638),
                              (72,646),(56,646),(50,640),(48,621),(47,602),
                              (44,579),(44,566),(48,558)])
    if version == 'spartak' and name == 'IMG_20210101_003521_Original':
        # Restore the raised right arm and bottle in the three-person mirror
        # photograph; the automatic mask made them partly transparent.
        mask = polygon(mask, [(487,215),(500,200),(519,185),(538,171),(552,163),
                              (566,156),(566,146),(570,140),(579,136),(589,134),
                              (599,137),(609,135),(605,151),(604,170),(596,184),
                              (585,198),(579,213),(576,234),(574,260),(574,295),
                              (575,328),(575,360),(573,383),(566,393),(555,398),
                              (541,396),(530,392),(516,385),(500,383),(495,369),
                              (507,361),(529,357),(543,355),(547,326),(549,291),
                              (552,259),(556,227),(557,205),(551,201),(537,208),
                              (521,220),(508,230),(496,228)])
        mask = polygon(mask, [(250,127),(258,125),(269,128),(273,140),(279,147),
                              (282,161),(286,177),(289,194),(294,204),(291,210),
                              (267,212),(262,207),(258,194),(253,178),(250,160),
                              (248,145)])
        # The hand resting on the right shoulder was semi-transparent.
        mask = polygon(mask, [(466,382),(489,384),(510,390),(527,400),(542,410),
                              (551,418),(555,426),(553,440),(549,452),(541,462),
                              (532,469),(522,469),(513,471),(502,468),(494,461),
                              (486,448),(479,432),(470,414),(454,406)])
        # Translucent curtain fragments below the arm and beside the trousers.
        mask = polygon(mask, [(558,395),(768,395),(768,1024),(470,1024),
                              (470,850),(473,760),(481,703),(490,681),(504,665),
                              (527,653),(539,634),(544,610),(548,572),(550,530),
                              (551,495),(557,470)], add=False)
        # Clear the remaining wall and curtain between the raised bottle and
        # the two heads without cutting the hair or the bottle outline.
        mask = polygon(mask, [(232,218),(240,213),(249,214),(280,214),
                              (290,212),(308,216),(323,219),(344,224),
                              (343,242),(342,255),(343,280),(345,304),
                              (329,302),(326,283),(322,270),(316,257),
                              (307,246),(295,240),(282,236),(268,235),
                              (254,236),(241,242),(231,252),(224,263),
                              (217,273),(212,271),(214,258),(220,242),
                              (224,232)], add=False)
    if version == 'spartak' and name == 'IMG_20200819_205213_Original':
        # Remove recognisable pieces of foliage left beside the bare torso.
        mask = polygon(mask, [(295,330),(333,330),(337,380),(337,435),(336,485),
                              (339,530),(324,551),(305,551)], add=False)
        mask = polygon(mask, [(552,515),(600,515),(600,665),(541,665),(544,618),
                              (548,570)], add=False)
    if version == 'spartak' and name == 'IMG_6868':
        # Return the white shoe cut away by segmentation. Remove two disconnected
        # ground items; the grill and both people remain.
        mask = polygon(mask, [(145,583),(158,584),(171,588),(179,592),(186,598),
                              (193,603),(194,612),(189,620),(180,624),(163,623),
                              (148,617),(135,612),(130,607),(134,600),(141,596)])
        # The model selected a rectangle of ground beneath the grill. Replace
        # that patch with just its three visible legs, taken from the photo.
        mask = polygon(mask, [(237,626),(321,655),(333,659),(419,600),(438,600),
                              (438,760),(230,760)], add=False)
        mask = polygon(mask, [(237,623),(247,626),(249,700),(246,711),(240,710),(238,684)])
        mask = polygon(mask, [(315,650),(328,651),(328,744),(324,753),(316,752)])
        mask = polygon(mask, [(414,595),(421,591),(421,661),(417,668),(413,663)])
        mask = polygon(mask, [(210,754),(355,754),(355,1023),(210,1023)], add=False)
    if version == 'spartak' and name == 'IMG_6851':
        # The white emblem on the black shirt was misread as a hole.
        mask = polygon(mask, [(250,479),(296,479),(298,536),(250,538)])
        # Preserve the bench behind the two seated men as part of their cutout;
        # without it the figures appear to be sitting in mid-air.
        mask = polygon(mask, [(0,395),(140,395),(240,393),(350,390),(454,386),
                              (448,414),(365,419),(256,422),(140,425),(0,426)])
        mask = polygon(mask, [(0,438),(155,435),(254,427),(352,426),(432,425),
                              (420,465),(305,467),(190,471),(0,476)])
    # Suppress almost-transparent model speckles, not fine, deliberate edges.
    data = np.asarray(mask, dtype=np.uint8).copy()
    data[data < 10] = 0
    return Image.fromarray(data, 'L')


def main():
    for root in VERSIONS:
        version = 'dubravnaya' if root.name == 'dubravnaya' else 'spartak'
        dest = root / 'assets' / 'motion_masks'
        dest.mkdir(parents=True, exist_ok=True)
        photos = sorted((root / 'originals').glob('*.jpeg'))
        if not photos:
            raise FileNotFoundError(f'No originals under {root}')
        for photo in photos:
            name = photo.stem
            folder = 'motion_masks_source' if name in SELECTED[version] else 'intro_masks'
            source = root / 'assets' / folder / f'{name}.png'
            if not source.is_file():
                raise FileNotFoundError(source)
            with Image.open(source) as im:
                result = correct(version, name, im.convert('L'))
            if result.point(lambda p: 255 if p > 85 else 0).getbbox() is None:
                raise ValueError(f'Empty mask: {source}')
            result.save(dest / f'{name}.png', optimize=True)
            print(f'{version}: {name}', flush=True)


if __name__ == '__main__':
    main()
