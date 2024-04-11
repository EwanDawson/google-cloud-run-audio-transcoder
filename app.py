import sys
import os
import subprocess
from google.cloud import storage
from flask import Flask, request
import json

# pylint: disable=C0103
app = Flask(__name__)

def log(message):
    print(json.dumps(message))
    sys.stdout.flush()

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
    blob = bucket.blob(source_file_name)

    ## Skip if the file has already been transcoded
    if blob.metadata and blob.metadata.get('transcoded') == 'true':
        msg = f'Skipping transcoding for file: {source_file_name}'
        log(msg)
        return msg, 200
    
    # Create the src and dest folders if needed
    os.makedirs('/tmp/src', exist_ok=True)
    os.makedirs('/tmp/dest', exist_ok=True)

    # Temporary file names
    temp_source_file = '/tmp/src/' + source_file_name
    temp_destination_file = '/tmp/dest/' + source_file_name

    # Download the file from GCS
    blob.download_to_filename(temp_source_file)

    # Transcode the audio file to m4a/aac, forcing ffmpeg to overwrite if a file exists
    try:
        subprocess.check_call(['ffmpeg', '-y', '-i', temp_source_file, '-acodec', 'aac', temp_destination_file])
    except subprocess.CalledProcessError as e:
        msg = f'Error occurred during transcoding: {e}'
        log(msg)
        return msg, 500

    # Upload the transcoded file back to GCS
    blob.upload_from_filename(temp_destination_file)

    ## Add metadata to blob to indicate it has been transcoded
    blob.metadata = {'transcoded': 'true'}

    # Delete the temporary files
    os.remove(temp_source_file)
    os.remove(temp_destination_file)

    msg = f"Succesfully transcoded file: {source_file_name}"
    log(msg)
    return msg, 201

if __name__ == '__main__':
    server_port = os.environ.get('PORT', '8080')
    app.run(debug=False, port=server_port, host='0.0.0.0')
