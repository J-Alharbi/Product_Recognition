import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    logger.info(f"Received event: {event}")

    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    logger.info(f"Processing file {key} from bucket {bucket}")

    download_path = '/tmp/video.mp4'
    frames_dir = '/tmp/frames'
    os.makedirs(frames_dir, exist_ok=True)

    s3.download_file(bucket, key, download_path)

    cap = cv2.VideoCapture(download_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    logger.info(f"Video FPS: {fps}")
    if not fps or fps <= 0:
        fps = 1
    frame_interval = int(fps)

    frame_count = 0
    saved_count = 0
    video_name = os.path.splitext(os.path.basename(key))[0]

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        if frame_count % frame_interval == 0:
            frame_filename = f"{video_name}_frame_{saved_count:04d}.jpg"
            frame_path = os.path.join(frames_dir, frame_filename)
            cv2.imwrite(frame_path, frame)
            logger.info(f"Saved frame {frame_filename}")

            s3.upload_file(frame_path, "video-frames-output", f"{video_name}/{frame_filename}")
            saved_count += 1

        frame_count += 1

    cap.release()
    logger.info(f"Extracted {saved_count} frames")
    return {"status": "done", "frames_extracted": saved_count}
