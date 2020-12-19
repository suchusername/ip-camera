## Welcome to GitHub Pages

You can use the [editor on GitHub](https://github.com/suchusername/ip-camera/edit/gh-pages/index.md) to maintain and preview the content for your website in Markdown files.

Whenever you commit to this repository, GitHub Pages will run [Jekyll](https://jekyllrb.com/) to rebuild the pages in your site, from the content in your Markdown files.

## Installation

Here's how to install the project on a local machine and on Google Cloud.

### Locally

All you need is `docker` and `git` installed on your local machine.

Then follow these steps:
1. Pull this repository
```markdown
git pull https://github.com/suchusername/ip-camera
```
2. Build Docker image
```markdown
cd ip-camera/launch
./build_image.sh
```
3. Launch the application
```markdown
./start_bot.sh
```
Now the bot is available to use on Telegram.

### Google Cloud Services

Go to Cloud Shell and perform the following steps.

1. Pull this repository
```markdown
git pull https://github.com/suchusername/ip-camera
```
2. Build an image
```markdown
cd ip-camera
gcloud builds submit --config cloudbuild.yaml --timeout=50m .
```
3. Run the service
```markdown
gcloud run deploy\
  --image gcr.io/ip-camera-299021/ip-camera-run\
  --memory 2G
```
