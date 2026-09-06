import os, sys, boto3, zipfile, io, urllib.request, time

def deploy_to_amplify():
    session = boto3.Session(profile_name=os.getenv('AWS_PROFILE', 'zaeem-khan'), region_name='us-east-1')
    amplify = session.client('amplify')

    app_name = 'rebuttal-judge-console'
    existing_apps = amplify.list_apps().get('apps', [])
    target_app = next((a for a in existing_apps if a['name'] == app_name), None)

    if not target_app:
        print('Creating Amplify app:', app_name)
        app = amplify.create_app(
            name=app_name,
            description='Rebuttal Autonomous Chargeback Defense - Judge Console',
            platform='WEB',
            customRules=[
                {
                    'source': '</^[^.]+$|\\.(?!(css|gif|ico|jpg|js|png|txt|svg|woff|woff2|ttf|map|json)$)([^.]+$)/>',
                    'target': '/index.html',
                    'status': '200'
                }
            ],
            environmentVariables={
                'NEXT_PUBLIC_SUPABASE_URL': 'https://ygcmdhmoqvafxrqyqnqv.supabase.co',
                'NEXT_PUBLIC_INJECT_URL': 'https://aovwsnanmseqfc753yan52g3be0nqnem.lambda-url.us-east-1.on.aws/',
                'NEXT_PUBLIC_TWILIO_WEBHOOK_URL': 'https://n2g4gh2yjripct4y4sre3lnx2e0ivggv.lambda-url.us-east-1.on.aws/',
                'NEXT_PUBLIC_CONSOLE_KEY': 'rebuttal-judge-console-key-2026',
            }
        )
        app_id = app['app']['appId']
    else:
        app_id = target_app['appId']
        print('Found existing Amplify app:', app_id)

    branches = amplify.list_branches(appId=app_id).get('branches', [])
    if not any(b['branchName'] == 'main' for b in branches):
        print('Creating branch main...')
        amplify.create_branch(appId=app_id, branchName='main')

    print('Creating deployment...')
    dep = amplify.create_deployment(appId=app_id, branchName='main')
    job_id = dep['jobId']
    upload_url = dep['zipUploadUrl']
    print(f'Deployment job ID: {job_id}')

    print('Packaging console/out...')
    out_dir = 'console/out'
    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(out_dir):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, out_dir).replace('\\\\', '/')
                zf.write(full_path, rel_path)

    zip_bytes = zip_buf.getvalue()
    print(f'Archive size: {len(zip_bytes)} bytes')

    print('Uploading archive to S3...')
    req = urllib.request.Request(
        upload_url,
        data=zip_bytes,
        method='PUT',
        headers={'Content-Type': 'application/zip'}
    )
    with urllib.request.urlopen(req) as resp:
        print(f'Upload response: {resp.status}')

    print('Starting deployment job...')
    amplify.start_deployment(appId=app_id, branchName='main', jobId=job_id)

    print('Waiting for Amplify deployment to complete...')
    status = 'PENDING'
    for attempt in range(30):
        time.sleep(3)
        job = amplify.get_job(appId=app_id, branchName='main', jobId=job_id)
        status = job['job']['summary']['status']
        print(f'[{attempt*3}s] Job status: {status}')
        if status in ['SUCCEED', 'FAILED', 'CANCELLED']:
            break

    if status != 'SUCCEED':
        print(f'Deployment failed with status: {status}')
        sys.exit(1)

    live_url = f'https://main.{app_id}.amplifyapp.com'
    print('DEPLOYMENT SUCCEEDED!')
    print(f'Live AWS Amplify Console URL: {live_url}')
    return live_url

if __name__ == '__main__':
    deploy_to_amplify()
