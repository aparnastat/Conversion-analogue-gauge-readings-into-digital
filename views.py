import math
import cv2
import numpy as np
from django.shortcuts import render, redirect
from django.urls import reverse
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse
from ultralytics import YOLO 

detection_model = YOLO('runs100/detect/train/weights/best.pt')
segmentation_model = YOLO('runs/segment/train2/weights/best.pt')

def calculate_angle_from_three_points(initial_tip, gauge_center, current_tip):
    v1 = np.array(initial_tip) - np.array(gauge_center)
    v2 = np.array(current_tip) - np.array(gauge_center)
    angle_rad = np.arctan2(v2[1], v2[0]) - np.arctan2(v1[1], v1[0])
    angle_deg = np.degrees(angle_rad)
    angle_deg = angle_deg % 353  
    return angle_deg

def detect_needle_tip(frame):
    results = segmentation_model(frame)
    boxes = results[0].boxes.xyxy
    confidences = results[0].boxes.conf
    classes = results[0].boxes.cls
    
    needle_tip = None
    needle_class_id = 2 

    for i in range(len(boxes)):
        if classes[i] == needle_class_id and confidences[i] > 0.41:
            x1, y1, x2, y2 = boxes[i]
            needle_tip = ((x1 + x2) / 2, (y1 + y2) / 2)
            break 
    return needle_tip

def landing_page(request):
    return render(request, 'upload.html')




def upload_video(request):
    if request.method == 'POST':
        video_file = request.FILES['video']
        fs = FileSystemStorage()
        filename = fs.save(video_file.name, video_file)
        uploaded_file_path = fs.url(filename)

        cap = cv2.VideoCapture(f'media/{filename}')

        ret, first_frame = cap.read()
        if not ret:
            return HttpResponse("Error reading video", status=400)
        
        gauge_results = detection_model(first_frame)
        gauge_boxes = gauge_results[0].boxes.xyxy
        gauge_confidences = gauge_results[0].boxes.conf
        gauge_classes = gauge_results[0].boxes.cls
        gauge_box = None
        gauge_class_id = 0  
      
        for i in range(len(gauge_boxes)):
            if gauge_classes[i] == gauge_class_id and gauge_confidences[i] > 0.4:
                x1, y1, x2, y2 = gauge_boxes[i]
                gauge_box = (int(x1), int(y1), int(x2), int(y2))
                break
                
        if gauge_box is None:
            return HttpResponse("Gauge not detected in the first frame", status=400)

        x1, y1, x2, y2 = gauge_box

        gauge_center = (181, 158)  
        initial_needle_tip = (86, 245)
        angles = []

        output_filename = 'media/processed_video.mp4'
        fourcc = cv2.VideoWriter_fourcc(*'avc1') 

        fps = cap.get(cv2.CAP_PROP_FPS)
        width = x2 - x1
        height = y2 - y1
        out = cv2.VideoWriter(output_filename, fourcc, fps, (width, height))


        while True:
            ret, frame = cap.read()
            if not ret:
                break

            cropped_frame = frame[y1:y2, x1:x2]

            
            current_needle_tip = detect_needle_tip(cropped_frame)

           
            if current_needle_tip is not None:
                angle = calculate_angle_from_three_points(initial_needle_tip, gauge_center, current_needle_tip)
                angles.append(angle)
                reading = angle / 2.6
                cv2.putText(cropped_frame, f"Gauge reading: {reading:.0f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.99, (0, 0, 255), 2)

            
            out.write(cropped_frame)

        
        cap.release()
        out.release()


        
       
        with open('media/readings_calculated.txt', 'w') as f:
            for angle in angles:
                f.write(f"{angle/2.6:.0f}\n")

        return render(request, 'upload.html', {
            'uploaded_file_path': uploaded_file_path,
            'angles_file_path': 'http://127.0.0.1:8000/media/readings_calculated.txt',
            'processed_video_path': 'http://127.0.0.1:8000/media/processed_video.mp4'
        })
    

    return render(request, 'upload.html')

def output_video(request):
    processed_video_path = 'media/processed_video.mp4'  
    return render(request, 'output_video.html', {'processed_video_path': processed_video_path})