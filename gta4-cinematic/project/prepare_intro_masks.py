"""Prepare photographed-person masks for the GTA IV-inspired intro.

The video renderer uses the saved PNG masks and does *not* require MediaPipe.
Regenerating masks is optional and requires mediapipe==0.10.21 and OpenCV.
No face generation or face replacement is used. All RGB pixels remain the
provided photographs; the masks only select the foreground.
"""
from pathlib import Path
import cv2
import mediapipe as mp
import numpy as np
from PIL import Image, ImageFilter, ImageOps

BASE = Path(__file__).resolve().parents[1]
OUT = BASE / "assets" / "intro_masks"
# Individual regions are used only when the subject is very small or when an
# original mirror background would otherwise be mistaken for the subject.
ROIS = {
    "IMG_7373": (0.35, 0.30, 0.78, 0.89),
    "IMG_6779": (0.08, 0.16, 0.95, 1.00),
    "IMG_6919": (0.05, 0.39, 0.94, 1.00),
}
# Two earlier hand-checked/GrabCut-refined masks from this project.
REFINED = {"IMG_6782", "IMG_7149"}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with mp.solutions.selfie_segmentation.SelfieSegmentation(model_selection=0) as model:
        for path in sorted((BASE / "originals").glob("*.jpeg")):
            im = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
            im.thumbnail((768, 1024), Image.Resampling.LANCZOS)
            w, h = im.size
            if path.stem in REFINED:
                mask = Image.open(BASE / "assets" / "masks" / f"{path.stem}_mask.png").convert("L").resize(im.size)
                alpha = np.array(mask)
            else:
                roi = ROIS.get(path.stem, (0., 0., 1., 1.))
                box = (round(roi[0] * w), round(roi[1] * h), round(roi[2] * w), round(roi[3] * h))
                crop = np.asarray(im.crop(box))
                prob = model.process(crop).segmentation_mask
                selected = (np.clip((prob - .26) / .50, 0, 1) * 255).astype(np.uint8)
                alpha = np.zeros((h, w), np.uint8)
                alpha[box[1]:box[3], box[0]:box[2]] = selected

            # Retain all substantial connected components, for images with more
            # than one person, while removing isolated segmentation debris.
            count, labels, stats, _ = cv2.connectedComponentsWithStats((alpha > 75).astype(np.uint8), 8)
            if count > 1:
                largest = max(stats[1:, cv2.CC_STAT_AREA])
                keep = np.zeros_like(alpha)
                for k in range(1, count):
                    if stats[k, cv2.CC_STAT_AREA] >= largest * 0.012:
                        keep[labels == k] = 255
                keep = cv2.dilate(keep, np.ones((3, 3), np.uint8))
                alpha = np.minimum(alpha, keep)

            if path.stem == "IMG_7373":
                # Restore the original orange tool (foreground, not a new asset)
                # that generic person segmentation tends to exclude.
                hsv = cv2.cvtColor(np.asarray(im), cv2.COLOR_RGB2HSV)
                orange = cv2.inRange(hsv, (3, 110, 105), (19, 255, 255))
                area = np.zeros_like(orange)
                area[round(h * .39):round(h * .46), round(w * .34):round(w * .76)] = 255
                tool = cv2.morphologyEx(cv2.bitwise_and(orange, area), cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
                # Keep the grasping hand and the thin shaft together, using
                # only their actual pixels from the source image.
                shaft = np.zeros_like(alpha)
                # Coordinates trace the visible shaft and the hand that grips
                # it; avoid copying a rectangular slab of background.
                trace=[(338,430),(370,429),(370,421),(390,417),(402,423),
                       (540,408),(544,446),(526,447),(524,438),(480,447),
                       (473,437),(454,434),(419,440),(402,443),(404,451),
                       (390,454),(378,449),(375,444),(339,445)]
                pts=np.array([[(x*w/768,y*h/1024) for x,y in trace]],dtype=np.int32)
                cv2.fillPoly(shaft,pts,255)
                alpha = np.maximum.reduce([alpha, tool, shaft])
                # Refine the left contour of the helmet against the white
                # machinery behind it; retain the actual face pixels untouched.
                knots_y=np.array([0,337,338,340,345,350,355,360,365,370,375,380,390,400,410,414],dtype=float)
                knots_x=np.array([768,768,420,418,410,405,402,399,398,397,395,396,399,402,405,405],dtype=float)
                for yy in range(min(round(414*h/1024),h)):
                    cutoff=int(np.interp(yy*1024/h,knots_y,knots_x)*w/768)
                    alpha[yy,:cutoff]=0
                # Remove the pale machinery immediately above the hard hat,
                # whose actual orange edge has much stronger colour saturation.
                patch = np.zeros_like(alpha, dtype=bool)
                patch[round(337*h/1024):round(345*h/1024),
                      round(400*w/768):round(435*w/768)] = True
                alpha[patch & (hsv[:,:,1] < 65)] = 0
            if path.stem == "IMG_6853":
                # Small background remnant above the head, outside the subject.
                alpha[:round(h * .018), :] = 0

            def polygon(points, value=255):
                """Draw a traced patch in the 768×1024 thumbnail coordinates."""
                stencil = np.zeros_like(alpha)
                pts = np.array([[(x*w/768, y*h/1024) for x, y in points]], dtype=np.int32)
                cv2.fillPoly(stencil, pts, value)
                return stencil

            if path.stem == "IMG_7373":
                # The small raised arm is translucent in the generic model.
                # Restore its natural silhouette from the source pixels.
                arm = polygon([(341,451),(344,451),(346,456),(345,464),(346,468),
                               (350,468),(355,468),(359,472),(360,476),(357,481),
                               (358,485),(362,490),(370,496),(381,501),(392,504),
                               (399,501),(404,497),(410,503),(412,515),(405,522),
                               (397,529),(389,528),(379,524),(369,518),(360,511),
                               (353,503),(348,494),(345,485),(340,480),(338,475),
                               (340,468)])
                alpha = np.maximum(alpha, arm)

            if path.stem == "IMG_20191118_130227_Original":
                # The person's hand holds a pale bag; the model mistook the car
                # for foreground and dropped most of the bag. Remove the car
                # fragment and retain the actual hand/bag pixels as one shape.
                alpha[round(195*h/1024):round(281*h/1024), round(410*w/768):round(540*w/768)] = 0
                bag = polygon([(458,313),(469,303),(476,292),(484,290),(491,300),
                               (499,307),(504,318),(505,340),(507,368),(510,394),
                               (513,424),(521,456),(508,437),(496,418),(487,411),
                               (466,412),(455,407),(450,400),(447,383),(444,363),
                               (440,348),(437,337),(441,326),(450,320)])
                alpha = np.maximum(alpha, bag)

            if path.stem == "IMG_6779":
                # A mirror edge was erroneously included above the hair. Trace
                # its right silhouette while preserving the face and hair.
                alpha[:round(253*h/1024), :] = 0
                ys = [253,255,260,265,270,275,280,285,290,295,300,305,310,315,320,325,330]
                xs = [446,452,465,474,481,487,493,498,503,506,510,512,514,516,516,516,515]
                for yy in range(round(253*h/1024), min(round(331*h/1024), h)):
                    cutoff = round(np.interp(yy*1024/h, ys, xs)*w/768)
                    alpha[yy, cutoff:] = 0
                # Restore the real phone. Without it the selected fingers look
                # incomplete; the shape is traced from the source photograph.
                phone = polygon([(464,438),(465,432),(469,427),(473,425),(524,425),
                                 (532,427),(536,432),(538,438),(539,491),(535,497),
                                 (525,490),(509,484),(492,479),(476,477),(464,479)])
                alpha = np.maximum(alpha, phone)

            if path.stem == "IMG_6759":
                # In this backlit group photo, remove roof fragments around the
                # middle person's head and the bright background visible through
                # the arm opening. The original people and grill stay intact.
                alpha[:round(252*h/1024), round(330*w/768):round(445*w/768)] = 0
                alpha[:round(263*h/1024), round(315*w/768):round(350*w/768)] = 0
                # Clear the dark roof between the left head, the grill edge,
                # and the middle head; the lower diagonal follows the grill.
                roof = polygon([(313,240),(371,240),(371,260),(368,264),(365,270),
                                (363,278),(360,286),(358,292),(356,299),(350,294),
                                (343,288),(335,282),(327,277),(319,272),(313,268)])
                alpha[roof > 0] = 0
                gap = polygon([(410,252),(440,252),(438,265),(434,279),(432,295),
                               (432,310),(434,321),(438,333),(431,343),(424,335),
                               (422,322),(422,309),(423,295),(423,282),(421,271),
                               (417,261)])
                alpha[gap > 0] = 0
                # Trace just outside the head and adjacent shoulder so bright
                # roof pieces do not create white islands around the people.
                for yy in range(round(252*h/1024), min(round(283*h/1024), h)):
                    edge = np.interp(yy*1024/h, [252,255,260,265,270,275,280,282],
                                     [392,382,372,367,365,363,362,360])
                    alpha[yy, round(350*w/768):round(edge*w/768)] = 0
                for yy in range(round(289*h/1024), min(round(347*h/1024), h)):
                    edge = np.interp(yy*1024/h, [289,300,310,320,330,340,346],
                                     [460,454,448,444,442,439,438])
                    alpha[yy, round(425*w/768):round(edge*w/768)] = 0
                opening = polygon([(624,393),(631,395),(635,400),(638,410),(640,425),
                                   (642,440),(643,455),(643,471),(642,481),(638,491),
                                   (634,499),(631,493),(629,481),(628,466),(627,451),
                                   (626,435),(625,420),(624,405)])
                alpha[opening > 0] = 0
                ys = [520,525,530,535,540,545,550,560,600,640,670,700,720]
                xs = [680,676,671,666,661,655,633,632,632,630,626,622,623]
                for yy in range(round(520*h/1024), min(round(721*h/1024), h)):
                    cutoff = round(np.interp(yy*1024/h, ys, xs)*w/768)
                    alpha[yy, cutoff:] = 0

            Image.fromarray(alpha, "L").filter(ImageFilter.GaussianBlur(.65)).save(OUT / f"{path.stem}.png", optimize=True)
            print(f"mask: {path.stem}", flush=True)


if __name__ == "__main__":
    main()
