import boto3

def destroy_stacks(appName):
    client = boto3.client('cloudformation')
    r = client.describe_stacks()

    for stack in r['Stacks']:       
        if str(stack['StackName']).startswith(appName+'-'):
            client.delete_stack(
                StackName=stack['StackName']
            )

def empty_buckets(appName):
    client = boto3.client('s3')

    r = client.list_buckets()

    for bucket in r['Buckets']:
        if str(bucket['Name']).startswith(appName+'-'):
            s3 = boto3.resource('s3')
            bucket_object = s3.Bucket(bucket['Name'])
            bucket_object.objects.all().delete()

def go_remove(appName):

    print('Empty S3 buckets named as '+appName+'-*')
    empty_buckets(appName)

    print('Destroy stacks named as '+appName+'-*')
    destroy_stacks(appName)

    print('Done')