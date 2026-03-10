# Mobile Notifications via FCM (Path 1 — Direct from bash)

Send agent completion notifications directly to your Android device using Firebase Cloud Messaging, with no backend server required. Everything runs locally on your Mac inside `notify.sh`.

---

## How it works

```
notify.sh
  │
  ├─ 1. Exchange service account JSON → short-lived OAuth2 access token
  │       POST https://oauth2.googleapis.com/token
  │
  └─ 2. Call FCM HTTP v1 API with that token
          POST https://fcm.googleapis.com/v1/projects/{PROJECT_ID}/messages:send
                │
                └─ FCM → your Android device
```

The token is valid for 1 hour. Since hooks fire infrequently, we fetch a fresh token on each call — no caching needed.

---

## What you need to do manually (before implementation)

### 1. Create a Firebase Service Account

1. Go to [Firebase Console](https://console.firebase.google.com) → your project
2. **Project Settings** (gear icon) → **Service accounts** tab
3. Click **Generate new private key** → confirm → download the JSON file
4. Store it on your Mac at:
   ```
   ~/.agent-box/fcm-service-account.json
   ```
   **Important:** Never commit this file. It has full access to your Firebase project.

5. Verify the JSON has these fields (it will):
   ```json
   {
     "type": "service_account",
     "project_id": "your-project-id",
     "private_key": "-----BEGIN RSA PRIVATE KEY-----...",
     "client_email": "firebase-adminsdk-xxx@your-project.iam.gserviceaccount.com",
     ...
   }
   ```

### 2. Verify FCM API is enabled

1. Go to [Google Cloud Console](https://console.cloud.google.com) → your Firebase project
2. **APIs & Services** → **Enabled APIs**
3. Check that **Firebase Cloud Messaging API** is listed. If not, enable it.

### 3. Get your Android device's FCM registration token

Your Android app already uses FCM. You need to extract your device's current registration token — it's the unique identifier FCM uses to route the notification to your specific device.

In your Android app code, add a temporary log (or a visible text field) to print:
```kotlin
FirebaseMessaging.getInstance().token.addOnCompleteListener { task ->
    if (task.isSuccessful) {
        Log.d("FCM", "Token: ${task.result}")
    }
}
```
Copy that token and store it on your Mac:
```
~/.agent-box/fcm-device-token
```

> **Note:** FCM tokens can rotate (app reinstall, token refresh). You'll need to update this file if notifications stop arriving. Consider building a mechanism in your app to write the current token to a backend or expose it in settings.

### 4. Set file permissions

```bash
chmod 600 ~/.agent-box/fcm-service-account.json
chmod 600 ~/.agent-box/fcm-device-token
```

---

## What the implementation will do

`notify.sh` additions:
1. Check for a toggle flag file (`~/.agent-box/mobile-notify-enabled`) — skip if absent
2. Read `project_id`, `client_email`, `private_key` from the service account JSON using Python (built-in, no extra deps needed to sign the JWT)
3. Exchange service account credentials for an OAuth2 Bearer token
4. POST to the FCM v1 API with the notification payload

Toggle commands (will be added as shell aliases):
```bash
mobile-notify-on    # touch ~/.agent-box/mobile-notify-enabled
mobile-notify-off   # rm ~/.agent-box/mobile-notify-enabled
```

Python is used for the JWT signing step (signing with RS256 requires it). Python 3 is available on macOS by default.

---

## Security notes

- The service account JSON lives only on your Mac, never in the repo
- The FCM device token is also local only
- The toggle flag means mobile notifications are **off by default** — you opt in per session
- If you want to limit the service account's blast radius, create a dedicated service account with only the `cloudmessaging.messages.create` permission rather than using the default Firebase Admin SDK account
