import boto3
import botocore

def get_stack_status(stackname):
    client = boto3.client('cloudformation')
    r = client.describe_stacks(StackName=stackname)
    
    for stack in r['Stacks']:
        if str(stack['StackName']) == stackname:

            return stack['StackStatus']

def get_stack_output_value_from_key(stackname, output_key):
    client = boto3.client('cloudformation')
    r = client.describe_stacks(StackName=stackname)
    
    for stack in r['Stacks']:
        if str(stack['StackName']) == stackname:
            
            for output in stack['Outputs']:
                if output['OutputKey'] == output_key:
                    
                    return output['OutputValue']

def replace_in_file(path, search, replace):
    if search == '' or replace == '':
        raise ValueError('serch and replace cannot be empty')
    s = open(path).read()
    s = s.replace(str(search), str(replace))
    f = open(path, 'w')
    f.write(s)
    f.close()