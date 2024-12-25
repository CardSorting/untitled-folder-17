import json
import os
import yaml

# Read the Firebase credentials
with open('firebase-credentials.json', 'r') as f:
    firebase_creds = json.load(f)

# Read the current render.yaml
with open('render.yaml', 'r') as f:
    render_config = yaml.safe_load(f)

# Find the web service and update the secrets
for service in render_config['services']:
    if service['type'] == 'web' and service['name'] == 'flask-app':
        if 'secrets' not in service:
            service['secrets'] = []
        
        # Find or create firebase-credentials secret
        found = False
        for secret in service.get('secrets', []):
            if secret.get('key') == 'firebase-credentials':
                secret['value'] = '${FIREBASE_CREDENTIALS_JSON}'
                found = True
                break
        
        if not found:
            service['secrets'].append({
                'key': 'firebase-credentials',
                'value': '${FIREBASE_CREDENTIALS_JSON}'
            })

# Write the updated render.yaml
with open('render.yaml', 'w') as f:
    yaml.dump(render_config, f, default_flow_style=False, sort_keys=False)

print("Successfully updated render.yaml with Firebase credentials")
