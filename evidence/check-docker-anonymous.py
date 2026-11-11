import subprocess
import tempfile

with tempfile.TemporaryDirectory(prefix='sovity-docker-anonymous-') as config:
    for image in ('edc-ce', 'edc-ce-ui'):
        result = subprocess.run(['docker', '--config', config, 'pull', f'ghcr.io/sovity/{image}:16.8.1'])
        print(image, 'exit', result.returncode, flush=True)
