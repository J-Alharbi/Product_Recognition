import boto3, cv2, os, logging, concurrent.futures

logger = logging.getLogger()
logger.setLevel(logging.INFO)
s3 = boto3.client('s3')

BATCH_SIZE = 50

def lambda_handler(event, context):
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    download_path = '/tmp/video.mp4'
    frames_dir = '/tmp/frames'
    os.makedirs(frames_dir, exist_ok=True)

    s3.download_file(bucket, key, download_path)
    cap = cv2.VideoCapture(download_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 1
    frame_interval = int(fps)

    frame_count = 0
    saved_count = 0
    batch_files = []
    video_name = os.path.splitext(os.path.basename(key))[0]

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        if frame_count % frame_interval == 0:
            frame_filename = f"{video_name}_frame_{saved_count:04d}.jpg"
            frame_path = os.path.join(frames_dir, frame_filename)
            cv2.imwrite(frame_path, frame, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
            batch_files.append(frame_path)
            saved_count += 1

            # Upload batch
            if len(batch_files) >= BATCH_SIZE:
                upload_batch(batch_files, video_name)
                batch_files = []

        frame_count += 1

    # Upload remaining frames
    if batch_files:
        upload_batch(batch_files, video_name)

    cap.release()
    return {"status": "done", "frames_extracted": saved_count}

def upload_batch(files, video_name):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        for f in files:
            filename = os.path.basename(f)
            executor.submit(
                s3.upload_file, f, "video-frames-output", f"{video_name}/{filename}"
            )
    logger.info(f"Uploaded batch of {len(files)} frames")
