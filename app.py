import boto3
import cv2
import os
import logging
import concurrent.futures
from boto3.s3.transfer import S3Transfer, TransferConfig

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client("s3")
transfer = S3Transfer(s3, config=TransferConfig(max_concurrency=10))

BATCH_SIZE = 10
OUTPUT_BUCKET = "video-frames-output"

def lambda_handler(event, context):
    # Get bucket and key from S3 trigger
    bucket = event["Records"][0]["s3"]["bucket"]["name"]
    key = event["Records"][0]["s3"]["object"]["key"]

    # Prepare temp paths
    download_path = "/tmp/video.mp4"
    frames_dir = "/tmp/frames"
    os.makedirs(frames_dir, exist_ok=True)

    # Download video to Lambda /tmp
    s3.download_file(bucket, key, download_path)
    logger.info(f"Downloaded video: s3://{bucket}/{key}")

    cap = cv2.VideoCapture(download_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 1
    frame_interval = int(fps)  # 1 frame per second

    frame_count = 0
    saved_count = 0
    batch_files = []
    video_name = os.path.splitext(os.path.basename(key))[0]

    # Extract frames
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

            # Upload batch of 10 in parallel
            if len(batch_files) >= BATCH_SIZE:
                upload_batch(batch_files, video_name)
                batch_files = []

        frame_count += 1

    # Upload any remaining frames
    if batch_files:
        upload_batch(batch_files, video_name)

    cap.release()
    logger.info(f"Extracted {saved_count} frames")
    return {"status": "done", "frames_extracted": saved_count}

def upload_batch(files, video_name):
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        for f in files:
            filename = os.path.basename(f)
            futures.append(
                executor.submit(
                    transfer.upload_file,
                    f,
                    OUTPUT_BUCKET,
                    f"{video_name}/{filename}",
                )
            )
        concurrent.futures.wait(futures)

    logger.info(f"Uploaded batch of {len(files)} frames in parallel")
