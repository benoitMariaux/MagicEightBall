import json
import boto3
from datetime import datetime
import logging
import random
import available_answers

logger = logging.getLogger(__name__)
logging.getLogger().setLevel(logging.INFO)

def handler(event, context):

    rdsData = boto3.client('rds-data')

    cluster_arn = '__DB_CLUSTER_ARN__'
    secret_arn = '__SECRET_ARN__'

    if event['httpMethod'] == 'GET':
        page = get_current_page(event)
        itemsPerPage = 3
        offset = (page - 1) * itemsPerPage

        sql = f'SELECT id, user_question, magicball_answer, DATE_FORMAT(created_at, "%H:%i:%s") as at_time, DATE_FORMAT(created_at, "%d/%m/%Y") as at_date FROM Questions ORDER BY created_at DESC LIMIT {offset}, {itemsPerPage}'

        resp = rdsData.execute_statement(
            resourceArn = cluster_arn, 
            secretArn = secret_arn,
            database = 'EightMagicBall',
            sql = sql
        )

        logger.info("get list:")
        logger.info(json.dumps(resp))

        return {
            'statusCode': 200,
            'headers': get_response_headers(),
            'body': json.dumps(resp['records'])
        }


    if event['httpMethod'] == 'POST':

        user_question = get_user_question(event)
        if not user_question or user_question == '' or user_question.isspace():
            return {
                'statusCode': 400,
                'headers': get_response_headers(),
                'body': 'Your question cannot be empty'
            }
        
        magicball_answer = random.choice(available_answers.items)

        sql = 'INSERT INTO EightMagicBall.Questions(created_at, user_question, magicball_answer) VALUES(:created_at, :user_question, :magicball_answer)'
        now = datetime.now()

        param1 = {'name':'created_at', 'value':{'stringValue': now.strftime('%Y-%m-%d %H:%M:%S')}}
        param2 = {'name':'user_question', 'value':{'stringValue': user_question}}
        param3 = {'name':'magicball_answer', 'value':{'stringValue': magicball_answer}}
        paramSet = [param1, param2, param3]

        r = rdsData.execute_statement(
            resourceArn = cluster_arn, 
            secretArn = secret_arn, 
            parameters = paramSet,
            sql = sql)
        
        logger.info(json.dumps(r))

        return {
            'statusCode': 200,
            'headers': get_response_headers(),
            'body': json.dumps({ 
                'user_question': user_question,
                'magicball_answer': magicball_answer
            })
        }

    return {
        'statusCode': 400,
        'body': '{} method is not implemented.'.format(event['httpMethod'])
    }

def get_current_page(event):
    try:
        page = int(event['queryStringParameters']['page'])
        logger.info('in get_current_page')
        logger.info(page)
        page = page > 0 and page or 1
    except:
        page = 1
        pass

    logger.info(page)
    return page

def get_user_question(event):
    q = ''
    try:
        b = event['body']
        q = json.loads(b)['question']
    except:
        pass
    
    return q

def get_response_headers():
    return {
        "Access-Control-Allow-Origin": "__WEBSITE_URL__",
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Allow-Methods": "OPTIONS,POST,GET"
    }