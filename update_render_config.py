import json
import os
import yaml

# Read the Firebase credentials
with open('firebase-credentials.json', 'r') as f:
    firebase_creds = json.load(f)

# Read the current render.yaml
with open('render.yaml', 'r') as f:
    render_config = yaml.safe_load(f)

# Find the web service and update the file contents
for service in render_config['services']:
    if service['type'] == 'web' and service['name'] == 'flask-app':
        for file_config in service.get('files', []):
            if file_config['name'] == 'firebase-credentials':
                file_config['contents'] = json.dumps(firebase_creds, indent=2)

# Write the updated render.yaml
with open('render.yaml', 'w') as f:
    yaml.dump(render_config, f, default_flow_style=False, sort_keys=False)

print("Successfully updated render.yaml with Firebase credentials")
