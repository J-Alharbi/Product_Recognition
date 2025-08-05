import boto3
import cv2
import os

s3 = boto3.client('s3')

def lambda_handler(event, context):
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    download_path = '/tmp/video.mp4'
    frames_dir = '/tmp/frames'

    os.makedirs(frames_dir, exist_ok=True)

    # Download video from S3
    s3.download_file(bucket, key, download_path)

    # Open video with OpenCV
    cap = cv2.VideoCapture(download_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_interval = int(fps)  # 1 frame per second

    frame_count = 0
    saved_count = 0
    video_name = os.path.splitext(os.path.basename(key))[0]

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Save 1 frame per second
        if frame_count % frame_interval == 0:
            frame_filename = f"{video_name}_frame_{saved_count:04d}.jpg"
            frame_path = os.path.join(frames_dir, frame_filename)
            cv2.imwrite(frame_path, frame)
            
            # Upload to S3
            s3.upload_file(frame_path, "video-frames-output", f"{video_name}/{frame_filename}")
            saved_count += 1

        frame_count += 1

    cap.release()
    return {"status": "done", "frames_extracted": saved_count}
