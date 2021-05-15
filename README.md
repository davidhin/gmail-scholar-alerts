# Quickstart

**NOTE: This is a very basic script, it just downloads gmail content into a .html table. Not very sophisticated.**

1. Install python requirements `pip install -r requirements.txt`
2. Download Gmail API token from [here](https://console.developers.google.com/start/api?id=gmail)

   1. Select a project (or create a new one).
   2. Click continue.
   3. Click go to credentials.
   4. It will redirect to creating a new credential with Gmail API. Click "User Data", then next.
   5. Fill in the fields.
   6. Skip scopes.
   7. For application type, select "Desktop App".
   8. There should now be a credential under OAuth 2.0 Client IDs. Press the "download" button to the far right of the column. If not, just refresh. If it's still not there, click create credentials -> Oauth client ID and repeat the steps (shouldn't need to do this though).
   9. You should now have something like `client_secret_XXXXXXXX_.json`, which looks something like

      ```json
      {
        "installed": {
          "client_id": "XXX.apps.googleusercontent.com",
          "project_id": "XXX",
          "auth_uri": "https://accounts.google.com/o/oauth2/auth",
          "token_uri": "https://oauth2.googleapis.com/token",
          "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
          "client_secret": "XXX",
          "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob", "http://localhost"]
        }
      }
      ```

   10. Move this file to this directory (gmail-scholar-alerts) and rename it to `credentials.json`
   11. Run `python quickstart.py`. It should generate a table.html in this folder. It caches emails that have been downloaded before.
