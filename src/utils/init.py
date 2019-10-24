import os
import mimetypes
import boto3
import botocore
import time
import json
from zipfile import ZipFile
from ..utils import tools

lambda_s3_name = '-lambda-s3'
web_s3_name = '-web-s3'
website_url = ''
api_url = ''
db_cluster_arn = ''
db_cluster_id = ''
secret_arn = ''

def create_web_s3(appName):
    global web_s3_name
    web_s3_name = str(appName) + web_s3_name
    stackname = web_s3_name + '-stack'
    cf_template = open('iac/s3-web-stack.yaml').read()

    client = boto3.client('cloudformation')
    client.create_stack(
        StackName=stackname,
        TemplateBody=cf_template,
        Capabilities=['CAPABILITY_NAMED_IAM'],
        Parameters=[
            {
                'ParameterKey': 'webBucketName',
                'ParameterValue': web_s3_name
            }
        ]
    )

    print('Waiting for S3 web Bucket URL...')
    while tools.get_stack_status(stackname) != 'CREATE_COMPLETE':
        time.sleep(2)
        print('.', end='')
    print("\n")

    global website_url
    website_url = tools.get_stack_output_value_from_key(stackname, 'WebsiteURL')

def create_lambda_s3(appName):

    global lambda_s3_name 
    lambda_s3_name =  str(appName) + lambda_s3_name
    stackname = lambda_s3_name + '-stack'
    cf_template = open('iac/s3-lambda-stack.yaml').read()

    client = boto3.client('cloudformation')
    client.create_stack(
        StackName=stackname,
        TemplateBody=cf_template,
        Capabilities=['CAPABILITY_NAMED_IAM'],
        Parameters=[
            {
                'ParameterKey': 'lambdaBucketName',
                'ParameterValue': lambda_s3_name
            }
        ]
    )

    print('Waiting for S3 lambda Bucket...')
    while tools.get_stack_status(stackname) != 'CREATE_COMPLETE':
        time.sleep(2)
        print('.', end='')
    print("\n")

def zip_lambda():
    try:
        os.remove('function.zip')
    except:
        pass

    zipObj = ZipFile('function.zip', 'w')

    # Replace vars
    for x in os.listdir('src/lambda'):
        if os.path.isfile('src/lambda/'+x): 
            local_path = 'src/lambda/'+x
            tools.replace_in_file(local_path, '__WEBSITE_URL__', website_url)
            tools.replace_in_file(local_path, '__DB_CLUSTER_ARN__', db_cluster_arn)
            tools.replace_in_file(local_path, '__SECRET_ARN__', secret_arn)
            zipObj.write('src/lambda/'+x, x)
    
    zipObj.close()

    # Revert vars
    for x in os.listdir('src/lambda'):
        if os.path.isfile('src/lambda/'+x): 
            local_path = 'src/lambda/'+x
            tools.replace_in_file(local_path, website_url, '__WEBSITE_URL__')
            tools.replace_in_file(local_path, db_cluster_arn, '__DB_CLUSTER_ARN__')
            tools.replace_in_file(local_path, secret_arn, '__SECRET_ARN__')


def upload_lambda():
    s3 = boto3.client('s3')
    s3.upload_file('function.zip', lambda_s3_name, 'function.zip')
    os.remove('function.zip')

def upload_static_files():
    s3 = boto3.client('s3')

    for root, dirs, files in os.walk('web'):

        for filename in files:
            local_path = os.path.join(root, filename)

            if '.html' in local_path:
                tools.replace_in_file(local_path, '__API_URL__', api_url)
            
            if mimetypes.MimeTypes().guess_type(local_path)[0] != None:
                content_type = mimetypes.MimeTypes().guess_type(local_path)[0]
            else:
                content_type = 'binary/octet-stream'

            s3.upload_file(
                local_path, 
                web_s3_name,
                local_path.replace('web/', ''), 
                ExtraArgs={
                    'ACL':'public-read',
                    'ContentType': content_type
                }
            )

            if '.html' in local_path:
                tools.replace_in_file(local_path, api_url, '__API_URL__')
            

def create_stack(appName):
    client = boto3.client('cloudformation')

    stackname = appName + '-main-stack'
    cf_template = open('iac/main-stack.yaml').read()

    client.create_stack(
        StackName=stackname,
        TemplateBody=cf_template,
        Capabilities=['CAPABILITY_NAMED_IAM'],
        Parameters=[
            {
                'ParameterKey': 'appName',
                'ParameterValue': appName
            }
        ]
    )

    print('Waiting for main stack...')
    while tools.get_stack_status(stackname) != 'CREATE_COMPLETE':
        time.sleep(2)
        print('.', end='')
    print("\n")
    
    global api_url
    api_url = tools.get_stack_output_value_from_key(stackname, 'apiGatewayInvokeURL')

def create_rds_cluster(appName):
    client = boto3.client('cloudformation')

    stackname = appName + '-rds-stack'
    cf_template = open('iac/rds-stack.yaml').read()

    client.create_stack(
        StackName=stackname,
        TemplateBody=cf_template,
        Capabilities=['CAPABILITY_NAMED_IAM'],
        Parameters=[
            {
                'ParameterKey': 'appName',
                'ParameterValue': appName
            }
        ]
    )

    print('Waiting for RDS Cluster stack...')
    while tools.get_stack_status(stackname) != 'CREATE_COMPLETE':
        time.sleep(2)
        print('.', end='')
    print("\n")

    global db_cluster_id, db_cluster_arn, secret_arn
    db_cluster_id = tools.get_stack_output_value_from_key(stackname, 'rdsClusterId')
    r = boto3.client('rds').describe_db_clusters(
        DBClusterIdentifier=db_cluster_id
    )
    db_cluster_arn = r['DBClusters'][0]['DBClusterArn']
    secret_arn = tools.get_stack_output_value_from_key(stackname, 'rdsSecretArn')

def init_database(appName):
    
    # Because Cloudformation does not support "EnableHttpEndpoint" propertie yet
    global db_cluster_id, db_cluster_arn, secret_arn
    client = boto3.client('rds')
    client.modify_db_cluster(
        DBClusterIdentifier=db_cluster_id,
        EnableHttpEndpoint=True,
        ApplyImmediately=True
    )

    # Create db and table
    client = boto3.client('rds-data')
    sql = "CREATE DATABASE IF NOT EXISTS `EightMagicBall`"
    client.execute_statement(
        resourceArn = db_cluster_arn, 
        secretArn = secret_arn, 
        sql = sql
    )
    
    sql = "CREATE TABLE IF NOT EXISTS `EightMagicBall`.`Questions` (`id` INT AUTO_INCREMENT NOT NULL ,`created_at` DATETIME NOT NULL ,`user_question` TEXT NOT NULL ,`magicball_answer` TEXT NOT NULL, PRIMARY KEY (`id`)) ENGINE = InnoDB"
    
    client.execute_statement(
        resourceArn = db_cluster_arn, 
        secretArn = secret_arn, 
        sql = sql
    )


def go_init(appName):

    print("Create S3 for lambda files")
    create_lambda_s3(appName)

    print("Create S3 for web app")
    create_web_s3(appName)

    print("Create RDS Cluster stack")
    create_rds_cluster(appName)

    print("Init Database")
    init_database(appName)

    print("Zip the lambda function")
    zip_lambda()

    print("Upload lambda function to S3")
    upload_lambda()

    print("Create Lambda and API Gateway stack")
    create_stack(appName)

    print("Upload static web files to S3")
    upload_static_files()

    print('Done')
    print('Now, go to '+website_url)


