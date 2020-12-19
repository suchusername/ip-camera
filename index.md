# Incredible IP camera bot

Telegram handle: `@incredible_ip_camera_bot`

## Managing the bot

To get information about how to use the bot, send `/help`.

#### Example of the bot's operation

1. Get started by sending `/start`.

2. You will be prompted to enter an email. Enter it if you want to receive email notifications from the tracker, otherwise select `skip`.

3. You will be prompted to enter the IP address of the camera to which you want to connect. Press `stop` to stop work. Here are some examples:
	- `166.145.68.221`
	
 	- `191.186.149.4:8080`

4. Now the **camera control mode** is activated. An image from the camera is displayed along with a message showing the current camera configurations. Commands for controlling the camera will appear at the bottom of the dialog:
	- `up`, `down`, `left`, `right`  are used to change the orientation of the camera in space
	
	- `zoom in`, `zoom out`  are used for zooming
	
	- `show` sends a photo from the camera
	
	- `track` enables **tracking mode**
	
	- `stop` stops working with the camera
	
#### Tracking mode

In tracking mode the neural network (YOLOv3) detects objects on the videostream and notifies the user if something appears in the photo (people, cars, etc). In this case, the camera control is blocked. To see what's happening on the camera click `show`. To return to the **camera control mode** press `stop`.

---

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
