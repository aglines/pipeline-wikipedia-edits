from config import topic, project_id, temp_location, region, job_name, output_table
import json
import logging
import apache_beam as beam
import datetime
from datetime import datetime

from apache_beam.options.pipeline_options import GoogleCloudOptions
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.options.pipeline_options import StandardOptions
from apache_beam.io import ReadFromPubSub, WriteToBigQuery
from apache_beam.io.gcp.bigquery import BigQueryDisposition

# Filters ---------------------------------------------------------------------

class OnlyEditType(beam.DoFn):
    def process(self, element):
        """Filter for only Edit type messages, which have the data we want"""
        parsed_msg = json.loads(element.data.decode('utf-8'))
        if (parsed_msg['type'] == 'edit') :
            yield parsed_msg

def check_for_absence(message, key):
    """Set default value to False if key is missing"""
    message[key] = message.get(key) or False
    return message

def get_columns(message):
    try:
        event_id = message['meta']['id']
        change_type = message['type']
        user = message['user']
        title = message['title']
        title_url = message['title_url']
        bot = message['bot'] 
        datetime_user = message['meta']['dt']
        datetime_server = message['timestamp']
        domain = message['meta']['domain']
        is_minor_change = message['minor']
        is_patrolled = message['patrolled']
        length_old = message['length']['old']
        length_new = message['length']['new']
            
        return { 
            'event_id' : event_id, 
            'change_type' : change_type, 
            'user': user,
            'title': title,
            'title_url': title_url,
            'bot' : bot,
            'datetime_user' : datetime_user,
            'datetime_server': datetime_server,
            'domain': domain,
            'is_minor_change' : is_minor_change,
            'is_patrolled' : is_patrolled,
            'length_old': length_old,
            'length_new': length_new
            }
    except: return

# Transformations -------------------------------------------------------------

def find_edit_length(message):
    message['edit_length'] = (message['length_new'] - message['length_old'])
    return message

def add_col_is_edit(message):
    submsg = message['domain']
    message['is_article_edit'] = True if submsg[-13:] == 'wikipedia.org' else False
    return message

def convert_server_dt(message):
    # Yep, it only works if I import datetime inside the function
    import datetime
    from datetime import datetime
    curr = message['datetime_server']
    message['datetime_server'] = datetime.utcfromtimestamp(curr).strftime('%Y-%m-%d %H:%M:%S')
    return message

def convert_user_dt(message):
    import datetime
    from datetime import datetime
    input_string = message['datetime_user']
    dt = datetime.strptime(input_string, '%Y-%m-%dT%H:%M:%SZ')
    message['datetime_user'] = dt.strftime('%Y-%m-%d %H:%M:%S')
    return message

# PIPELINE --------------------------------------------------------------------

def run():
    options = PipelineOptions(
        runner = 'DataflowRunner',
        project=project_id,
        job_name=job_name + '-' + datetime.now().strftime('%y%m%d-%H%M%S'),
        region=region,
        temp_location=temp_location
    )
    options.view_as(StandardOptions).streaming = True
    options.view_as(GoogleCloudOptions).staging_location = '%s/staging' % temp_location
    options.view_as(GoogleCloudOptions).temp_location = '%s/temp' % temp_location

    with beam.Pipeline(options=options) as p:

        input_data = p | 'read' >> ReadFromPubSub(topic=topic,with_attributes=True)

        # Server-side filtering not supported, so filter by type here
        data = input_data | 'transform' >> beam.ParDo(OnlyEditType())

        # Clean NULLs from certain columns likely to have them
        data = data | 'check for empty minor' >> beam.Map(check_for_absence, key='minor')
        data = data | 'check for empty patrolled' >> beam.Map(check_for_absence, key='patrolled')

        data = data | 'get columns' >> beam.Map(get_columns)

        # Ensure datetimes can be compared with each other, as well as human readable
        data = data | 'convert server dt' >> beam.Map(convert_server_dt)
        data = data | 'convert user dt' >> beam.Map(convert_user_dt)

        # Add columns for edit length and whether it's an article edit
        data = data | 'calc edit length' >> beam.Map(find_edit_length)
        data = data | 'add col is_edit' >> beam.Map(add_col_is_edit)

        output_data = data | 'Write to BigQuery' >> WriteToBigQuery(
            output_table,
            schema = """
            'event_id:STRING, change_type:STRING, user:STRING, title:STRING, title_url:STRING,
            bot:BOOL, datetime_server: DATETIME, datetime_user: DATETIME, domain:STRING,
            is_article_edit:BOOL, is_minor_change:BOOL, is_patrolled:BOOL, length_old:INT64, length_new:INT64, edit_length:INT64'
            """,
            create_disposition=BigQueryDisposition.CREATE_IF_NEEDED,
            write_disposition=BigQueryDisposition.WRITE_APPEND
        )        

# -----------------------------------------------------------------------------

if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    run()
