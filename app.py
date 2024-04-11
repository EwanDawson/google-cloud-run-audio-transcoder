import os
import subprocess
from google.cloud import storage
from flask import Flask

# pylint: disable=C0103
app = Flask(__name__)

@app.route('/pubsub/push', methods=['POST'])
def transcode_audio(request):
    # Extract the bucket name and source file name from the Pub/Sub message
    # The message is a JSON object
    message = request.get_json()
    bucket_name = message['bucket']
    source_file_name = message['name']
    
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(source_file_name)
    
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
        result = f'Error occurred during transcoding: {e}'
        print(result)
        return result, 500

    # Upload the transcoded file back to GCS
    blob.upload_from_filename(temp_destination_file)

    # Delete the temporary files
    os.remove(temp_source_file)
    os.remove(temp_destination_file)

    return f'Transcoded file uploaded: {source_file_name}', 201

if __name__ == '__main__':
    server_port = os.environ.get('PORT', '8080')
    app.run(debug=False, port=server_port, host='0.0.0.0')
