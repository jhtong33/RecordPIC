def lambda_handler(event, context):
    output = []

    for i in range(1, 10001):
        output.append({'number': i})

    # TODO implement
    return {
        'statusCode': 200,
        'body': output
    }
