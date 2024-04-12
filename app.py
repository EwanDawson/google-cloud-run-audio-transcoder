import sys
import os
import subprocess
from google.cloud import storage
from flask import Flask, request
import json
import magic

# pylint: disable=C0103
app = Flask(__name__)

def log(message):
    print(json.dumps(message))
    sys.stdout.flush()

VALID_AUDIO_TARGET_FORMAT = ['audio/mp4','audio/x-m4a']

@app.route('/transcode-audio', methods=['POST'])
def transcode_audio():
    """Receive and parse Pub/Sub messages."""
    envelope = request.get_json()
    log(envelope)
    if not envelope:
        msg = "no Pub/Sub message received"
        log(f"error: {msg}")
        return f"Bad Request: {msg}", 400
    
    if not isinstance(envelope, dict) or "message" not in envelope:
        msg = "invalid Pub/Sub message format"
        log(f"error: {msg}")
        return f"Bad Request: {msg}", 400
    
    message = envelope["message"]
    if not isinstance(message, dict) or "attributes" not in message:
        msg = "invalid Pub/Sub message format"
        log(f"error: {msg}")
        return f"Bad Request: {msg}", 400
    
    attributes = message['attributes']
    if not isinstance(attributes, dict) or "bucketId" not in attributes or "objectId" not in attributes:
        msg = "invalid Cloud Storage event format"
        log(f"error: {msg}")
        return f"Bad Request: {msg}", 400
    
    bucket_name = attributes['bucketId']
    source_file_name = attributes['objectId']
    
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.get_blob(source_file_name)

    if blob is None:
        msg = f"File {source_file_name} not found in bucket {bucket_name}"
        log(msg)
        return msg, 404

    # Skip if the file is alredy in the target format or has already been transcoded
    content_type = blob.content_type
    log(f"Content-Type: {content_type}")
    print("Metadata:")
    log(blob.metadata)
    if (blob.metadata and blob.metadata.get('transcoded') == 'true') or content_type in VALID_AUDIO_TARGET_FORMAT:
        msg = f'Skipping transcoding for file: {source_file_name}'
        log(msg)
        return msg, 200
    
    # If the file is not an audio/video file or an octet stream, return an error
    if not content_type.startswith('audio/') and not content_type.startswith('video/') and not content_type == 'application/octet-stream':
        msg = f'File {source_file_name} is not an audio/video file'
        log(msg)
        return msg, 400
    
    # Create the src and dest folders if needed
    os.makedirs('/tmp/src', exist_ok=True)
    os.makedirs('/tmp/dest', exist_ok=True)

    # If the source file has an extension, we strip it and replace it with .m4a. Otherwise, we make no change to the file name
    if os.path.splitext(source_file_name)[1]:
        destination_file_name = os.path.splitext(source_file_name)[0] + '.m4a'
    else:
        destination_file_name = source_file_name
    
    # Temporary file names
    temp_source_file = '/tmp/src/' + source_file_name
    temp_destination_file = '/tmp/dest/' + destination_file_name

    # Download the file from GCS
    blob.download_to_filename(temp_source_file)

    # If the content type is application/octet-stream, we try to determine the content type using the magic library,
    # and return an error if it is not an audio/video file
    if content_type == 'application/octet-stream':
        mime = magic.Magic(mime=True)
        content_type = mime.from_file(temp_source_file)
        log(f"Determined content type of octet stream: {content_type}")
        if not content_type.startswith('audio/') and not content_type.startswith('video/'):
            msg = f'File {source_file_name} is not an audio/video file'
            log(msg)
            return msg, 400
        if content_type in VALID_AUDIO_TARGET_FORMAT:
            msg = f'Skipping transcoding for file: {source_file_name}'
            log(msg)
            return msg, 200

    # Transcode the audio/video file to m4a/aac, ignoring any video stream, and forcing ffmpeg to overwrite if a file exists
    try:
        subprocess.check_call(['ffmpeg', '-y', '-i', temp_source_file, '-vn', '-c:a', 'aac', '-f', 'ipod', temp_destination_file])
    except subprocess.CalledProcessError as e:
        msg = f'Error occurred during transcoding: {e}'
        log(msg)
        return msg, 500

    # Upload the transcoded file back to GCS. Use the same blob if we hvae not changed the file name
    # Otherwise, upload the transcoded file to a new blob
    if destination_file_name != source_file_name:
        blob = bucket.blob(destination_file_name)
    blob.upload_from_filename(temp_destination_file, content_type='audio/mp4')
    
    ## Add metadata to blob to indicate it has been transcoded
    blob.metadata = {'transcoded': 'true'}
    blob.patch()

    # Delete the temporary files
    os.remove(temp_source_file)
    os.remove(temp_destination_file)

    msg = f"Succesfully transcoded file: {source_file_name}"
    log(msg)
    return msg, 201

if __name__ == '__main__':
    server_port = os.environ.get('PORT', '8080')
    app.run(debug=False, port=server_port, host='0.0.0.0')
