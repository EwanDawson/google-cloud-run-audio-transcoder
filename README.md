# Audio Transcoding Service for Google Cloud Run

This service is designed to transcode audio files stored in Google Cloud Storage (GCS) to the `.m4a` format using the `ffmpeg` tool. It is deployed on Google Cloud Run and is triggered by Pub/Sub messages that contain information about the GCS event.

## Dependencies

The service is written in Python and uses the following libraries:

- `google-cloud-storage` for interacting with Google Cloud Storage
- `flask` for handling HTTP requests
- `os` and `subprocess` for file operations and running shell commands
- `json` and `sys` for logging

## Service Endpoint

The service exposes a single HTTP POST endpoint at `/transcode-audio`. This endpoint is designed to receive Pub/Sub messages in the following format:

```json
{
  "message": {
    "attributes": {
      "bucketId": "bucket-name",
      "objectId": "file-name"
    }
  }
}
```

## Transcoding Process

When a Pub/Sub message is received, the service performs the following steps:

1. Validates the Pub/Sub message and extracts the bucket name and file name.
2. Transcodes the audio file to `.m4a` format using `ffmpeg`.
3. Uploads the transcoded file back to GCS, either replacing the original file or creating a new one, depending on whether the original file had an extension.
4. Adds metadata to the GCS blob to indicate that it has been transcoded.

## Error Handling

The service logs all actions and errors to stdout. If an error occurs during the transcoding process, it is logged and returned in the HTTP response.

## Deployment

The service is designed to be deployed on Google Cloud Run. It listens on the port specified by the `PORT` environment variable, or `8080` if the variable is not set. The service does not require any special permissions, but the Google Cloud Run service account must have the necessary permissions to read and write to the GCS bucket.

## Reuse and Iteration

To reuse or iterate on this code, you can modify the `transcode_audio` function to handle different types of GCS events, transcode to different audio formats, or perform other types of processing on the files. You can also add more endpoints to the Flask app to handle different types of requests.

### Deploy to Cloud Run

1. Select 'Deploy to Cloud Run' using the Cloud Code status bar.

2. If prompted, login to your Google Cloud account and set your project.

3. Use the Deploy to Cloud Run dialog to configure your deploy settings. For more information on the configuration options available, see [Deploying a Cloud Run app](https://cloud.google.com/code/docs/vscode/deploying-a-cloud-run-app?utm_source=ext&utm_medium=partner&utm_campaign=CDR_kri_gcp_cloudcodereadmes_012521&utm_content=-).  

4. Click 'Deploy'. Cloud Code now builds your image, pushes it to the container registry, and deploys your service to Cloud Run.

5. View your live service by clicking on the URL displayed at the top of the 'Deploy to Cloud Run' dialog.  
![image](../../img/cloud-run-deployed-url.png)

---
