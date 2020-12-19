gcloud config set project ip-camera-299021
cd ../..
gcloud builds submit --config cloudbuild.yaml --timeout=50m .
cd -