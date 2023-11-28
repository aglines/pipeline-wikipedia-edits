# Wikipedia Recent Edits Statistics

## Overview

- A pipeline in Apache Beam / Python ingests event data from a stream: recent edits to articles on Wikipedia

- Events are published to Pub/Sub topic in a Google Cloud project

- Beam workflow reads msgs from the topic, performs some transformations, then writes to a BigQuery table

- SQL statements in BigQuery process data to address some analysis questions

- Looker Studio displays the results of this analysis

- Code is run locally to ingest data & publish to Pub/Sub (ingest.py and pipeline.py)

## Development notes: Google Cloud and locally

- First I set up infrastructure in Google Cloud Platform:
    - project, APIs, billing, app registrationm, scopes...
    - storage bucket, Pub/Sub topic & subscription...
    - auth credentials / roles for user account, service acct...
    - DataFlow job, region, BigQuery table...

- Then I wrote a script (ingest.py) to get a corpus of messages into Pub/Sub

- To develop the pipeline I started with Dataflow Workbench: 
    - A Jupyter notebook there provides a way to interact with the runner
    - This method helped test code iteratively
    - This required some manual setup, incl allocation of VM resources in DataProc
    - But the isolated environment had problems with BigQuery...

- So instead, I built and ran pipeline.py locally. In it:
    - A Beam workflow subscribes to the messages now published in the Pub/Sub topic
    - A Beam.ParDo function filters for the desired message type (server side filtering isn't supported)
    - A series of consecutive Beam.Maps perform transformations on the data to:
        - Handle missing values for certain columns
        - Extract the desired columns
        - Convert datetimes to same format & for readability
        - Add other various columns
    - Finally, it constructs the schema and writes each row to a BigQuery table

