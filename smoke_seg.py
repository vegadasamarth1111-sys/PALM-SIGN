import cv2, time
from src.segment import SkinSegmenter
from src.features import extract_features
cap=cv2.VideoCapture(0, cv2.CAP_DSHOW)
cap.set(cv2.CAP_PROP_FRAME_WIDTH,640); cap.set(cv2.CAP_PROP_FRAME_HEIGHT,480)
for _ in range(8): cap.read()
ok, frame=cap.read(); cap.release()
print('read',ok, None if frame is None else frame.shape)
if ok:
    frame=cv2.flip(frame,1)
    s=SkinSegmenter()
    t=time.time(); seg=s.segment(frame); print('seg seconds', round(time.time()-t,3))
    print('faces', seg.faces, 'hand', None if seg.hand is None else cv2.contourArea(seg.hand), 'contours',len(seg.contours))
    if seg.hand is not None:
        f=extract_features(seg.hand, frame.shape, seg.hull)
        print('valid', f.info.get('valid'), 'fingers', f.info.get('finger_estimate'), 'solidity', round(f.info.get('solidity',0),3))
    cv2.imwrite('seg_frame.jpg', frame)
    cv2.imwrite('seg_mask.jpg', seg.mask)
    cv2.imwrite('seg_light.jpg', seg.light)
    if seg.hand is not None:
        over=frame.copy(); x1,y1,x2,y2=seg.roi_box
        cv2.drawContours(over,[seg.hand+np.array([[x1,y1]])],-1,(0,0,255),2)
        cv2.imwrite('seg_overlay.jpg',over)
