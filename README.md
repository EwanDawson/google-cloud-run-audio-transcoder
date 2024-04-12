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

### Deploy to Cloud Run

1. Select 'Deploy to Cloud Run' using the Cloud Code status bar.

2. If prompted, login to your Google Cloud account and set your project.

3. Use the Deploy to Cloud Run dialog to configure your deploy settings. For more information on the configuration options available, see [Deploying a Cloud Run app](https://cloud.google.com/code/docs/vscode/deploying-a-cloud-run-app?utm_source=ext&utm_medium=partner&utm_campaign=CDR_kri_gcp_cloudcodereadmes_012521&utm_content=-).  

4. Click 'Deploy'. Cloud Code now builds your image, pushes it to the container registry, and deploys your service to Cloud Run.

5. View your live service by clicking on the URL displayed at the top of the 'Deploy to Cloud Run' dialog.  
![image](../../img/cloud-run-deployed-url.png)

### Create a Pub/Sub Topic

If you haven't already created a Pub/Sub topic, do so by running the following command:

```bash
gcloud pubsub topics create [TOPIC_NAME]
```

Replace `[TOPIC_NAME]` with your desired topic name.

### Grant Pub/Sub Publisher Role to Cloud Storage

Your Cloud Storage service account needs permission to publish to your Pub/Sub topic. Grant the necessary role with the following command:

```bash
gcloud pubsub topics add-iam-policy-binding [TOPIC_NAME] \
--member=serviceAccount:service-[PROJECT_NUMBER]@gs-project-accounts.iam.gserviceaccount.com \
--role=roles/pubsub.publisher
```

Replace `[TOPIC_NAME]` with your topic name and `[PROJECT_NUMBER]` with your Google Cloud project number.

### Create a Notification Configuration

Now, set up a notification for your bucket. Use the `gsutil` command:

```bash
gsutil notification create -t [TOPIC_NAME] -f json -e OBJECT_FINALIZE gs://[BUCKET_NAME]
```

Replace `[TOPIC_NAME]` with your Pub/Sub topic name and `[BUCKET_NAME]` with the name of your Cloud Storage bucket.

This command creates a notification configuration that sends a JSON-formatted event to the specified Pub/Sub topic whenever a new object is created in the specified bucket.

Create a separate notification for each bucket you want to monitor.

### Create a Subscription that Triggers the Transcoder

Use the Cloud Console to create a subscription with a configuration similar to this:

```
ackDeadlineSeconds: 300
deadLetterPolicy:
  deadLetterTopic: [DEAD_LETTER_TOPIC_NAME]
  maxDeliveryAttempts: 5
expirationPolicy: {}
messageRetentionDuration: 604800s
name: [SUBSCRIPTION_NAME]
pushConfig:
  oidcToken:
    serviceAccountEmail: [SERVICE_ACCOUNT]
  pushEndpoint: []
retryPolicy:
  maximumBackoff: 600s
  minimumBackoff: 10s
state: ACTIVE
topic: [TOPIC_NAME]
```

Choose `[DEAD_LETTER_TOPIC_NAME]`, `[SUBSCRIPTION_NAME]` as appropriate. Choose (or create) a `[SERVICE_ACCOUNT]` that has the `Cloud Run Invoker` role. `[TOPIC_NAME]` is the name of previously created topic that receives the object creation notifications.

## Reuse and Iteration

To reuse or iterate on this code, you can modify the `transcode_audio` function to handle different types of GCS events, transcode to different audio formats, or perform other types of processing on the files. You can also add more endpoints to the Flask app to handle different types of requests.

---
