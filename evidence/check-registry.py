import json
import urllib.request
import urllib.error

for image in ('edc-ce', 'edc-ce-ui'):
    print('IMAGE', image, '16.8.1', flush=True)
    try:
        url = f'https://ghcr.io/token?service=ghcr.io&scope=repository:sovity/{image}:pull'
        with urllib.request.urlopen(url) as response:
            token = json.load(response)['token']
        request = urllib.request.Request(
            f'https://ghcr.io/v2/sovity/{image}/manifests/16.8.1',
            headers={'Authorization': f'Bearer {token}', 'Accept': 'application/vnd.oci.image.index.v1+json, application/vnd.docker.distribution.manifest.list.v2+json'})
        with urllib.request.urlopen(request) as response:
            result = json.load(response)
            print(json.dumps(result, indent=2))
    except urllib.error.HTTPError as error:
        print('HTTP', error.code, error.read().decode())
